#!/usr/bin/env python3
"""WolfBench Weave — Upload Harbor eval results to W&B Weave.

Integrates with the WolfBench dashboard and chart workflow.

Unified upload: evaluations with real per-task metrics and nested agent
traces, all connected in the Weave evaluation hierarchy.

Usage:
    python wolfbench_weave.py upload -i wolfbench_results.json
    python wolfbench_weave.py status
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

# Suppress noisy dependency warnings (requests vs urllib3/chardet version mismatch)
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")

# Suppress Weave's noisy version/progress warnings
logging.getLogger("weave").setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PROJECT = "wolfbench"


def _manifest_filename(project: str = DEFAULT_PROJECT) -> str:
    """Return project-specific manifest filename."""
    return f"{project}-manifest.json"

# Default result for tasks not in a run's results map (errored/missing tasks).
_DEFAULT_RESULT = {
    "reward": 0.0,
    "success": False,
    "duration_sec": 0.0,
    "n_input_tokens": 0,
    "n_output_tokens": 0,
    "n_cache_tokens": 0,
    "cost_usd": 0.0,
    "has_error": True,
}

# Lazy-init scorer singleton (created once per process).
_scorer = None


# ---------------------------------------------------------------------------
# Manifest management
# ---------------------------------------------------------------------------


def load_manifest(manifest_path: Path | None = None, project: str = DEFAULT_PROJECT) -> dict:
    """Load dedup manifest from disk, or return an empty one."""
    if manifest_path is None:
        manifest_path = Path(__file__).parent / _manifest_filename(project)
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"project": DEFAULT_PROJECT, "last_updated": None, "evaluations": {}}


def save_manifest(manifest: dict, manifest_path: Path | None = None, project: str = DEFAULT_PROJECT) -> None:
    """Atomically save manifest (write .tmp then rename)."""
    if manifest_path is None:
        manifest_path = Path(__file__).parent / _manifest_filename(project)
    manifest["last_updated"] = datetime.now().isoformat()
    tmp = manifest_path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2)
    tmp.rename(manifest_path)


def manifest_key(agent: str, version: str, model_display: str,
                 timeout_sec: float | None, thinking: str = "-") -> str:
    """Build lookup key matching the chart grouping tuple."""
    return f"{agent}|{version or 'unknown'}|{model_display}|{timeout_sec}|{thinking}"


def parse_manifest_key(key: str) -> tuple[str, str, str, float | None, str]:
    """Parse a manifest key back into (agent, version, model_display, timeout, thinking)."""
    parts = key.split("|", 4)
    timeout = float(parts[3]) if len(parts) > 3 and parts[3] != "None" else None
    thinking = parts[4] if len(parts) > 4 else "-"
    return parts[0], parts[1], parts[2], timeout, thinking


def _resolve_display_name(r: dict) -> str:
    """Return display name: model_display override if set, else auto-derive from model path."""
    md = r.get("model_display") or ""
    if md:
        return md
    model_full = r.get("model", "unknown")
    parts = model_full.split("/")
    if len(parts) >= 3:
        return "/".join(parts[2:])
    elif len(parts) == 2:
        return parts[-1]
    return model_full


def _normalize_thinking(t) -> str:
    """Normalize thinking/reasoning_effort to a display string."""
    if t is None:
        return "-"
    if t is True or t == "enabled":
        return "on"
    if t is False or t == "disabled":
        return "off"
    return str(t)


def _resolve_thinking(r: dict) -> str:
    """Return thinking display: thinking_display override if set, else auto-normalize."""
    td = r.get("thinking_display") or ""
    if td:
        return td
    return _normalize_thinking(r.get("thinking"))


def is_run_uploaded(manifest: dict, key: str, timestamp: str) -> bool:
    """Check if a run was already uploaded."""
    eval_entry = manifest.get("evaluations", {}).get(key)
    if not eval_entry:
        return False
    run_entry = eval_entry.get("runs", {}).get(timestamp)
    if not run_entry:
        return False
    return run_entry.get("uploaded", False)


def _resolve_local_run_dir(run: dict, local_runs_dir: Path | None) -> str | None:
    """Resolve local run directory path for per-task result.json reading."""
    if run.get("vm") == "local":
        return run["run_dir"]
    if local_runs_dir:
        parts = run["run_dir"].rstrip("/").split("/")
        local_path = Path(local_runs_dir) / parts[-2] / parts[-1]
        if local_path.exists():
            return str(local_path)
    return None


# ---------------------------------------------------------------------------
# Run grouping (matches wolfbench-chart.py key)
# ---------------------------------------------------------------------------


def group_runs(runs: list[dict]) -> dict[str, list[dict]]:
    """Group runs by (agent, version, model_display, timeout, thinking) manifest key."""
    groups: dict[str, list[dict]] = {}
    for r in runs:
        ver = r.get("agent_version") or "unknown"
        thinking = _resolve_thinking(r)
        key = manifest_key(r["agent"], ver, _resolve_display_name(r), r.get("timeout_sec"), thinking)
        groups.setdefault(key, []).append(r)
    return groups


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_timeout(sec: float | None) -> str:
    if sec is None:
        return ""
    h = sec / 3600
    return f"{int(h)}h" if h == int(h) else f"{h:.1f}h"


def _eval_label(agent: str, model_display: str, timeout_sec: float | None,
                thinking: str = "-") -> str:
    label = f"{agent}_{model_display}"
    t = _fmt_timeout(timeout_sec)
    if t:
        label += f"@{t}"
    if thinking != "-":
        label += f"_{thinking}"
    return label


def _get_scorer():
    """Return (and lazily create) the shared Weave scorer op."""
    global _scorer
    if _scorer is None:
        import weave

        @weave.op()
        def wolfbench_scorer(task_name: str, output: dict) -> dict:
            return {
                "success": output.get("success", False),
                "reward": output.get("reward", 0.0),
                "duration_sec": output.get("duration_sec", 0.0),
                "n_input_tokens": output.get("n_input_tokens", 0),
                "n_output_tokens": output.get("n_output_tokens", 0),
                "n_cache_tokens": output.get("n_cache_tokens", 0),
                "total_tokens": (
                    output.get("n_input_tokens", 0)
                    + output.get("n_output_tokens", 0)
                ),
                "cost_usd": output.get("cost_usd", 0.0),
                "has_error": output.get("has_error", False),
            }

        _scorer = wolfbench_scorer
    return _scorer


def _create_run_model(
    run_label: str,
    results_map: dict[str, dict],
    trajectories: dict[str, dict] | None = None,
    client=None,
    run: dict | None = None,
):
    """Create a @weave.op predictor that returns pre-computed results.

    If trajectories and client are provided, also creates nested trace
    children inside predict() (unified upload: metrics + traces in one pass).
    """
    import weave

    @weave.op(name=run_label)
    def predict(task_name: str) -> dict:
        result = results_map.get(task_name, _DEFAULT_RESULT)

        # Create nested trace hierarchy if trajectory data is available
        if trajectories and client and run:
            traj = trajectories.get(task_name)
            if traj:
                _create_trace_children(
                    traj, task_name, run_label, run, client, result
                )

        return result

    return predict


def _resolve_entity(entity: str | None) -> str:
    """Resolve W&B entity from arg, env, or API."""
    if entity:
        return entity
    entity = os.environ.get("WANDB_ENTITY", "")
    if entity:
        return entity
    try:
        import wandb

        return wandb.Api().default_entity or "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Tier 1: Evaluations from summary data
# ---------------------------------------------------------------------------


def read_per_task_results(run_dir: str) -> dict[str, dict]:
    """Read per-task result.json files and extract real metrics.

    Returns {task_name: result_dict} with actual tokens, duration, cost.
    Mirrors _aggregate_local_tokens() in wolfbench_collect.py but per-task.
    """
    run_path = Path(run_dir)
    results = {}
    for result_file in run_path.glob("*/result.json"):
        if result_file.parent.name in (".", "__pycache__"):
            continue
        task_name = result_file.parent.name.split("__")[0]
        try:
            d = json.loads(result_file.read_text())
            ar = d.get("agent_result") or {}
            vr = d.get("verifier_result") or {}
            reward = vr.get("rewards", {}).get("reward", 0.0)

            # Duration from agent_execution timing
            ae = d.get("agent_execution") or {}
            duration = 0.0
            if ae.get("started_at") and ae.get("finished_at"):
                start = datetime.fromisoformat(ae["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(ae["finished_at"].replace("Z", "+00:00"))
                duration = (end - start).total_seconds()

            results[task_name] = {
                "reward": reward,
                "success": reward > 0,
                "duration_sec": round(duration, 1),
                "n_input_tokens": ar.get("n_input_tokens", 0) or 0,
                "n_output_tokens": ar.get("n_output_tokens", 0) or 0,
                "n_cache_tokens": ar.get("n_cache_tokens", 0) or 0,
                "cost_usd": ar.get("cost_usd", 0) or 0,
                "has_error": d.get("exception_info") is not None,
            }
        except (json.JSONDecodeError, OSError):
            pass
    return results


def build_task_results(run: dict, run_dir: str | None = None) -> dict[str, dict]:
    """Convert a run's data into per-task results.

    If run_dir is provided and contains per-task result.json files,
    uses real metrics. Otherwise falls back to passed/failed lists with zeros.
    """
    # Try real per-task metrics first
    if run_dir:
        real = read_per_task_results(run_dir)
        if real:
            return real

    # Fallback: passed/failed lists with zero metrics
    results = {}
    for task in run.get("passed_tasks", []):
        results[task] = {
            "reward": 1.0,
            "success": True,
            "duration_sec": 0.0,
            "n_input_tokens": 0,
            "n_output_tokens": 0,
            "n_cache_tokens": 0,
            "cost_usd": 0.0,
            "has_error": False,
        }
    for task in run.get("failed_tasks", []):
        results[task] = {
            "reward": 0.0,
            "success": False,
            "duration_sec": 0.0,
            "n_input_tokens": 0,
            "n_output_tokens": 0,
            "n_cache_tokens": 0,
            "cost_usd": 0.0,
            "has_error": False,
        }
    # Tasks in neither list (errored) fall through to _DEFAULT_RESULT
    return results


async def upload_evaluations(
    runs: list[dict],
    project: str = DEFAULT_PROJECT,
    entity: str | None = None,
    manifest_path: Path | None = None,
    local_runs_dir: Path | None = None,
    progress_callback=None,
) -> dict[str, str]:
    """Upload evaluations with real metrics and (optionally) nested traces.

    Unified upload: reads per-task result.json for real metrics, and if
    trajectory data is available, creates nested trace children inside
    the Weave evaluation hierarchy.

    Returns {manifest_key: weave_evaluation_url}.
    """
    import weave

    if manifest_path is None:
        manifest_path = Path(__file__).parent / _manifest_filename(project)

    manifest = load_manifest(manifest_path, project=project)
    manifest["project"] = project
    entity = _resolve_entity(entity)
    manifest["entity"] = entity

    _init_path = f"{entity}/{project}" if entity and entity != "unknown" else project
    client = weave.init(_init_path)
    scorer = _get_scorer()

    groups = group_runs(runs)
    manifest_keys = set(manifest.get("evaluations", {}).keys())
    group_keys = set(groups.keys())
    print(f"Upload: {len(groups)} groups from runs, {len(manifest_keys)} entries in manifest")
    _only_in_groups = group_keys - manifest_keys
    _only_in_manifest = manifest_keys - group_keys
    if _only_in_groups:
        print(f"  Keys in runs but NOT in manifest: {_only_in_groups}")
    if _only_in_manifest:
        print(f"  Keys in manifest but NOT in runs: {_only_in_manifest}")

    results: dict[str, str] = {}
    n_uploaded = 0
    n_skipped = 0

    for key, group in sorted(groups.items()):
        agent, version, model_display, timeout_sec, thinking = parse_manifest_key(key)
        label = _eval_label(agent, model_display, timeout_sec, thinking)

        # Check if ALL runs in this group are already uploaded
        new_runs = [
            r
            for r in group
            if not is_run_uploaded(manifest, key, r["timestamp"])
        ]

        eval_entry = manifest.get("evaluations", {}).get(key, {})
        has_eval_calls = bool(eval_entry.get("eval_call_ids"))

        if new_runs or not has_eval_calls:
            _reasons = []
            if new_runs:
                _reasons.append(f"{len(new_runs)} new runs: {[r['timestamp'] for r in new_runs]}")
            if not has_eval_calls:
                _reasons.append("no eval_call_ids")
            if not eval_entry:
                _reasons.append("key not in manifest")
            print(f"  NOT skipping {label} [{key}]: {'; '.join(_reasons)}")

        if not new_runs and has_eval_calls:
            url = eval_entry.get("weave_url", "")
            results[key] = url
            n_skipped += len(group)
            msg = f"Skipped {label} ({len(group)} runs already uploaded)"
            print(f"  {msg}")
            if progress_callback:
                progress_callback(msg)
            continue

        _legacy_reupload = False
        if not new_runs and not has_eval_calls:
            # Legacy upload: runs marked uploaded but no eval calls exist.
            # Re-process entire group to create proper Evaluation.evaluate calls.
            # Skip traces — only need eval calls for Leaderboard URLs.
            _legacy_reupload = True
            new_runs = group
            print(f"  Re-uploading {label} (legacy: no eval calls, {len(group)} runs, traces skipped)")

        print(f"  Uploading: {label} ({len(group)} runs)")

        # Build per-run predictor models
        models = []
        all_tasks: set[str] = set()
        run_trace_counts: dict[str, int] = {}  # timestamp -> n_traces

        for i, r in enumerate(group, 1):
            run_label = r["timestamp"].replace("/", "-").replace(" ", "_")

            # Resolve local run dir for per-task result.json reading
            local_dir = _resolve_local_run_dir(r, local_runs_dir)

            # Real metrics from per-task result.json (falls back to zeros)
            task_results = build_task_results(r, run_dir=local_dir)
            all_tasks.update(task_results.keys())

            # Load trajectories for nested trace creation (skip for legacy re-uploads)
            if _legacy_reupload:
                trajectories = {}
            else:
                trajectories = _load_trajectories_for_run(r, local_runs_dir)
            run_trace_counts[r["timestamp"]] = len(trajectories)
            if i == 1:  # debug: show trajectory loading for first run of each group
                print(f"    [debug] vm={r.get('vm')!r} run_dir=...{r.get('run_dir','')[-50:]} "
                      f"local_runs_dir={local_runs_dir!r} trajs={len(trajectories)} legacy={_legacy_reupload}")

            model = _create_run_model(
                run_label, task_results,
                trajectories=trajectories or None,
                client=client if trajectories else None,
                run=r if trajectories else None,
            )
            models.append((run_label, model))

            n_pass = sum(1 for v in task_results.values() if v["success"])
            has_real = local_dir is not None
            has_traces = bool(trajectories)
            print(
                f"    {run_label}: {n_pass}/{len(task_results)}"
                f" (metrics: {'real' if has_real else 'stub'}"
                f", traces: {len(trajectories) if has_traces else 'none'})"
            )

        # Shared dataset (union of all task names in this group)
        dataset = weave.Dataset(
            name=f"terminal-bench-2.0__{label.replace('/', '-')}",
            rows=[{"task_name": t} for t in sorted(all_tasks)],
        )

        # Evaluation
        evaluation = weave.Evaluation(
            name=f"Terminal-Bench 2.0: {label}",
            dataset=dataset,
            scorers=[scorer],
        )

        # Evaluate each run (predict() creates nested traces if available)
        for run_label, model in models:
            print(f"    Evaluating {run_label}...")
            await evaluation.evaluate(
                model,
                __weave={"display_name": f"{label} / {run_label}"},
            )

        _ref = weave.publish(evaluation)
        n_uploaded += len(group)

        # Flush async queue BEFORE querying eval calls — otherwise the calls
        # may still be in the async queue and get_calls() won't find them,
        # resulting in empty eval_call_ids and duplicate uploads on next click.
        client.flush()

        # Object URL → Leaderboard view (the proper UI for comparing eval runs)
        url = (
            f"https://wandb.ai/{client.entity}/{client.project}"
            f"/weave/objects/{_ref.name}/versions/{_ref.digest}"
        )
        results[key] = url

        # Capture evaluation call IDs for skip-logic (detect completed uploads)
        from weave.trace.weave_client import CallsFilter as _CF
        _eval_op = f"weave:///{client.entity}/{client.project}/op/Evaluation.evaluate:*"
        _prefix = f"{label} / "
        _total_runs = sum(len(g) for g in groups.values())
        _eval_calls = list(client.get_calls(
            filter=_CF(op_names=[_eval_op]),
            sort_by=[{"field": "started_at", "direction": "desc"}],
            limit=max(_total_runs * 2, 200),
            columns=["id", "display_name"],
        ))
        _call_ids = [
            c.id for c in _eval_calls
            if (c.display_name or "").startswith(_prefix)
        ][:len(models)]

        # Update manifest (new unified format)
        manifest.setdefault("evaluations", {})[key] = {
            "eval_name": f"Terminal-Bench 2.0: {label}",
            "weave_url": url,
            "eval_call_ids": _call_ids,
            "runs": {
                r["timestamp"]: {
                    "vm": r["vm"],
                    "score": r["score"],
                    "uploaded": True,
                    "has_traces": run_trace_counts.get(r["timestamp"], 0) > 0,
                    "n_traces": run_trace_counts.get(r["timestamp"], 0),
                }
                for r in group
            },
        }
        save_manifest(manifest, manifest_path)

        total_traces = sum(run_trace_counts.get(r["timestamp"], 0) for r in group)
        msg = f"Uploaded {label} ({len(group)} runs, {len(all_tasks)} tasks, {total_traces} traces)"
        print(f"  {msg}")
        if progress_callback:
            progress_callback(msg)

    _summary = f"Done: {n_uploaded} runs uploaded, {n_skipped} skipped"
    print(f"\n{_summary}")
    return {"urls": results, "n_uploaded": n_uploaded, "n_skipped": n_skipped, "summary": _summary}


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------


def _extract_message(message) -> str:
    """Extract text from a message field (string or ContentParts list)."""
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        parts = []
        for part in message:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(part.get("text", ""))
                elif part.get("type") == "image":
                    parts.append("[image]")
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    return str(message) if message else ""


def _extract_observation(observation) -> str:
    """Extract text from an observation field."""
    if not observation:
        return ""
    parts = []
    for result in observation.get("results", []):
        content = result.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.append(_extract_message(content))
    return "\n".join(parts)


def load_local_trajectories(local_run_dir: str) -> dict[str, dict]:
    """Load trajectory.json files from local storage.

    Returns {task_name: trajectory_dict}.
    """
    run_path = Path(local_run_dir)
    trajectories = {}
    for traj_file in run_path.glob("**/agent/trajectory.json"):
        # Path: evals/<eval>/<task_name__hash>/agent/trajectory.json
        task_dir = traj_file.parent.parent.name  # task_name__hash
        task_name = task_dir.split("__")[0]
        try:
            trajectories[task_name] = json.loads(traj_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Error reading {traj_file}: {e}", file=sys.stderr)
    return trajectories


def fetch_all_trajectories(vm: str, run_dir: str) -> dict[str, dict]:
    """SSH to VM, tar all trajectory.json files, stream back.

    Uses a single SSH call per run (not 89 individual fetches).
    Returns {task_name: trajectory_dict}.
    """
    import base64
    import importlib
    import io
    import tarfile

    hcr = importlib.import_module("wolfbench_collect")

    command = (
        f'cd "{run_dir}" && '
        'find . -path "*/agent/trajectory.json" -print0 2>/dev/null | '
        "tar -czf - --null -T - 2>/dev/null | base64"
    )
    stdout, _stderr, rc = hcr.ssh_run(vm, command, timeout=120)
    if rc != 0 or not stdout.strip():
        return {}

    try:
        tar_bytes = base64.b64decode(stdout.strip())
        trajectories = {}
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
            for member in tar.getmembers():
                if not member.name.endswith("trajectory.json"):
                    continue
                # Path: ./task_name__hash/agent/trajectory.json
                parts = member.name.split("/")
                task_dir = parts[1] if len(parts) >= 3 else parts[0]
                task_name = task_dir.split("__")[0]
                f = tar.extractfile(member)
                if f:
                    trajectories[task_name] = json.loads(f.read())
        return trajectories
    except Exception as e:
        print(f"  Error parsing trajectories from {vm}: {e}", file=sys.stderr)
        return {}


def _load_trajectories_for_run(
    run: dict, local_runs_dir: Path | None = None
) -> dict[str, dict]:
    """Load trajectory data for a run from local storage or SSH.

    Checks local first, then falls back to SSH. Returns {task_name: trajectory}.
    """
    trajectories = {}

    if run.get("vm") == "local":
        trajectories = load_local_trajectories(run["run_dir"])
    elif local_runs_dir:
        parts = run["run_dir"].rstrip("/").split("/")
        local_path = Path(local_runs_dir) / parts[-2] / parts[-1]
        if local_path.exists():
            trajectories = load_local_trajectories(str(local_path))

    if not trajectories and run.get("vm") and run["vm"] != "local":
        trajectories = fetch_all_trajectories(run["vm"], run["run_dir"])

    return trajectories


def _create_trace_children(
    traj: dict,
    task_name: str,
    run_label: str,
    run: dict,
    client,
    result: dict,
) -> None:
    """Create nested Weave trace calls for one task's trajectory.

    Must be called from inside a @weave.op context (e.g., predict()).
    Creates agent_run with use_stack=True so it auto-parents to the
    calling op via Weave's ContextVar call stack.
    """
    steps = traj.get("steps", [])
    if not steps:
        return

    final_metrics = traj.get("final_metrics") or {}
    session_id = traj.get("session_id")
    traj_agent = traj.get("agent") or {}

    # Task prompt from first user step
    task_prompt = ""
    for s in steps:
        if s.get("source") == "user":
            task_prompt = _extract_message(s.get("message"))
            break

    # Parent: agent_run (auto-parents to predict via stack)
    parent = client.create_call(
        op="agent_run",
        inputs={
            "task_name": task_name,
            "model": _resolve_display_name(run),
            "agent": run.get("agent", "unknown"),
            "agent_version": (
                traj_agent.get("version") or run.get("agent_version")
            ),
            "run": run_label,
            "total_steps": len(steps),
            "session_id": session_id,
            "task_prompt": task_prompt,
        },
        display_name=f"{task_name} [{run_label}]",
        use_stack=True,
    )

    # Children: one per step (explicit parent, no stack push)
    for step in steps:
        source = step.get("source", "unknown")
        step_id = step.get("step_id", 0)
        timestamp = step.get("timestamp")
        metrics = step.get("metrics") or {}
        msg = _extract_message(step.get("message"))

        if source == "user":
            child = client.create_call(
                op="user_message",
                inputs={"step_id": step_id, "timestamp": timestamp},
                parent=parent,
                display_name=f"step {step_id}: user",
                use_stack=False,
            )
            client.finish_call(child, output={"message": msg})

        elif source == "agent" and metrics:
            child = client.create_call(
                op="llm_call",
                inputs={
                    "step_id": step_id,
                    "timestamp": timestamp,
                    "model": (
                        step.get("model_name") or _resolve_display_name(run)
                    ),
                    "prompt_tokens": metrics.get("prompt_tokens", 0),
                },
                parent=parent,
                display_name=f"step {step_id}: llm",
                use_stack=False,
            )
            client.finish_call(
                child,
                output={
                    "message": msg,
                    "reasoning": step.get("reasoning_content") or "",
                    "tool_calls": step.get("tool_calls") or [],
                    "completion_tokens": metrics.get("completion_tokens", 0),
                    "cached_tokens": metrics.get("cached_tokens", 0),
                    "cost_usd": metrics.get("cost_usd"),
                    "stop_reason": (step.get("extra") or {}).get(
                        "stop_reason"
                    ),
                },
            )

        elif source == "agent" and step.get("observation"):
            obs = _extract_observation(step.get("observation"))
            child = client.create_call(
                op="tool_result",
                inputs={"step_id": step_id, "timestamp": timestamp},
                parent=parent,
                display_name=f"step {step_id}: tool",
                use_stack=False,
            )
            client.finish_call(child, output={"output": obs})

        elif source == "system":
            child = client.create_call(
                op="system_message",
                inputs={"step_id": step_id, "timestamp": timestamp},
                parent=parent,
                display_name=f"step {step_id}: system",
                use_stack=False,
            )
            client.finish_call(child, output={"message": msg})

        else:
            child = client.create_call(
                op="agent_message",
                inputs={"step_id": step_id, "timestamp": timestamp},
                parent=parent,
                display_name=f"step {step_id}: agent",
                use_stack=False,
            )
            client.finish_call(child, output={"message": msg})

    # Finish agent_run (pops from stack)
    client.finish_call(
        parent,
        output={
            "reward": result.get("reward", 0.0),
            "success": result.get("success", False),
            "has_error": result.get("has_error", False),
            "total_steps": final_metrics.get("total_steps", len(steps)),
            "total_prompt_tokens": final_metrics.get(
                "total_prompt_tokens", 0
            ),
            "total_completion_tokens": final_metrics.get(
                "total_completion_tokens", 0
            ),
            "total_cached_tokens": final_metrics.get(
                "total_cached_tokens", 0
            ),
            "total_cost_usd": final_metrics.get("total_cost_usd"),
        },
    )


# ---------------------------------------------------------------------------
# URL helpers (for chart integration)
# ---------------------------------------------------------------------------


def get_evaluation_urls(
    manifest: dict | Path | None = None,
) -> dict[tuple, str]:
    """Return {(agent, version, model_display, timeout): url} for chart.

    Accepts a manifest dict, a Path to the manifest file, or None (default path).
    """
    if manifest is None:
        manifest = load_manifest()
    elif isinstance(manifest, Path):
        manifest = load_manifest(manifest)

    urls = {}
    for key, eval_data in manifest.get("evaluations", {}).items():
        agent, version, model_display, timeout, thinking = parse_manifest_key(key)
        url = eval_data.get("weave_url", "")
        if url:
            urls[(agent, version, model_display, timeout, thinking)] = url
    return urls


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="WolfBench Weave — upload eval results to W&B Weave"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # upload
    pu = sub.add_parser("upload", help="Upload evaluations + traces")
    pu.add_argument(
        "-i", "--input", type=Path, required=True,
        help="Path to wolfbench_results.json",
    )
    pu.add_argument("--project", default=DEFAULT_PROJECT)
    pu.add_argument("--entity", default=None)

    # status
    sub.add_parser("status", help="Show manifest status")

    args = parser.parse_args()

    if args.command == "status":
        manifest = load_manifest()
        evals = manifest.get("evaluations", {})
        if not evals:
            print("No uploads yet.")
            return 0
        print(f"Project: {manifest.get('project', '?')}")
        print(f"Entity:  {manifest.get('entity', '?')}")
        print(f"Updated: {manifest.get('last_updated', '?')}")
        print()
        for key, ev in evals.items():
            runs = ev.get("runs", {})
            n_uploaded = sum(1 for r in runs.values() if r.get("uploaded"))
            n_traces = sum(1 for r in runs.values() if r.get("has_traces"))
            print(f"  {ev.get('eval_name', key)}")
            print(
                f"    Runs: {len(runs)}, "
                f"Uploaded: {n_uploaded}/{len(runs)}, "
                f"With traces: {n_traces}/{len(runs)}"
            )
            print(f"    URL:  {ev.get('weave_url', '-')}")
        return 0

    # Load runs
    with open(args.input) as f:
        data = json.load(f)
    runs = data.get("runs", [])
    print(f"Loaded {len(runs)} runs from {args.input}")

    manifest_path = args.input.parent / _manifest_filename(args.project)

    asyncio.run(
        upload_evaluations(
            runs,
            project=args.project,
            entity=args.entity,
            manifest_path=manifest_path,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
