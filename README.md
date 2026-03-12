# WolfBench

Wolfram Ravenwolf's Four-Metric Evaluation Framework for Agentic Benchmarks, based on [Terminal-Bench 2.0](https://github.com/harbor-framework/terminal-bench).

## Four-Metric Framework

> **One score is not enough.**  \
> **Because performance is a distribution, not a point.**

Most benchmarks report just a single average. WolfBench shows four metrics:

| Metric      | Definition                                         | Answers                          |
| ----------- | -------------------------------------------------- | -------------------------------- |
| **Ceiling** | Union of all solved tasks (ever solved by any run) | "What's the theoretical max?"    |
| **Best-of** | Peak score in any single run                       | "What's possible on a good day?" |
| **Average** | Mean score across runs                             | "What's typical?"                |
| **Solid**   | Tasks solved in _every_ run                        | "What can we rely on?"           |

The spread between them tells you how consistent – or how unpredictable – an AI agent really is.

## Architecture

### Core Scripts

| File                     | Type        | Role                                                                                                             |
| ------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------- |
| `wolfbench-dashboard.py` | Entry point | Marimo reactive notebook. Orchestrates scanning, filtering, downloading, saving, uploading, and chart generation |
| `wolfbench-chart.py`     | Entry point | Generates standalone interactive HTML charts from `harbor_results.json`                                          |
| `wolfbench_collect.py`   | Library     | SSH scanner. Discovers VMs (exe.dev, Hetzner), reads results, deduplicates, classifies runs                      |
| `wolfbench_weave.py`     | Library     | W&B Weave integration. Two-tier upload (evaluations + full traces), manifest management                          |

Entry points use kebab-case (never imported). Libraries use snake_case (importable).

### Data Flow

```
VMs (Harbor runs)
  |
  | SSH scan (wolfbench_collect)
  v
Local Storage (runs/<config>/<timestamp>/)
  |
  | download once, VMs no longer needed
  v
harbor_results.json (save)
  |
  +---> wolfbench_YYYY-MM-DD.html (chart)
  |
  +---> W&B Weave (upload evaluations + traces)
```

### Dashboard Workflow

```
Step 1: Select VMs (0 = local only)
        Scan (local first + VMs) -> dedup -> results table
Step 2: Review / Filter / Select
Step 3: Download to Local Storage
Step 4: Save Results (harbor_results.json)
Step 5: Upload to W&B Weave
Step 6: Generate Chart
```

### Local Storage

Downloaded run data lives in `runs/`, mirroring the VM directory structure:

```
runs/
  <config-name>/
    <YYYY-MM-DD__HH-MM-SS>/
      result.json           # run-level results
      config.json           # agent configuration
      _meta.json            # provenance (source VM, download time)
      evals/
        <agent>__<model>__<dataset>/
          <task>__<hash>/
            result.json     # per-task result
            agent/
              trajectory.json  # full conversation trace (ATIF v1.6)
```

Local storage is scanned first. Deduplication (first-wins) means local copies automatically shadow VM originals. Local storage is project-agnostic; Weave upload manifests (`{project}-manifest.json`) track uploads per project separately.

### W&B Weave Integration

Two-tier upload to [Weights & Biases Weave](https://wandb.ai/site/weave):

- **Tier 1 (Evaluations):** Pass/fail per task from summary data. Fast, no SSH needed.
- **Tier 2 (Traces):** Full agent conversation traces from trajectory.json files. Uploads nested call hierarchies (agent_run > llm_call/tool_result/user_message).

Chart bars link to Weave evaluations when a manifest exists.

## Supporting Files

| Category               | Description                                     |
| ---------------------- | ----------------------------------------------- |
| `harbor_results*.json` | Timestamped result snapshots (valid + excluded) |
| `wolfbench*.html`      | Generated interactive charts                    |
| `*-manifest.json`      | Weave upload tracking per project               |

## Running Benchmarks

Benchmarks run on [exe.dev](https://exe.dev/) VMs via [Harbor](https://harborframework.com/) orchestration with [Daytona](https://www.daytona.io/) sandboxes.

### 1. Create and Provision a VM

```sh
# Pick a name for this eval run
name=harbor-evals-…

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
OPENAI_API_KEY={{ op://Employee/OpenAI API Key/credential }}
OPENROUTER_API_KEY={{ op://Employee/OpenRouter API Key/credential }}

WANDB_API_KEY={{ op://Employee/WandB API Key/credential }}
WANDB_BASE_URL=https://api.inference.wandb.ai/v1

WANDBQA_API_KEY={{ op://Employee/WandB API Key QA-Staging/credential }}
WANDBQA_BASE_URL=https://api.qa.inference.wandb.ai/v1
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
      version: "2026.3.1"      # OpenClaw version
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

### 5. Run Evals

```sh
# Quick test (1 task, ~5m)
uv run harbor run -c ~/harbor/configs/oc-….yaml \
  -d terminal-bench-sample@2.0 \
  --jobs-dir ~/harbor/jobs/oc-…-test \
  -l 1 --timeout-multiplier 0.08

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
uv run harbor run -c ~/harbor/configs/t2-….yaml
```

### Config Reference

| Field                  | Description                                                             |
| ---------------------- | ----------------------------------------------------------------------- |
| `jobs_dir`             | Output directory for results (relative to `~/harbor/`)                  |
| `n_concurrent_trials`  | Parallel Daytona sandboxes (32 recommended)                             |
| `override_timeout_sec` | Per-task timeout in seconds (3600 = 1h, 7200 = 2h)                      |
| `model_name`           | Provider/model path (e.g., `anthropic/claude-opus-4-6`)                 |
| `kwargs.version`       | OpenClaw version (agent-specific)                                       |
| `kwargs.thinking`      | OpenClaw thinking level: off, minimal, low, medium, high, xhigh         |
| `--ak 'key=value'`     | CLI override for agent kwargs                                           |
| `-d dataset@version`   | Override dataset (e.g., `terminal-bench-sample@2.0` for 10-task subset) |
| `-l N`                 | Limit to N tasks                                                        |
| `--timeout-multiplier` | Scale all timeouts (0.333 = 1/3 of configured timeout)                  |

## Running the Dashboard

```sh
export WANDB_API_KEY=$(op item get "WandB API Key" --fields credential --reveal)
export WANDB_PROJECT=wolfbench

uvx marimo run --sandbox wolfbench-dashboard.py
```

Opens at http://localhost:2718. From there, scan VMs (or local only), review results, download, save, upload to Weave, and generate charts — all in one workflow.

## Dependencies

- **Python 3.12+**
- **Marimo** (dashboard)
- **weave**, **wandb** (Weave upload)
- **SSH access** to VMs (for initial data collection)
- Core scripts (`wolfbench_collect.py`, `wolfbench-chart.py`) have no external dependencies beyond stdlib

## License

TBD

---

Inference sponsored by [CoreWeave](https://www.coreweave.com/): The Essential Cloud for AI.  \
Sandbox compute by [Daytona](https://www.daytona.io/) – Secure Infrastructure for Running AI-Generated Code.  \
Built with [Harbor](https://harborframework.com/) for orchestration, [Terminal-Bench 2.0](https://www.tbench.ai/) for tasks, and [W&B Weave](https://wandb.ai/) for tracking.  \
Charts and dashboards generated with [marimo](https://marimo.io/) notebooks.
