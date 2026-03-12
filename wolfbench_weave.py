#!/usr/bin/env python3
"""WolfBench Weave — Upload Harbor eval results to W&B Weave.

Integrates with the WolfBench dashboard and chart workflow.

Two-tier upload:
  Tier 1: Evaluations from collected summary data (fast, no SSH)
  Tier 2: Full agent traces from VMs (slow, requires SSH)

Usage:
    python wolfbench_weave.py tier1 -i harbor_results.json
    python wolfbench_weave.py tier2 -i harbor_results.json
    python wolfbench_weave.py both  -i harbor_results.json
    python wolfbench_weave.py status
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

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
                 timeout_sec: float | None) -> str:
    """Build lookup key matching the chart grouping tuple."""
    return f"{agent}|{version or 'unknown'}|{model_display}|{timeout_sec}"


def parse_manifest_key(key: str) -> tuple[str, str, str, float | None]:
    """Parse a manifest key back into (agent, version, model_display, timeout)."""
    parts = key.split("|", 3)
    timeout = float(parts[3]) if len(parts) > 3 and parts[3] != "None" else None
    return parts[0], parts[1], parts[2], timeout


def is_run_uploaded(manifest: dict, key: str, timestamp: str, tier: int) -> bool:
    """Check if a run was already uploaded for the given tier."""
    eval_entry = manifest.get("evaluations", {}).get(key)
    if not eval_entry:
        return False
    run_entry = eval_entry.get("runs", {}).get(timestamp)
    if not run_entry:
        return False
    return run_entry.get(f"tier{tier}_uploaded", False)


# ---------------------------------------------------------------------------
# Run grouping (matches wolfbench-chart.py key)
# ---------------------------------------------------------------------------


def group_runs(runs: list[dict]) -> dict[str, list[dict]]:
    """Group runs by (agent, version, model_display, timeout) manifest key."""
    groups: dict[str, list[dict]] = {}
    for r in runs:
        ver = r.get("agent_version") or "unknown"
        key = manifest_key(r["agent"], ver, r["model_display"], r.get("timeout_sec"))
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


def _eval_label(agent: str, model_display: str, timeout_sec: float | None) -> str:
    label = f"{agent}_{model_display}"
    t = _fmt_timeout(timeout_sec)
    if t:
        label += f"@{t}"
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
                "total_tokens": (
                    output.get("n_input_tokens", 0)
                    + output.get("n_output_tokens", 0)
                ),
                "has_error": output.get("has_error", False),
            }

        _scorer = wolfbench_scorer
    return _scorer


def _create_run_model(run_label: str, results_map: dict[str, dict]):
    """Create a @weave.op predictor that returns pre-computed results."""
    import weave

    @weave.op(name=run_label)
    def predict(task_name: str) -> dict:
        return results_map.get(task_name, _DEFAULT_RESULT)

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


def build_task_results(run: dict) -> dict[str, dict]:
    """Convert a collected run's passed/failed task lists into per-task results."""
    results = {}
    for task in run.get("passed_tasks", []):
        results[task] = {
            "reward": 1.0,
            "success": True,
            "duration_sec": 0.0,
            "n_input_tokens": 0,
            "n_output_tokens": 0,
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
    progress_callback=None,
) -> dict[str, str]:
    """Upload Tier 1 evaluations from collected summary data.

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
    _client = weave.init(_init_path)  # noqa: F841 — sets global context
    scorer = _get_scorer()

    groups = group_runs(runs)
    results: dict[str, str] = {}
    n_uploaded = 0
    n_skipped = 0

    for key, group in sorted(groups.items()):
        agent, version, model_display, timeout_sec = parse_manifest_key(key)
        label = _eval_label(agent, model_display, timeout_sec)

        # Check if ALL runs in this group are already uploaded
        new_runs = [
            r
            for r in group
            if not is_run_uploaded(manifest, key, r["timestamp"], tier=1)
        ]

        if not new_runs and key in manifest.get("evaluations", {}):
            url = manifest["evaluations"][key].get("weave_url", "")
            results[key] = url
            n_skipped += len(group)
            msg = f"Skipped {label} ({len(group)} runs already uploaded)"
            print(f"  {msg}")
            if progress_callback:
                progress_callback(msg)
            continue

        print(f"  Uploading: {label} ({len(group)} runs)")

        # Build per-run predictor models
        models = []
        all_tasks: set[str] = set()

        for i, r in enumerate(group, 1):
            task_results = build_task_results(r)
            all_tasks.update(task_results.keys())

            run_label = r["timestamp"].replace("/", "-").replace(" ", "_")

            model = _create_run_model(run_label, task_results)
            models.append((run_label, model))

            n_pass = sum(1 for v in task_results.values() if v["success"])
            print(f"    {run_label}: {n_pass}/{len(task_results)}")

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

        # Evaluate each run
        for run_label, model in models:
            print(f"    Evaluating {run_label}...")
            await evaluation.evaluate(
                model,
                __weave={"display_name": f"{label} / {run_label}"},
            )

        eval_ref = weave.publish(evaluation)
        n_uploaded += len(group)

        # Direct URL to this specific evaluation object
        from urllib.parse import quote
        url = (
            f"https://wandb.ai/{eval_ref.entity}/{eval_ref.project}"
            f"/weave/objects/{quote(eval_ref.name)}/versions/{eval_ref.digest}"
        )
        results[key] = url

        # Update manifest
        manifest.setdefault("evaluations", {})[key] = {
            "eval_name": f"Terminal-Bench 2.0: {label}",
            "weave_url": url,
            "runs": {
                r["timestamp"]: {
                    "vm": r["vm"],
                    "score": r["score"],
                    "tier1_uploaded": True,
                    "tier2_uploaded": False,
                }
                for r in group
            },
        }
        save_manifest(manifest, manifest_path)

        msg = f"Uploaded {label} ({len(group)} runs, {len(all_tasks)} tasks)"
        print(f"  {msg}")
        if progress_callback:
            progress_callback(msg)

    _summary = f"Tier 1 done: {n_uploaded} runs uploaded, {n_skipped} skipped"
    print(f"\n{_summary}")
    return {"urls": results, "n_uploaded": n_uploaded, "n_skipped": n_skipped, "summary": _summary}


# ---------------------------------------------------------------------------
# Tier 2: Trace upload (SSH)
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

    Local equivalent of fetch_all_trajectories() — reads from disk.
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


def upload_traces_for_run(
    run: dict, trajectories: dict[str, dict], client, run_label: str
) -> int:
    """Upload nested Weave trace hierarchy for one run. Returns count uploaded."""
    count = 0
    passed_set = set(run.get("passed_tasks") or [])
    failed_set = set(run.get("failed_tasks") or [])

    for task_name, traj in sorted(trajectories.items()):
        steps = traj.get("steps", [])
        if not steps:
            continue

        final_metrics = traj.get("final_metrics") or {}
        session_id = traj.get("session_id")
        traj_agent = traj.get("agent") or {}

        # Task prompt from first user step
        task_prompt = ""
        for s in steps:
            if s.get("source") == "user":
                task_prompt = _extract_message(s.get("message"))
                break

        passed = task_name in passed_set
        has_error = task_name not in passed_set and task_name not in failed_set

        # Parent: agent_run
        parent = client.create_call(
            op="agent_run",
            inputs={
                "task_name": task_name,
                "model": run.get("model_display", "unknown"),
                "agent": run.get("agent", "unknown"),
                "agent_version": (
                    traj_agent.get("version") or run.get("agent_version")
                ),
                "run": run_label,
                "total_steps": len(steps),
                "session_id": session_id,
                "task_prompt": task_prompt,
            },
            parent=None,
            display_name=f"{task_name} [{run_label}]",
            use_stack=False,
        )

        # Children: one per step
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
                            step.get("model_name") or run.get("model_display")
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

        # Finish parent with final results
        client.finish_call(
            parent,
            output={
                "reward": 1.0 if passed else 0.0,
                "success": passed,
                "has_error": has_error,
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
        count += 1

    return count


async def upload_all_traces(
    runs: list[dict],
    project: str = DEFAULT_PROJECT,
    entity: str | None = None,
    manifest_path: Path | None = None,
    local_runs_dir: Path | None = None,
    progress_callback=None,
) -> dict[str, int]:
    """Upload Tier 2 traces for all runs. Returns {key: n_traces_uploaded}.

    If local_runs_dir is provided, checks for locally-stored trajectories
    before falling back to SSH fetching from the VM.
    """
    import weave

    if manifest_path is None:
        manifest_path = Path(__file__).parent / _manifest_filename(project)

    manifest = load_manifest(manifest_path, project=project)
    entity = _resolve_entity(entity)
    _init_path = f"{entity}/{project}" if entity and entity != "unknown" else project
    client = weave.init(_init_path)

    groups = group_runs(runs)
    results: dict[str, int] = {}

    for key, group in sorted(groups.items()):
        agent, _version, model_display, timeout_sec = parse_manifest_key(key)
        label = _eval_label(agent, model_display, timeout_sec)
        group_total = 0

        for i, r in enumerate(group, 1):
            if is_run_uploaded(manifest, key, r["timestamp"], tier=2):
                msg = f"Skipped traces: {label} {r['timestamp']} (already uploaded)"
                print(f"  {msg}")
                if progress_callback:
                    progress_callback(msg)
                continue

            run_label = r["timestamp"].replace("/", "-").replace(" ", "_")

            # Try local storage first, then fall back to SSH
            trajectories = {}
            _source = "local"

            if r.get("vm") == "local":
                # Run was scanned from local — run_dir IS the local path
                trajectories = load_local_trajectories(r["run_dir"])
            elif local_runs_dir:
                # Run was scanned from VM, but check if a local copy exists
                _parts = r["run_dir"].rstrip("/").split("/")
                _local_path = Path(local_runs_dir) / _parts[-2] / _parts[-1]
                if _local_path.exists():
                    trajectories = load_local_trajectories(str(_local_path))

            if not trajectories:
                # Fall back to SSH
                _source = r["vm"]
                msg = f"Fetching: {label} {run_label} from {r['vm']}..."
                print(f"  {msg}")
                if progress_callback:
                    progress_callback(msg)
                trajectories = fetch_all_trajectories(r["vm"], r["run_dir"])

            if not trajectories:
                msg = f"No trajectories for {run_label} ({_source})"
                print(f"  {msg}", file=sys.stderr)
                if progress_callback:
                    progress_callback(msg)
                continue
            else:
                msg = f"Loaded {len(trajectories)} trajectories from {_source}: {run_label}"
                print(f"  {msg}")
                if progress_callback:
                    progress_callback(msg)

            # Upload
            msg = f"Uploading {len(trajectories)} traces: {label} {run_label}"
            print(f"  {msg}")
            if progress_callback:
                progress_callback(msg)

            n = upload_traces_for_run(r, trajectories, client, run_label)
            group_total += n

            # Update manifest
            eval_entry = manifest.get("evaluations", {}).get(key)
            if eval_entry:
                run_entry = eval_entry.get("runs", {}).get(r["timestamp"])
                if run_entry:
                    run_entry["tier2_uploaded"] = True
                    run_entry["tier2_traces"] = n

            save_manifest(manifest, manifest_path)

            msg = f"Uploaded {n} traces for {run_label}"
            print(f"  {msg}")
            if progress_callback:
                progress_callback(msg)

        results[key] = group_total

    total = sum(results.values())
    _summary = f"Tier 2 done: {total} traces uploaded across {len(results)} evaluation(s)"
    print(f"\n{_summary}")
    return {"traces": results, "total": total, "summary": _summary}


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
        agent, version, model_display, timeout = parse_manifest_key(key)
        url = eval_data.get("weave_url", "")
        if url:
            urls[(agent, version, model_display, timeout)] = url
    return urls


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="WolfBench Weave — upload eval results to W&B Weave"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # tier1
    p1 = sub.add_parser("tier1", help="Upload evaluations (fast, no SSH)")
    p1.add_argument(
        "-i", "--input", type=Path, required=True,
        help="Path to harbor_results.json",
    )
    p1.add_argument("--project", default=DEFAULT_PROJECT)
    p1.add_argument("--entity", default=None)

    # tier2
    p2 = sub.add_parser("tier2", help="Upload traces (slow, requires SSH)")
    p2.add_argument("-i", "--input", type=Path, required=True)
    p2.add_argument("--project", default=DEFAULT_PROJECT)
    p2.add_argument("--entity", default=None)

    # both
    pb = sub.add_parser("both", help="Upload evaluations + traces")
    pb.add_argument("-i", "--input", type=Path, required=True)
    pb.add_argument("--project", default=DEFAULT_PROJECT)
    pb.add_argument("--entity", default=None)

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
            t1 = sum(1 for r in runs.values() if r.get("tier1_uploaded"))
            t2 = sum(1 for r in runs.values() if r.get("tier2_uploaded"))
            print(f"  {ev.get('eval_name', key)}")
            print(
                f"    Runs: {len(runs)}, "
                f"Tier1: {t1}/{len(runs)}, "
                f"Tier2: {t2}/{len(runs)}"
            )
            print(f"    URL:  {ev.get('weave_url', '-')}")
        return 0

    # Load runs
    with open(args.input) as f:
        data = json.load(f)
    runs = data.get("runs", [])
    print(f"Loaded {len(runs)} runs from {args.input}")

    manifest_path = args.input.parent / _manifest_filename(args.project)

    if args.command in ("tier1", "both"):
        print("\n=== Tier 1: Uploading evaluations ===")
        asyncio.run(
            upload_evaluations(
                runs,
                project=args.project,
                entity=args.entity,
                manifest_path=manifest_path,
            )
        )

    if args.command in ("tier2", "both"):
        print("\n=== Tier 2: Uploading traces ===")
        asyncio.run(
            upload_all_traces(
                runs,
                project=args.project,
                entity=args.entity,
                manifest_path=manifest_path,
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
