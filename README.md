# WolfBench

[wolfbench.ai](https://wolfbench.ai/) · Wolfram Ravenwolf's Five-Metric Framework · based on Terminal-Bench 2.0

## Five-Metric Framework

> **One score is not enough.**  \
> **Because performance is a distribution, not a point.**

Most benchmarks report a single average. **WolfBench** shows five metrics that tell the full story – from the **rock-solid base** of tasks solved every time, through the **average**, up to the **ceiling** of everything ever solved – plus the **best** and **worst** single runs that frame the spread. Together, they reveal what no single number can: how consistent an AI agent truly is.

| Metric       | Symbol | Definition                                     | Answers                            |
| ------------ | ------ | ---------------------------------------------- | ---------------------------------- |
| **Ceiling**  | ★      | Union of all tasks ever solved across all runs | "What's theoretically possible?"   |
| **Best-of**  | ▲      | Highest score from any single run              | "What's the peak in a single run?" |
| **Average**  | ∅      | Mean score across all valid runs               | "What can you normally expect?"    |
| **Worst-of** | ▼      | Lowest score from any single run               | "How bad can a single run get?"    |
| **Solid**    | ■      | Tasks solved across _all_ runs (zero variance) | "What does it always get right?"   |

The spread between them tells you as much as the numbers themselves:

- **Tight spread** (metrics close together) = consistent, predictable agent
- **Wide spread** (big gap between solid and ceiling) = high variance, unreliable
- **High ceiling, low average** = the model _can_ do it, but usually doesn't
- **High solid, moderate average** = dependable in practice, even if not flashy

## Why WolfBench is Different

- **Five-metric framework:** Instead of a single average score, five complementary metrics paint a far more complete picture of what an AI agent can actually do – from the worst-case floor to the theoretical ceiling.
- **Uniform conditions:** Every task in a run gets the same timeout and identical sandbox resources. Scores reflect model and agent capability – not whether an inference endpoint was temporarily overloaded or a sandbox ran out of memory.
- **Multi-agent comparison:** Same model, different agents. Same agent, different models. Different timeouts, concurrency levels, thinking modes. The goal is to understand what _matters_ – not just what scored highest in one particular instance.
- **Multi-run methodology:** A single run is statistically meaningless – variance can swing results widely. Multiple replicates per configuration yield stable, trustworthy numbers.
- **Transparency:** Every run is collected, classified, and curated with full metadata: tokens consumed, cache hit rates, duration, timeout, concurrency, agent version, thinking mode. All traces and evaluations are published on [W&B Weave](https://wandb.ai/wolfram-evals/wolfbench).

## What This Repo Contains

This repository is the open-source engine behind [wolfbench.ai](https://wolfbench.ai/) — the methodology, the tooling pipeline, all run data, and complete instructions for running and reproducing the benchmarks. It contains the dashboard, chart generator, data collector, and Weave uploader that turn raw benchmark runs into the interactive leaderboard on the website.

The benchmark tasks themselves come from [Terminal-Bench 2.0](https://www.tbench.ai/), orchestrated by the [Harbor](https://github.com/harbor-framework/harbor) framework (or [this fork](https://github.com/WolframRavenwolf/harbor/tree/openclaw-agent) which adds the OpenClaw agent). Harbor runs the tasks in [Daytona](https://www.daytona.io/) sandboxes on ephemeral VMs — this repo picks up the results from there.

All run data (configs and results) lives in `wolfbench-runs/`, organized by configuration and timestamp. Full trajectories, evaluations, and traces are uploaded to [W&B Weave](https://wandb.ai/wolfram-evals/wolfbench).

### Core Scripts

| File                     | Type        | Role                                                                                                             |
| ------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------- |
| `wolfbench-dashboard.py` | Entry point | Marimo reactive notebook. Orchestrates scanning, filtering, downloading, saving, uploading, and chart generation |
| `wolfbench-chart.py`     | Entry point | Generates standalone interactive HTML charts from `wolfbench_results.json`                                       |
| `wolfbench_collect.py`   | Library     | SSH scanner. Discovers VMs (exe.dev, Hetzner), reads results, deduplicates, classifies runs                      |
| `wolfbench_weave.py`     | Library     | W&B Weave integration. Two-tier upload (evaluations + full traces), manifest management                          |

Entry points use kebab-case (never imported). Libraries use snake_case (importable).

## Running the Benchmark

WolfBench evaluates AI agents on [Terminal-Bench 2.0](https://www.tbench.ai/) (89 tasks) using the [Harbor](https://github.com/harbor-framework/harbor) framework for orchestration and [Daytona](https://www.daytona.io/) sandboxes for isolated execution. Benchmarks run on [exe.dev](https://exe.dev/) or [Hetzner](https://www.hetzner.com/cloud/) VMs.

Harbor supports multiple agents out of the box: **Terminus-2** (Harbor's native agent), **Claude Code**, and — via the [openclaw-agent branch](https://github.com/WolframRavenwolf/harbor/tree/openclaw-agent) — **OpenClaw**.

### 1. Create and Provision a VM

```sh
# Pick a name for this eval run
name=wolfbench-evals-…

# Create VM on exe.dev
ssh exe.dev new --name="${name:?}"

# Clone Harbor, install deps, suppress LiteLLM debug spam
ssh -o StrictHostKeyChecking=accept-new "${name:?}.exe.xyz" '
git clone https://github.com/WolframRavenwolf/harbor -b openclaw-agent &&
uv sync --project harbor &&
sed -i~ "/suppress_debug_info/s/False/True/" ~/harbor/.venv/lib/python3.13/site-packages/litellm/__init__.py
'
```

### 2. Inject API Keys

Uses [1Password CLI](https://developer.1password.com/docs/cli/) (`op inject`) to securely template secrets:

```sh
op inject -i /dev/stdin << 'EOF' | ssh "${name:?}.exe.xyz" 'cat > ~/harbor/.env && chmod 600 ~/harbor/.env'
DAYTONA_API_KEY={{ op://Employee/Daytona API Key/credential }}

ANTHROPIC_API_KEY={{ op://Employee/Anthropic API Key/credential }}
GEMINI_API_KEY={{ op://Employee/Gemini API Key/credential }}
MISTRAL_API_KEY={{ op://Employee/Mistral API Key/credential }}
OPENAI_API_KEY={{ op://Employee/OpenAI API Key/credential }}
OPENROUTER_API_KEY={{ op://Employee/OpenRouter API Key/credential }}

WANDB_API_KEY={{ op://Employee/WandB API Key/credential }}
WANDB_BASE_URL=https://api.inference.wandb.ai/v1
EOF
```

### 3. SSH In and Set Up tmux

```sh
ssh "${name:?}.exe.xyz"

# Enable mouse scrolling in tmux
echo "set -g mouse on" >> ~/.tmux.conf && tmux source ~/.tmux.conf

# Start (or reattach to) a tmux session
tmux new -A

cd ~/harbor
```

### 4. Create Config Files

Harbor uses YAML configs. Replace `…` placeholders with actual values.

**Terminus-2 config** (`t2-*.yaml`):

```sh
mkdir -p ~/harbor/configs && cat << 'EOF' > ~/harbor/configs/t2-….yaml
jobs_dir: jobs/t2-…

orchestrator:
  n_concurrent_trials: 32
  retry:
    max_retries: 3
    wait_multiplier: 2.5
    min_wait_sec: 60   # 1 min
    max_wait_sec: 300  # 5 min (caps retry 3)

environment:
  type: daytona
  override_cpus: 4             # Default: 1, Daytona Sandbox Limit: 4, Recommended: 16
  override_memory_mb: 8192     # Default: 2 GB, Daytona Sandbox Limit: 8 GB, Recommended: 32 GB
  #override_storage_mb: 10240  # Default: 10 GB, Daytona Sandbox Limit: 10 GB, Recommended: 10 GB
  suppress_override_warnings: true

agents:
  - name: terminus-2
    model_name: …/…/…
    override_timeout_sec: 3600  # 1 hour (Terminal-Bench 2.0: max 12000s = 200 min = 3h20m)

datasets:
  - name: terminal-bench
    version: "2.0"
    registry: {}
EOF
```

**Claude Code config** (`cc-*.yaml`):

```sh
mkdir -p ~/harbor/configs && cat << 'EOF' > ~/harbor/configs/cc-….yaml
jobs_dir: jobs/cc-…

orchestrator:
  n_concurrent_trials: 32
  retry:
    max_retries: 3
    wait_multiplier: 2.5
    min_wait_sec: 60   # 1 min
    max_wait_sec: 300  # 5 min (caps retry 3)

environment:
  type: daytona
  override_cpus: 4             # Default: 1, Daytona Sandbox Limit: 4, Recommended: 16
  override_memory_mb: 8192     # Default: 2 GB, Daytona Sandbox Limit: 8 GB, Recommended: 32 GB
  #override_storage_mb: 10240  # Default: 10 GB, Daytona Sandbox Limit: 10 GB, Recommended: 10 GB
  suppress_override_warnings: true

agents:
  - name: claude-code
    model_name: …/…/…
    override_timeout_sec: 3600  # 1 hour (Terminal-Bench 2.0: max 12000s = 200 min = 3h20m)
    kwargs:
      version: "2.1.75"  # Claude Code version

datasets:
  - name: terminal-bench
    version: "2.0"
    registry: {}
EOF
```

**OpenClaw config** (`oc-*.yaml`):

```sh
mkdir -p ~/harbor/configs && cat << 'EOF' > ~/harbor/configs/oc-….yaml
jobs_dir: jobs/oc-…

orchestrator:
  n_concurrent_trials: 32
  retry:
    max_retries: 3
    wait_multiplier: 2.5
    min_wait_sec: 60   # 1 min
    max_wait_sec: 300  # 5 min (caps retry 3)

environment:
  type: daytona
  override_cpus: 4             # Default: 1, Daytona Sandbox Limit: 4, Recommended: 16
  override_memory_mb: 8192     # Default: 2 GB, Daytona Sandbox Limit: 8 GB, Recommended: 32 GB
  #override_storage_mb: 10240  # Default: 10 GB, Daytona Sandbox Limit: 10 GB, Recommended: 10 GB
  suppress_override_warnings: true

agents:
  - name: openclaw
    model_name: …/…/…
    override_timeout_sec: 3600  # 1 hour (Terminal-Bench 2.0: max 12000s = 200 min = 3h20m)
    kwargs:
      version: "2026.3.11"     # OpenClaw version
      #context_window: 200000  # OpenClaw contextWindow (Default for unknown models: 200000)
      #max_tokens: 8192        # OpenClaw maxTokens (Default for unknown models: 8192)
      #temperature: 1.0        # OpenClaw temperature
      #thinking: low           # OpenClaw thinkingDefault (off, minimal, low, medium, high, xhigh; Default: low)

datasets:
  - name: terminal-bench
    version: "2.0"
    registry: {}
EOF
```

### 5. Run Evals

```sh
# Quick test (1 task, 3 min)
uv run harbor run -c ~/harbor/configs/oc-….yaml \
  -d terminal-bench-sample@2.0 \
  --jobs-dir ~/harbor/jobs/oc-…-test \
  -l 1 --timeout-multiplier 0.05 --agent-setup-timeout-multiplier 1.0

# Sample run (10 tasks)
uv run harbor run -c ~/harbor/configs/oc-….yaml \
  -d terminal-bench-sample@2.0 \
  --jobs-dir "jobs/oc-…-sample"

# Full run (89 tasks)
uv run harbor run -c ~/harbor/configs/oc-….yaml

# 5x full (5×89 = 445 tasks, ~5h)
RUNS=5
for run in $(seq 1 $RUNS); do
  uv run harbor run -c ~/harbor/configs/oc-….yaml
done

# Terminus-2
RUNS=5
for run in $(seq 1 $RUNS); do
  uv run harbor run -c ~/harbor/configs/t2-….yaml
done
```

### Config Reference

| Field                              | Description                                                             |
| ---------------------------------- | ----------------------------------------------------------------------- |
| `jobs_dir`                         | Output directory for results (relative to `~/harbor/`)                  |
| `n_concurrent_trials`              | Parallel Daytona sandboxes (32 recommended)                             |
| `override_timeout_sec`             | Per-task timeout in seconds (3600 = 1h, 7200 = 2h)                      |
| `model_name`                       | Provider/model path (e.g., `anthropic/claude-opus-4-6`)                 |
| `kwargs.version`                   | OpenClaw version (agent-specific)                                       |
| `kwargs.thinking`                  | OpenClaw thinking level: off, minimal, low, medium, high, xhigh         |
| `--ak 'key=value'`                 | CLI override for agent kwargs                                           |
| `-d dataset@version`               | Override dataset (e.g., `terminal-bench-sample@2.0` for 10-task subset) |
| `-l N`                             | Limit to N tasks                                                        |
| `--timeout-multiplier`             | Scale all timeouts (0.333 = 1/3 of configured timeout)                  |
| `--agent-setup-timeout-multiplier` | Scale agent setup timeout (use 1.0 with low `--timeout-multiplier`)     |

## Collecting Results & Publishing

After benchmark runs complete on the VMs, the WolfBench tooling takes over: scan the results, download them, curate, and publish.

### Data Flow

```
VMs (Harbor runs)
  |
  | SSH scan (wolfbench_collect)
  v
Local Storage (wolfbench-runs/<config>/<timestamp>/)
  |
  | download once, VMs can be torn down
  v
wolfbench_results.json (curated snapshot)
  |
  +---> wolfbench.ai (interactive HTML chart)
  |
  +---> W&B Weave (evaluations + full traces)
```

### Running the Dashboard

```sh
export WANDB_API_KEY=$(op item get "WandB API Key" --fields credential --reveal)
export WANDB_PROJECT=wolfbench
export UPLOAD_TARGET=wolfbench.exe.xyz:wolfbench

uvx marimo run --sandbox wolfbench-dashboard.py
```

Opens at http://localhost:2718. The dashboard walks through the entire pipeline:

```
Step 1: Select VMs → Scan (local first + VMs, deduplicated)
Step 2: Review / Filter / Select (classify valid vs. excluded runs)
Step 3: Download to Local Storage
Step 4: Upload to W&B Weave
Step 5: Save Results (wolfbench_results.json + wolfbench_results_excluded.json)
Step 6: Generate Chart (interactive HTML, opens in browser)
Step 7: Upload Chart (scp to wolfbench.ai server)
```

### Local Storage

Downloaded run data lives in `wolfbench-runs/`, mirroring the VM directory structure:

```
wolfbench-runs/
  <config-name>/
    <YYYY-MM-DD__HH-MM-SS>/
      config.json              # agent configuration
      result.json              # run-level results
      evals/
        <agent>__<model>__<dataset>/
          <task>__<hash>/
            result.json        # per-task result
            agent/
              trajectory.json  # full conversation trace (ATIF v1.6)
```

Local storage is scanned first. Deduplication (first-wins) means local copies automatically shadow VM originals. Once downloaded, VMs can be torn down — all data persists locally.

### W&B Weave Integration

All evaluations and full agent traces are uploaded to [W&B Weave](https://wandb.ai/wolfram-evals/wolfbench) in a single pass: per-task metrics from result.json, plus nested conversation traces from trajectory.json files (when available). Chart bars link directly to Weave evaluations when a manifest exists. Upload manifests (`{project}-manifest.json`) track what's been uploaded per Weave project.

### Generated Files

| File                                | Description                                                   |
| ----------------------------------- | ------------------------------------------------------------- |
| `wolfbench_results_*.json`          | Curated result snapshot (valid runs only)                     |
| `wolfbench_results_excluded_*.json` | Excluded runs (infra failures, invalid configs, etc.)         |
| `wolfbench-overrides.json`          | Manual display overrides (model names, thinking labels, etc.) |
| `wolfbench_*.html`                  | Interactive charts for wolfbench.ai                           |
| `*-manifest.json`                   | Weave upload tracking per project                             |

## Dependencies

- **Python 3.12+**
- **Marimo** (dashboard)
- **weave**, **wandb** (Weave upload)
- **SSH access** to VMs (for initial data collection)
- Core scripts (`wolfbench_collect.py`, `wolfbench-chart.py`) have no external dependencies beyond stdlib

## License

- Code: **Apache-2.0**
- Data: **CC-BY-4.0**

---

Inference sponsored by [CoreWeave](https://www.coreweave.com/): The Essential Cloud for AI.  \
Sandbox compute by [Daytona](https://www.daytona.io/) – Secure Infrastructure for Running AI-Generated Code.  \
Built with [Harbor](https://harborframework.com/) for orchestration, [Terminal-Bench 2.0](https://www.tbench.ai/) for tasks, and [W&B Weave](https://wandb.ai/) for tracking.  \
Charts and dashboards generated with [marimo](https://marimo.io/) notebooks.  \
Explore the interactive chart and model/agent leaderboard on the [WolfBench website](https://wolfbench.ai/).
