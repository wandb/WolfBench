#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "pyyaml>=6.0",
#   "weave>=0.51",
#   "wandb>=0.17",
# ]
# ///
"""WolfBench Ollama — Run WolfBench benchmarks against an Ollama LLM.

Full pipeline: configure → run → collect → upload to W&B Weave → generate chart.

Usage:
    uv run wolfbench-ollama.py qwen3.5:122b
    uv run wolfbench-ollama.py qwen3.5:122b --no-smoke --runs 5
    uv run wolfbench-ollama.py qwen3.5:122b --skip-upload --skip-chart
"""

import asyncio
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml

app = typer.Typer(help="Run WolfBench benchmarks against a local Ollama LLM.", add_completion=False)

WOLFBENCH_DIR = Path(__file__).parent
DEFAULT_JOBS_BASE = WOLFBENCH_DIR / "wolfbench-runs"
DEFAULT_API_BASE = "http://localhost:11434/v1"
SMOKE_DATASET = "terminal-bench-sample@2.0"
SANDBOX_CHOICES = ("docker", "daytona")

# Tracks the active harbor subprocess so signal handlers can terminate it cleanly.
_harbor_proc: subprocess.Popen | None = None
_sandbox_type: str = "docker"
_model_jobs_dir: Path | None = None


def _daytona_cmd() -> list[str] | None:
    """Return the daytona binary path, or None if not found."""
    daytona = shutil.which("daytona")
    if not daytona:
        # Common install location when not on PATH (e.g. linuxbrew)
        candidate = "/home/linuxbrew/.linuxbrew/bin/daytona"
        if Path(candidate).exists():
            daytona = candidate
    return [daytona] if daytona else None


def _cleanup_docker_containers(jobs_dir: Path) -> None:
    """Remove Docker compose projects for harbor trials under jobs_dir."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ls", "--all", "--format", "json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return
        projects = json.loads(result.stdout)
        jobs_str = str(jobs_dir.resolve())
        removed = 0
        for proj in projects:
            if jobs_str in proj.get("ConfigFiles", ""):
                name = proj.get("Name", "")
                if name:
                    subprocess.run(
                        ["docker", "compose", "-p", name, "down", "--remove-orphans"],
                        capture_output=True, check=False, timeout=30,
                    )
                    removed += 1
        if removed:
            typer.echo(f"  Removed {removed} Docker container(s).", err=True)
    except Exception as e:
        typer.echo(f"  Warning: Docker cleanup failed: {e}", err=True)


def _cleanup_sandboxes(sandbox_type: str = "daytona") -> None:
    """Kill the active harbor process and clean up sandboxes."""
    global _harbor_proc
    if _harbor_proc and _harbor_proc.poll() is None:
        typer.echo("\nTerminating harbor...", err=True)
        _harbor_proc.terminate()
        try:
            _harbor_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _harbor_proc.kill()
        _harbor_proc = None

    if sandbox_type == "docker":
        if _model_jobs_dir:
            _cleanup_docker_containers(_model_jobs_dir)
        return

    daytona = _daytona_cmd()
    if daytona:
        typer.echo("Cleaning up Daytona sandboxes...", err=True)
        subprocess.run(daytona + ["delete", "--all"], check=False)
    else:
        typer.echo(
            "daytona not found on PATH — delete sandboxes manually:\n"
            "  daytona delete --all -y",
            err=True,
        )


def _signal_handler(sig: int, frame: object) -> None:
    typer.echo(f"\nCaught signal {sig} — cleaning up.", err=True)
    _cleanup_sandboxes(_sandbox_type)
    sys.exit(1)


def _safe_name(model: str) -> str:
    """Filesystem-safe model name: qwen3.5:122b → qwen3_5-122b."""
    return model.replace(":", "-").replace("/", "-").replace(".", "_")


def _load_dotenv(env_file: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_file.exists():
        return env
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def _host_ip() -> str:
    """Return the primary outbound IP of this host (reachable from remote VMs)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def _rewrite_api_base_for_docker(api_base: str) -> str:
    """Rewrite localhost URLs to host.docker.internal for Docker sandbox access."""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(api_base)
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "::1"):
        new_host = "host.docker.internal"
        if parsed.port:
            new_netloc = f"{new_host}:{parsed.port}"
        else:
            new_netloc = new_host
        rewritten = urlunparse(parsed._replace(netloc=new_netloc))
        typer.echo(f"  [INFO] Rewrote api_base for Docker: {api_base} → {rewritten}")
        return rewritten
    return api_base


def _preflight(model: str, api_base: str, sandbox_type: str = "docker") -> None:
    """Check Ollama reachability and model availability. Abort on fatal issues."""
    typer.echo("\n--- Preflight checks ---")

    # 1. localhost warning — sandbox VMs resolve localhost to themselves, not the host
    from urllib.parse import urlparse
    parsed = urlparse(api_base)
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "::1"):
        if sandbox_type == "docker":
            typer.echo(
                f"  [INFO] api_base uses '{host}' — Docker containers will use host networking.\n"
                f"         Ensure Ollama is bound to 0.0.0.0: OLLAMA_HOST=0.0.0.0 ollama serve",
                err=True,
            )
        else:
            host_ip = _host_ip()
            typer.echo(
                f"  [WARN] api_base uses '{host}' — Daytona sandbox VMs cannot reach this.\n"
                f"         Ollama must bind to 0.0.0.0 and you should use:\n"
                f"         --api-base http://{host_ip}:{parsed.port or 11434}/v1\n"
                f"         To rebind Ollama: OLLAMA_HOST=0.0.0.0 ollama serve",
                err=True,
            )

    # 2. Ollama reachability — always test via local http regardless of api_base scheme/host
    # (api_base may be an ngrok/tunnel URL; we verify Ollama itself is up on the host)
    local_port = parsed.port or 11434
    tags_url = f"http://127.0.0.1:{local_port}/api/tags"

    try:
        with urllib.request.urlopen(tags_url, timeout=5) as resp:
            data = json.loads(resp.read())
        available = [m["name"] for m in data.get("models", [])]
        typer.echo(f"  [OK]   Ollama reachable at {tags_url}")
    except Exception as e:
        typer.echo(f"  [FAIL] Cannot reach Ollama at {tags_url}: {e}", err=True)
        typer.echo("         Is Ollama running? Try: ollama serve", err=True)
        raise typer.Exit(1)

    # 3. Model availability
    # Normalise: strip tag for prefix matching (qwen3.5:122b matches qwen3.5:122b)
    def _norm(name: str) -> str:
        return name.split(":")[0] if ":" not in name else name

    if model in available or any(a == model for a in available):
        typer.echo(f"  [OK]   Model '{model}' is available")
    else:
        typer.echo(f"  [FAIL] Model '{model}' not found in Ollama. Available:", err=True)
        for m in available:
            typer.echo(f"           {m}", err=True)
        raise typer.Exit(1)

    # 4. Ollama bind-address check — warn if only bound to 127.0.0.1
    # ss -tlnp output: State Recv-Q Send-Q Local:Port Peer:Port [Process]
    # The peer column always contains "0.0.0.0:*", so we must check the local
    # address field (col index 3) specifically, not the whole line.
    import subprocess as _sp
    result = _sp.run(["ss", "-tlnp"], capture_output=True, text=True)
    ollama_port = str(parsed.port or 11434)
    for line in result.stdout.splitlines():
        cols = line.split()
        if len(cols) < 4:
            continue
        local_addr = cols[3]  # e.g. "127.0.0.1:11434" or "0.0.0.0:11434" or "*:11434"
        if f":{ollama_port}" not in local_addr:
            continue
        local_host = local_addr.rsplit(":", 1)[0]
        if local_host in ("127.0.0.1", "::1"):
            if sandbox_type == "docker":
                typer.echo(f"  [OK]   Ollama bound to {local_host}:{ollama_port} (Docker uses host networking)")
            else:
                typer.echo(
                    f"  [WARN] Ollama is bound to {local_host}:{ollama_port} only.\n"
                    f"         Daytona cloud sandboxes CANNOT connect to it.\n"
                    f"         Expose Ollama publicly via ngrok/cloudflare tunnel, then\n"
                    f"         re-run with: --api-base https://<tunnel-url>/v1",
                    err=True,
                )
        else:
            typer.echo(f"  [OK]   Ollama bound to {local_host}:{ollama_port} (all interfaces)")
        break

    typer.echo("--- Preflight complete ---\n")


def _harbor_config(
    model: str,
    jobs_dir: Path,
    timeout_sec: int,
    concurrent: int,
    api_base: str,
    memory_mb: int,
    sandbox_type: str = "docker",
    context_window: int | None = None,
) -> dict:
    """Build Harbor YAML config for terminus-2 targeting Ollama."""
    environment: dict = {
        "type": sandbox_type,
        "override_cpus": 4,
        "override_memory_mb": memory_mb,
        "suppress_override_warnings": True,
    }

    agent_kwargs: dict = {"api_base": api_base}
    if context_window is not None:
        # Pass model_info directly — harbor's LiteLLM calls litellm.register_model()
        # with this dict, which is more reliable than patching the backup JSON on disk.
        agent_kwargs["model_info"] = {
            "max_tokens": context_window,
            "max_input_tokens": context_window,
            "max_output_tokens": context_window,
            "input_cost_per_token": 0.0,
            "output_cost_per_token": 0.0,
            "litellm_provider": "openai",
            "mode": "chat",
        }

    return {
        "jobs_dir": str(jobs_dir),
        "n_concurrent_trials": concurrent,
        "retry": {
            "max_retries": 3,
            "wait_multiplier": 2.5,
            "min_wait_sec": 60,
            "max_wait_sec": 300,
        },
        "environment": environment,
        "agents": [
            {
                "name": "terminus-2",
                # LiteLLM openai/ prefix + api_base routes to any OpenAI-compatible endpoint
                "model_name": f"openai/{model}",
                "override_timeout_sec": timeout_sec,
                "kwargs": agent_kwargs,
            }
        ],
        "datasets": [
            {
                "name": "terminal-bench",
                "version": "2.0",
            }
        ],
    }


def _report_run_errors(jobs_dir: Path) -> None:
    """Scan the latest run directory for sandbox/trial errors and print a summary."""
    if not jobs_dir.exists():
        return

    # Find the most recently modified run directory (timestamp-named subdirs)
    run_dirs = sorted(
        (d for d in jobs_dir.iterdir() if d.is_dir()),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not run_dirs:
        return

    latest = run_dirs[0]
    result_file = latest / "result.json"
    if not result_file.exists():
        return

    try:
        result = json.loads(result_file.read_text())
    except (json.JSONDecodeError, OSError):
        return

    stats = result.get("stats", {})
    n_trials = stats.get("n_trials", 0)
    n_errors = stats.get("n_errors", 0)
    if n_errors == 0:
        return

    typer.echo(f"\n--- Error summary ({n_errors}/{n_trials} trials failed) ---")

    # Collect exception types and affected tasks from result.json
    for eval_data in stats.get("evals", {}).values():
        for exc_type, tasks in eval_data.get("exception_stats", {}).items():
            if not tasks:
                continue
            typer.echo(f"  {exc_type}: {len(tasks)} task(s)")

            # Show the actual error message from the first task's exception.txt
            sample_task = tasks[0]
            exc_file = latest / sample_task / "exception.txt"
            if exc_file.exists():
                lines = exc_file.read_text().strip().splitlines()
                # Print only the last line (the actual error message)
                if lines:
                    typer.echo(f"    → {lines[-1]}")

            # List affected task names (truncated if many)
            if len(tasks) <= 5:
                for t in tasks:
                    typer.echo(f"    - {t}")
            else:
                for t in tasks[:3]:
                    typer.echo(f"    - {t}")
                typer.echo(f"    ... and {len(tasks) - 3} more")

    typer.echo("--- End error summary ---\n")


def _run_harbor(
    config_path: Path,
    env_file: Path,
    extra_env: dict[str, str],
    smoke: bool,
    run_label: str,
) -> bool:
    """Execute one harbor run. Returns True on success."""
    global _harbor_proc

    cmd = ["harbor", "run", "-c", str(config_path), "--env-file", str(env_file), "-y"]

    if smoke:
        cmd += [
            "-d", SMOKE_DATASET,
            "-l", "1",
        ]

    # Write extra_env to a temp env file so Harbor forwards them into the sandbox.
    # Passing via subprocess env alone is not sufficient — Harbor passes --env-file
    # contents to the Daytona sandbox, but not the host process environment.
    extra_env_file: Path | None = None
    if extra_env:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False, dir=config_path.parent, prefix="harbor-extra-"
        ) as f:
            for k, v in extra_env.items():
                f.write(f"{k}={v}\n")
            extra_env_file = Path(f.name)
        cmd += ["--env-file", str(extra_env_file)]

    typer.echo(f"\n[{run_label}] $ {' '.join(cmd)}")
    try:
        _harbor_proc = subprocess.Popen(cmd, env={**os.environ, **extra_env})
        _harbor_proc.wait()
        return _harbor_proc.returncode == 0
    finally:
        _harbor_proc = None
        if extra_env_file:
            extra_env_file.unlink(missing_ok=True)


def _collect_and_save(
    jobs_base: Path,
    results_path: Path,
    excluded_path: Path,
) -> tuple[list[dict], list[dict]]:
    """Scan local wolfbench-runs/, classify, write results JSON files."""
    sys.path.insert(0, str(WOLFBENCH_DIR))
    from wolfbench_collect import collect_local, split_runs, EXPECTED_TASKS  # type: ignore

    all_runs = collect_local(jobs_base)
    valid, excluded = split_runs(all_runs)

    now = datetime.now().isoformat()

    results_path.write_text(json.dumps({
        "collected_at": now,
        "n_vms": 0,
        "n_runs": len(valid),
        "benchmark": "terminal-bench-2.0",
        "expected_tasks": EXPECTED_TASKS,
        "vms": [],
        "runs": valid,
    }, indent=2))

    excluded_path.write_text(json.dumps({
        "collected_at": now,
        "n_vms": 0,
        "n_runs": len(excluded),
        "vms": [],
        "runs": excluded,
    }, indent=2))

    return valid, excluded


def _upload_to_weave(
    runs: list[dict],
    project: str,
    manifest_path: Path,
    jobs_base: Path,
) -> None:
    sys.path.insert(0, str(WOLFBENCH_DIR))
    from wolfbench_weave import upload_evaluations  # type: ignore

    asyncio.run(upload_evaluations(
        runs,
        project=project,
        manifest_path=manifest_path,
        local_runs_dir=jobs_base,
    ))


def _generate_chart(
    results_path: Path,
    chart_path: Path,
    manifest_path: Path | None,
) -> bool:
    cmd = [
        sys.executable,
        str(WOLFBENCH_DIR / "wolfbench-chart.py"),
        "-i", str(results_path),
        "-o", str(chart_path.with_suffix("")),  # chart.py appends .html
    ]
    if manifest_path and manifest_path.exists():
        cmd += ["--weave-manifest", str(manifest_path)]

    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


@app.command()
def main(
    model: Annotated[str, typer.Argument(help="Ollama model name, e.g. qwen3.5:122b")],
    smoke: Annotated[bool, typer.Option(
        "--smoke/--no-smoke",
        help="Smoke test: 1 task with short timeout (default: --smoke)",
    )] = True,
    runs: Annotated[int, typer.Option(
        "--runs", "-n",
        help="Number of full runs when --no-smoke (default: 1)",
        min=1,
    )] = 1,
    concurrent: Annotated[int, typer.Option(
        help="Concurrent sandboxes (default: 4; Daytona free tier: concurrent × memory_mb ≤ 10240)",
        min=1,
    )] = 4,
    timeout: Annotated[int | None, typer.Option(
        help="Per-task timeout in seconds (default: 600 for smoke, 3600 for full)",
    )] = None,  # None = auto
    memory: Annotated[int, typer.Option(
        "--memory",
        help="Sandbox memory in MB (default: 8192; Daytona free tier total ≤ 10240 MB)",
        min=512,
    )] = 8192,
    wandb_project: Annotated[str, typer.Option(
        "--wandb-project",
        help="W&B Weave project name (default: wolfbench-local)",
    )] = "wolfbench-local",
    jobs_base: Annotated[Path, typer.Option(
        "--jobs-dir",
        help="Base directory for all run output (default: wolfbench-runs/)",
    )] = DEFAULT_JOBS_BASE,
    env_file: Annotated[Path, typer.Option(
        help="Path to .env file with WANDB_API_KEY + DAYTONA_API_KEY",
    )] = WOLFBENCH_DIR / ".env",
    api_base: Annotated[str, typer.Option(
        help=f"Ollama OpenAI-compatible API base URL (default: {DEFAULT_API_BASE})",
    )] = DEFAULT_API_BASE,
    skip_upload: Annotated[bool, typer.Option(
        "--skip-upload",
        help="Skip W&B Weave upload",
    )] = False,
    skip_chart: Annotated[bool, typer.Option(
        "--skip-chart",
        help="Skip HTML chart generation",
    )] = False,
    context_window: Annotated[int | None, typer.Option(
        "--context-window",
        help="Model context window in tokens (registers with LiteLLM for unmapped models, e.g. 262144)",
    )] = None,
    sandbox: Annotated[str, typer.Option(
        "--sandbox",
        help="Sandbox type: 'docker' runs locally in Docker containers, 'daytona' uses cloud VMs (default: docker)",
    )] = "docker",
) -> None:
    """Run WolfBench against a local Ollama model via Terminal-Bench 2.0."""
    global _sandbox_type, _model_jobs_dir

    # Validate sandbox choice
    if sandbox not in SANDBOX_CHOICES:
        typer.echo(f"Invalid --sandbox '{sandbox}'. Choose from: {', '.join(SANDBOX_CHOICES)}", err=True)
        raise typer.Exit(1)
    _sandbox_type = sandbox

    # Resolve timeout
    effective_timeout = timeout if timeout is not None else (600 if smoke else 3600)

    safe = _safe_name(model)
    model_jobs_dir = jobs_base / f"t2-ollama-{safe}"
    _model_jobs_dir = model_jobs_dir
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = WOLFBENCH_DIR / f"wolfbench_results_{safe}_{ts}.json"
    excluded_path = WOLFBENCH_DIR / f"wolfbench_results_{safe}_{ts}_excluded.json"
    manifest_path = WOLFBENCH_DIR / f"{wandb_project}-manifest.json"
    chart_path = WOLFBENCH_DIR / f"wolfbench_{safe}_{ts}.html"

    typer.echo(f"Model:    {model} (via {api_base})")
    typer.echo(f"Mode:     {'smoke (1 task)' if smoke else f'{runs} full run(s) × 89 tasks'}")
    typer.echo(f"Timeout:  {effective_timeout}s per task")
    typer.echo(f"Sandbox:  {sandbox}")
    typer.echo(f"Sandboxes: {concurrent} concurrent × {memory} MB = {concurrent * memory} MB total")
    typer.echo(f"Jobs dir: {model_jobs_dir}")
    typer.echo(f"Env file: {env_file}")

    # Register signal handlers so Ctrl+C / SIGTERM cleans up Daytona sandboxes
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Verify .env exists and has required keys
    dotenv = _load_dotenv(env_file)
    required_keys = ["WANDB_API_KEY"]
    if sandbox == "daytona":
        required_keys.append("DAYTONA_API_KEY")
    missing = [k for k in required_keys if k not in dotenv]
    if missing:
        typer.echo(f"Warning: missing from {env_file}: {', '.join(missing)}", err=True)

    # Preflight: verify Ollama is reachable, model exists, and bind-address is suitable
    _preflight(model, api_base, sandbox)

    # For Docker sandbox, rewrite localhost URLs so containers can reach the host
    effective_api_base = _rewrite_api_base_for_docker(api_base) if sandbox == "docker" else api_base

    # LiteLLM needs OPENAI_API_KEY set (any non-empty value) for openai/ prefix
    extra_env = {
        "OPENAI_API_KEY": "ollama",
        "OPENAI_API_BASE": effective_api_base,
    }


    # Write Harbor config to a temp file
    config = _harbor_config(model, model_jobs_dir, effective_timeout, concurrent, effective_api_base, memory, sandbox, context_window)
    if context_window:
        typer.echo(f"  [OK]   Registered 'openai/{model}' with {context_window:,} token context window")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=WOLFBENCH_DIR, prefix="harbor-ollama-"
    ) as f:
        yaml.dump(config, f, default_flow_style=False)
        config_path = Path(f.name)

    n_runs = 1 if smoke else runs
    success_count = 0

    try:
        for i in range(1, n_runs + 1):
            label = "smoke" if smoke else f"run {i}/{n_runs}"
            ok = _run_harbor(config_path, env_file, extra_env, smoke, label)
            _report_run_errors(model_jobs_dir)
            if ok:
                success_count += 1
            else:
                typer.echo(f"[{label}] harbor exited with an error", err=True)
    finally:
        config_path.unlink(missing_ok=True)

    typer.echo(f"\n{success_count}/{n_runs} run(s) completed.")

    if success_count == 0:
        typer.echo("No successful runs — aborting post-processing.", err=True)
        raise typer.Exit(1)

    # Collect and classify results
    typer.echo("\nCollecting results from local storage...")
    valid, excluded = _collect_and_save(jobs_base, results_path, excluded_path)
    typer.echo(f"  Valid runs:    {len(valid)}")
    typer.echo(f"  Excluded runs: {len(excluded)}")

    if smoke and not valid:
        typer.echo("\nSmoke test complete. Runs are excluded from leaderboard (<89 tasks).")
        typer.echo(f"  Excluded details: {excluded_path}")

    # Upload to W&B Weave
    upload_runs = valid if valid else (excluded if smoke else [])
    if not skip_upload and upload_runs:
        typer.echo(f"\nUploading {len(upload_runs)} run(s) to W&B project '{wandb_project}'...")
        try:
            _upload_to_weave(upload_runs, wandb_project, manifest_path, jobs_base)
            typer.echo("  Upload complete.")
        except Exception as e:
            typer.echo(f"  Upload failed: {e}", err=True)
    elif skip_upload:
        typer.echo("\nSkipping W&B upload (--skip-upload).")

    # Generate chart (only meaningful for full valid runs)
    if not skip_chart and valid:
        typer.echo("\nGenerating chart...")
        ok = _generate_chart(results_path, chart_path, manifest_path)
        if ok and chart_path.exists():
            typer.echo(f"  Chart: {chart_path}")
        else:
            typer.echo("  Chart generation failed.", err=True)
    elif not valid:
        typer.echo("\nSkipping chart (no valid full runs yet).")
    elif skip_chart:
        typer.echo("\nSkipping chart (--skip-chart).")

    typer.echo(f"\nDone. Results: {results_path}")


if __name__ == "__main__":
    app()
