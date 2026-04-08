# Running WolfBench with a Local Ollama Model

This guide covers running WolfBench benchmarks against a model served by a local [Ollama](https://ollama.com/) instance using `wolfbench-ollama.py`.

## How it works

WolfBench tasks run inside **Daytona cloud sandboxes** — ephemeral VMs on Daytona's infrastructure, not your local machine. The agent inside each sandbox calls your Ollama API over the internet, so your local Ollama must be publicly reachable via a tunnel.

```
Daytona cloud VM  →  tunnel URL  →  your machine  →  Ollama (port 11434)
```

---

## Prerequisites

### 1. Install Harbor

Harbor orchestrates the benchmark tasks. Install it via uv:

```bash
uv tool install harbor
```

### 2. Install and log in to the Daytona CLI

Harbor uses the Daytona API to spin up sandboxes. Install the CLI to manage them:

```bash
# macOS / Linux via Homebrew
brew install daytonaio/cli/daytona

# Or download directly from https://github.com/daytonaio/daytona/releases
```

> **Linux/Homebrew note:** If installed via Linuxbrew, the binary may not be on your PATH automatically. Add it:
> ```bash
> echo 'export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"' >> ~/.bashrc
> source ~/.bashrc
> ```

Log in (required before any run):

```bash
daytona login
```

Keep the CLI version in sync with the API to avoid warnings:

```bash
brew upgrade daytonaio/cli/daytona
```

### 3. Create a `.env` file

The script reads API keys from a `.env` file in the project root. Create it with your credentials:

```bash
cat > .env <<'EOF'
WANDB_API_KEY=your_wandb_api_key_here
DAYTONA_API_KEY=your_daytona_api_key_here
EOF
```

- **WANDB_API_KEY** — from [wandb.ai/settings](https://wandb.ai/settings) (needed for results upload)
- **DAYTONA_API_KEY** — from [app.daytona.io/settings](https://app.daytona.io/settings) (needed for sandbox creation)

### 4. Pull your model in Ollama

```bash
ollama pull qwen3.5:122b
```

Verify it is available:

```bash
ollama list
```

### 5. Expose Ollama publicly via a tunnel

Ollama listens on `localhost:11434` by default — Daytona cloud VMs cannot reach a private LAN address. Choose one of the following tunnel options:

#### Option A — ngrok (easiest, free tier available)

```bash
# Install: https://ngrok.com/download
ngrok http 11434
# Copy the Forwarding URL, e.g. https://abc123.ngrok-free.dev
```

#### Option B — Cloudflare Tunnel (free, no account needed for quick tunnels)

```bash
# Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared tunnel --url http://localhost:11434
# Copy the trycloudflare.com URL printed to stdout
```

#### Option C — Tailscale Funnel (if you already use Tailscale)

```bash
tailscale funnel 11434
# Your Tailscale hostname becomes publicly reachable on port 11434
# Use: https://<your-machine>.ts.net/v1 as --api-base
```

> **Important:** Keep your tunnel process running for the full duration of the benchmark. ngrok free tier tunnels expire when the process stops. For a full run (89 tasks × up to 1 hour each), that can be many hours.

---

## Before every run — clean up leftover sandboxes

Failed or interrupted runs can leave Daytona sandboxes consuming your quota (free tier: 10 GiB total). Always clean up before starting a new run:

```bash
daytona delete --all
daytona list   # confirm empty
```

> The script also cleans up sandboxes automatically if you press **Ctrl+C** during a run.

---

## Finding your model's context window

Pass the correct context window via `--context-window` so the agent uses the model's full capacity. Query Ollama directly:

```bash
curl -s http://localhost:11434/api/show -d '{"name":"qwen3.5:122b"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model_info',{}).get('llama.context_length','unknown'))"
```

For `qwen3.5:122b` the context window is **262144** (256k tokens).

---

## Running the benchmark

```bash
uv run wolfbench-ollama.py qwen3.5:122b \
  --no-smoke \
  --concurrent 4 \
  --memory 8192 \
  --runs 5 \
  --api-base https://<your-tunnel-url>/v1 \
  --context-window 262144
```

### Key options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-base` | Public tunnel URL pointing to your Ollama instance | `http://localhost:11434/v1` |
| `--context-window` | Model context window in tokens — patches LiteLLM so the agent uses the model's full context | None |
| `--concurrent` | Number of simultaneous Daytona sandboxes | 4 |
| `--memory` | Memory per sandbox in MB. Free tier total: 10 GiB. Keep `concurrent × memory ≤ 10240` | 8192 |
| `--no-smoke` | Run the full 89-task benchmark. Omit to run a 1-task smoke test first | smoke mode on |
| `--runs` | Number of full benchmark runs (multi-run methodology gives more stable scores) | 1 |
| `--skip-upload` | Skip W&B Weave upload | false |
| `--skip-chart` | Skip HTML chart generation | false |

### Free tier sandbox limits

With `--concurrent 4 --memory 8192` you use max free tier for one sandbox at a time.

The sandbox memory is for the benchmark agent and test environment. The model runs on your host machine, so sandbox memory does **not** affect inference quality or speed.

To run more sandboxes concurrently, upgrade your Daytona tier at [app.daytona.io/dashboard/limits](https://app.daytona.io/dashboard/limits).

### Smoke test first

Before committing to a full 89-task run, do a quick 1-task smoke test to verify connectivity end-to-end:

```bash
uv run wolfbench-ollama.py qwen3.5:122b \
  --api-base https://<your-tunnel-url>/v1 \
  --context-window 262144
```

(No `--no-smoke` = smoke mode. Runs 1 task with a 600s timeout.)

---

## Preflight checks

The script runs automatic checks before starting Harbor and will abort on fatal issues:

```
--- Preflight checks ---
  [OK]   Ollama reachable at http://127.0.0.1:11434/api/tags
  [OK]   Model 'qwen3.5:122b' is available
  [OK]   Ollama bound to *:11434 (all interfaces)
  [OK]   Registered 'openai/qwen3.5:122b' with 262,144 token context window
--- Preflight complete ---
```

If the `--context-window` registration line is missing, the agent falls back to an internal default (10k tokens), which may not reflect the model's true limit and may break something ... 

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Total memory limit exceeded` | Leftover sandboxes from a previous run | `daytona delete --all` then retry |
| `Sandbox not found` | Daytona not logged in, or memory limit hit | `daytona login` then `daytona delete --all` |
| `daytona: command not found` | Linuxbrew install not on PATH | Add `/home/linuxbrew/.linuxbrew/bin` to PATH |
| Version mismatch warning from daytona | CLI version behind API version | `brew upgrade daytonaio/cli/daytona` |
| `[WARN] api_base uses 'localhost'` | Sandbox VMs can't reach localhost | Use a tunnel URL with `--api-base` |
| `[WARN] Could not locate litellm backup JSON` | Harbor installed in unexpected location | Context window still works via 1M fallback; file a GitHub issue |
| Score 0.000 on all tasks | Ollama not responding via tunnel | Test: `curl https://<tunnel-url>/api/tags` |
| Tunnel URL unreachable from sandbox | Tunnel session expired mid-run | Restart the tunnel; re-run the benchmark |
| `CERTIFICATE_VERIFY_FAILED` | Old bug in preflight (now fixed) | Update to latest `wolfbench-ollama.py` |
