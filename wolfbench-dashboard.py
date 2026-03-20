# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "wandb",
#     "weave",
# ]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import json
    import subprocess
    import webbrowser
    from pathlib import Path
    from datetime import date, datetime

    return Path, date, datetime, json, mo, subprocess, webbrowser


@app.cell
def _(mo):
    mo.Html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700;800&family=Source+Serif+4:wght@600;700;800&display=swap');
    body, .marimo { font-family: 'Source Sans 3', -apple-system, sans-serif !important; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Source Serif 4', Georgia, serif !important; }
    .wb-subtitle {
        font-family: 'Source Sans 3', sans-serif;
        color: #9BA1A6;
        font-size: 1rem;
        font-weight: 500;
    }
    </style>
    <div style="display:flex; align-items:center; justify-content:center; gap:16px; margin-bottom:12px;">
        <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 32.3C0 38 4.6 42.6 10.3 42.6C16 42.6 20.7 38 20.7 32.3C20.7 26.6 16 22 10.3 22C4.6 22 0 26.6 0 32.3Z" fill="#FFCC33"/>
            <path d="M0 84C0 89.7 4.6 94.3 10.3 94.3C16 94.3 20.7 89.7 20.7 84C20.7 78.3 16 73.6 10.3 73.6C4.6 73.6 0 78.3 0 84Z" fill="#FFCC33"/>
            <path d="M3.9 58.1C3.9 61.7 6.8 64.6 10.3 64.6C13.9 64.6 16.8 61.7 16.8 58.1C16.8 54.6 13.9 51.7 10.3 51.7C6.8 51.7 3.9 54.6 3.9 58.1Z" fill="#FFCC33"/>
            <path d="M3.9 6.5C3.9 10 6.8 12.9 10.3 12.9C13.9 12.9 16.8 10 16.8 6.5C16.8 2.9 13.9 0 10.3 0C6.8 0 3.9 2.9 3.9 6.5Z" fill="#FFCC33"/>
            <path d="M39.7 67.7C39.7 73.4 44.3 78 50 78C55.7 78 60.3 73.4 60.3 67.7C60.3 62 55.7 57.4 50 57.4C44.3 57.4 39.7 62 39.7 67.7Z" fill="#FFCC33"/>
            <path d="M43.5 93.5C43.5 97.1 46.4 100 50 100C53.6 100 56.5 97.1 56.5 93.5C56.5 90 53.6 87.1 50 87.1C46.4 87.1 43.5 90 43.5 93.5Z" fill="#FFCC33"/>
            <path d="M43.5 41.9C43.5 45.4 46.4 48.3 50 48.3C53.6 48.3 56.5 45.4 56.5 41.9C56.5 38.3 53.6 35.4 50 35.4C46.4 35.4 43.5 38.3 43.5 41.9Z" fill="#FFCC33"/>
            <path d="M43.5 16C43.5 19.6 46.4 22.5 50 22.5C53.6 22.5 56.5 19.6 56.5 16C56.5 12.5 53.6 9.6 50 9.6C46.4 9.6 43.5 12.5 43.5 16Z" fill="#FFCC33"/>
            <path d="M79.3 32.3C79.3 38 84 42.6 89.7 42.6C95.4 42.6 100 38 100 32.3C100 26.6 95.4 22 89.7 22C84 22 79.3 26.6 79.3 32.3Z" fill="#FFCC33"/>
            <path d="M83.2 6.5C83.2 10 86.1 12.9 89.7 12.9C93.2 12.9 96.1 10 96.1 6.5C96.1 2.9 93.2 0 89.7 0C86.1 0 83.2 2.9 83.2 6.5Z" fill="#FFCC33"/>
            <path d="M83.2 58.1C83.2 61.7 86.1 64.6 89.7 64.6C93.2 64.6 96.1 61.7 96.1 58.1C96.1 54.6 93.2 51.7 89.7 51.7C86.1 51.7 83.2 54.6 83.2 58.1Z" fill="#FFCC33"/>
            <path d="M83.2 84C83.2 87.5 86.1 90.4 89.7 90.4C93.2 90.4 96.1 87.5 96.1 84C96.1 80.4 93.2 77.5 89.7 77.5C86.1 77.5 83.2 80.4 83.2 84Z" fill="#FFCC33"/>
        </svg>
        <div style="text-align:center;">
            <svg width="420" height="40" viewBox="0 0 420 40" xmlns="http://www.w3.org/2000/svg">
                <text x="210" y="32" text-anchor="middle" font-family="'Source Serif 4',Georgia,serif" font-size="34" font-weight="800" letter-spacing="-0.5" fill="#FFCC33">WolfBench Dashboard</text>
            </svg>
            <div class="wb-subtitle">Scan VMs, review runs, curate results, generate charts.</div>
        </div>
    </div>
    """)
    return


@app.cell
def _(mo):
    import os as _os

    weave_api_key = mo.ui.text(
        value=_os.environ.get("WANDB_API_KEY", ""),
        label="W&B API Key",
        kind="password",
        full_width=True,
    )
    weave_project = mo.ui.text(
        value=_os.environ.get("WANDB_PROJECT", "wolfbench"),
        label="Weave Project",
        full_width=True,
    )
    weave_entity = mo.ui.text(
        value=_os.environ.get("WANDB_ENTITY", ""),
        label="W&B Entity",
        full_width=True,
    )
    upload_target = mo.ui.text(
        value=_os.environ.get("UPLOAD_TARGET", ""),
        label="Upload target (user@server:path)",
        full_width=True,
    )

    mo.vstack([
        mo.md("### Configuration"),
        mo.hstack([weave_project, weave_entity], widths=[1, 1]),
        mo.hstack([weave_api_key, upload_target], widths=[1, 1]),
        mo.md(
            '<span style="color:#9BA1A6;font-size:0.85rem;">'
            "Fields pre-filled from WANDB_API_KEY / WANDB_PROJECT / WANDB_ENTITY / UPLOAD_TARGET env vars. "
            "Entity = W&B team/org namespace (leave empty for default account)."
            "</span>"
        ),
    ])
    return upload_target, weave_api_key, weave_entity, weave_project


@app.cell
def _(Path):
    import sys as _sys
    import importlib as _importlib

    _script_dir = str(Path(__file__).parent)
    if _script_dir not in _sys.path:
        _sys.path.insert(0, _script_dir)

    hcr = _importlib.import_module("wolfbench_collect")
    _importlib.reload(hcr)
    LOCAL_RUNS_DIR = Path(__file__).parent / "wolfbench-runs"
    OVERRIDES_FILE = Path(__file__).parent / "wolfbench-overrides.json"
    None
    return LOCAL_RUNS_DIR, OVERRIDES_FILE, hcr


@app.cell
def _(mo):
    discover_all_button = mo.ui.run_button(label="Discover all VMs")
    discover_exe_button = mo.ui.run_button(label="Discover VMs from exe.dev")
    discover_hz_button = mo.ui.run_button(label="Discover VMs from Hetzner")
    mo.vstack([
        mo.md("### Step 1: Select VMs"),
        mo.hstack(
            [discover_all_button, discover_exe_button, discover_hz_button],
            justify="start", gap=1,
        ),
    ])
    return discover_all_button, discover_exe_button, discover_hz_button


@app.cell
def _(mo):
    get_exe_vms, set_exe_vms = mo.state([])
    get_hz_vms, set_hz_vms = mo.state([])
    # Track download/upload completion: "" = not done, "meta" / "full" for downloads
    get_dl_done, set_dl_done = mo.state("")
    get_dl_msg, set_dl_msg = mo.state(None)  # Persisted download status message
    get_upload_done, set_upload_done = mo.state(False)
    get_upload_msg, set_upload_msg = mo.state(None)  # Persisted upload status message
    return (
        get_dl_done, get_dl_msg, get_exe_vms, get_hz_vms, get_upload_done, get_upload_msg,
        set_dl_done, set_dl_msg, set_exe_vms, set_hz_vms, set_upload_done, set_upload_msg,
    )


@app.cell
def _(discover_all_button, discover_exe_button, hcr, mo, set_exe_vms):
    if discover_exe_button.value or discover_all_button.value:
        with mo.status.spinner("Discovering VMs from exe.dev..."):
            _raw = hcr.discover_vms()
        _vms = [{"name": v.replace(".exe.xyz", ""), "ssh": v, "source": "exe.dev"} for v in _raw]
        set_exe_vms(_vms)
    return


@app.cell
def _(discover_all_button, discover_hz_button, hcr, mo, set_hz_vms):
    if discover_hz_button.value or discover_all_button.value:
        with mo.status.spinner("Discovering VMs from Hetzner..."):
            _raw = hcr.discover_hetzner_vms()
        _vms = [
            {
                "name": v["name"] if v["status"] == "running" else f"{v['name']} ({v['status']})",
                "ssh": f"root@{v['ip']}",
                "source": "hetzner",
            }
            for v in _raw
        ]
        set_hz_vms(_vms)
    return


@app.cell
def _(get_exe_vms, get_hz_vms, mo):
    _exe = get_exe_vms()
    _hz = get_hz_vms()
    _seen = set()
    all_vms = []
    for vm in _exe + _hz:
        if vm["ssh"] not in _seen:
            _seen.add(vm["ssh"])
            all_vms.append(vm)
    _parts = []
    if _exe:
        _parts.append(f"**{len(_exe)}** from exe.dev")
    if _hz:
        _parts.append(f"**{len(_hz)}** from Hetzner")
    if _parts:
        _msg = mo.callout(mo.md(f"Discovered: {', '.join(_parts)}"), kind="success")
    else:
        _msg = mo.callout(mo.md("Click a **Discover** button to find VMs."), kind="info")
    _msg
    return (all_vms,)


@app.cell
def _(all_vms, mo):
    if all_vms:
        vm_rows = [{"name": vm["name"], "source": vm["source"]} for vm in all_vms]
        vm_filter = mo.ui.text(
            value="harbor*",
            label="Preselect filter (glob on name, * = wildcard):",
            full_width=True,
        )
        vm_filter_apply = mo.ui.run_button(label="Apply")
        _ui = mo.hstack([vm_filter, vm_filter_apply], widths=[1, 0], align="end")
    else:
        vm_rows = []
        vm_filter = None
        vm_filter_apply = None
        _ui = mo.md("")
    _ui
    return vm_filter, vm_filter_apply, vm_rows


@app.cell
def _(mo, vm_filter, vm_filter_apply, vm_rows):
    from fnmatch import fnmatch
    _ = vm_filter_apply  # reactive dependency: Apply button triggers re-eval
    if vm_rows:
        # Compute filtered indices from glob pattern (case-insensitive)
        _pattern = vm_filter.value if vm_filter is not None else "harbor-evals-*"
        filtered_indices = []
        if _pattern:
            _pat = _pattern.lower()
            for _i, _row in enumerate(vm_rows):
                if fnmatch(_row["name"].lower(), _pat):
                    filtered_indices.append(_i)

        vm_preset = mo.ui.radio(
            options={
                "Select All": "all",
                "Deselect All": "none",
                "Reselect Filtered": "filtered",
            },
            value="Reselect Filtered",
            inline=True,
        )
        _ui = mo.hstack(
            [mo.md("**Selection preset:**"), vm_preset],
            justify="start",
            gap=1,
        )
    else:
        filtered_indices = []
        vm_preset = None
        _ui = mo.md("")
    _ui
    return filtered_indices, vm_preset


@app.cell
def _(filtered_indices, mo, vm_preset, vm_rows):
    if vm_rows:
        if vm_preset is not None and vm_preset.value == "all":
            _init = list(range(len(vm_rows)))
        elif vm_preset is not None and vm_preset.value == "none":
            _init = []
        else:
            _init = filtered_indices
        vm_table = mo.ui.table(
            data=vm_rows,
            selection="multi",
            initial_selection=_init,
            page_size=30,
            label="Selected VMs will be scanned",
        )
    else:
        vm_table = None
    vm_table if vm_table is not None else mo.md("")
    return (vm_table,)


@app.cell
def _(all_vms, mo, vm_table):
    if vm_table is not None and vm_table.value:
        _lookup = {vm["name"]: vm["ssh"] for vm in all_vms}
        selected_vms = [_lookup[row["name"]] for row in vm_table.value]
    else:
        selected_vms = []
    _label = (
        f"Scan (local + {len(selected_vms)} VMs)"
        if selected_vms
        else "Scan Local Only"
    )
    scan_button = mo.ui.run_button(label=_label)
    mo.hstack(
        [mo.md(f"**{len(selected_vms)}** VMs selected"), scan_button],
        justify="start",
        gap=1,
    )
    return scan_button, selected_vms


@app.cell
def _(LOCAL_RUNS_DIR, hcr, mo, scan_button, selected_vms):
    if scan_button.value:
        _parts_label = ["local"]
        if selected_vms:
            _parts_label.append(f"{len(selected_vms)} VMs")
        with mo.status.spinner(f"Scanning {' + '.join(_parts_label)}..."):
            # LOCAL FIRST — dedup keeps first occurrence, so local wins
            _local = hcr.collect_local(LOCAL_RUNS_DIR)
            _vm = hcr.collect_all(selected_vms, max_workers=8) if selected_vms else []
            raw_results = hcr.deduplicate(_local + _vm)
        scan_completed = True
        _n_local = len(_local)
        _n_vm = len(_vm)
        _n_deduped = _n_local + _n_vm - len(raw_results)
        _breakdown = []
        if _n_local:
            _breakdown.append(f"{_n_local} local")
        if _n_vm:
            _breakdown.append(f"{_n_vm} from VMs")
        if _n_deduped:
            _breakdown.append(f"{_n_deduped} deduped")
        _detail = f" ({', '.join(_breakdown)})" if _breakdown else ""
        _msg = mo.callout(
            mo.md(f"Collected **{len(raw_results)}** unique runs{_detail}"),
            kind="success",
        )
    else:
        raw_results = []
        scan_completed = False
        _msg = mo.md("")
    _msg
    return raw_results, scan_completed


@app.cell
def _(all_vms, hcr, mo, raw_results, scan_completed):
    if scan_completed and raw_results:
        _vm_name_lookup = {vm["ssh"]: vm["name"] for vm in all_vms} if all_vms else {}
        _vm_source_lookup = {vm["ssh"]: vm["source"] for vm in all_vms} if all_vms else {}
        all_table_rows = []

        def _fmt_tokens(n):
            if not n: return "-"
            if n >= 1_000_000: return f"{n / 1_000_000:.1f}M"
            if n >= 1_000: return f"{n / 1_000:.0f}K"
            return str(n)

        for _idx, _run in enumerate(raw_results):
            _reason = hcr.classify_run(_run)
            _ts = _run.get("timestamp", "")
            _date = _ts[:10] if _ts else "?"
            # timestamp format: "2026-03-01__13-43-12" → time "13:43"
            _time = _ts[12:17].replace("-", ":") if len(_ts) >= 17 else "?"
            _score_str = (
                f'{_run["score"]:.1%}' if _run.get("score") is not None else "?"
            )
            _dur = ""
            if _run.get("duration_sec"):
                _h, _rem = divmod(int(_run["duration_sec"]), 3600)
                _m, _ = divmod(_rem, 60)
                _dur = f"{_h}h{_m:02d}m"

            # Split model: provider/vendor/model or provider/model
            _model_full = _run.get("model", "unknown")
            _model_parts = _model_full.split("/")
            if len(_model_parts) >= 3:
                _provider = _model_parts[0]
                _vendor = _model_parts[1]
                _model_name = "/".join(_model_parts[2:])
            elif len(_model_parts) == 2:
                _provider = _model_parts[0]
                _vendor = _model_parts[0]
                _model_name = _model_parts[1]
            else:
                _provider = "-"
                _vendor = "-"
                _model_name = _model_full

            # Thinking: True/False → on/off, None → -
            _t = _run.get("thinking")
            if _t is None:
                _thinking = "-"
            elif _t is True or _t == "enabled":
                _thinking = "on"
            elif _t is False or _t == "disabled":
                _thinking = "off"
            else:
                _thinking = str(_t)

            # Timeout display
            _timeout = _run.get("timeout_sec")
            _timeout_str = f"{int(_timeout)}s" if _timeout is not None else "-"

            # Concurrency
            _n_conc = _run.get("concurrency")
            _n_str = str(_n_conc) if _n_conc is not None else "-"

            # AgentTimeoutError = legitimate (agent ran out of time)
            _error_breakdown = _run.get("error_breakdown", {})
            _agent_timeouts = _error_breakdown.get("AgentTimeoutError", 0)

            # Tasks permanently lost = no final pass/fail verdict
            # (Harbor retries errors, so n_errors overcounts — use actual loss)
            _n_passed = _run.get("n_passed", 0)
            _n_failed = _run.get("n_failed", 0)
            _n_trials = _run.get("n_trials", 0)
            _lost = max(0, _n_trials - _n_passed - _n_failed)

            # Build infra error summary for _classify (diagnostic detail)
            _infra_parts = [
                f"{v} {k}" for k, v in _error_breakdown.items()
                if k != "AgentTimeoutError"
            ]
            _infra_summary = ", ".join(_infra_parts) if _infra_parts else None

            # Token metrics
            _tok_in = _run.get("tokens_in")
            _tok_out = _run.get("tokens_out")
            _tok_cache = _run.get("tokens_cache")
            _cost = _run.get("cost_usd")

            # Total prompt = uncached input + cached input
            _tok_prompt = None
            if _tok_in is not None or _tok_cache is not None:
                _tok_prompt = (_tok_in or 0) + (_tok_cache or 0)

            # % cached = cache / total_prompt
            _cached_pct = "-"
            if _tok_prompt and _tok_cache:
                _cached_pct = f"{_tok_cache / _tok_prompt:.0%}"

            # Jobs folder: immediate parent of the timestamp dir in run_dir
            _run_dir = _run.get("run_dir", "")
            _jobs_folder = _run_dir.split("/")[-2] if "/" in _run_dir else "-"

            _vm_val = _run.get("vm", "?")

            all_table_rows.append({
                "idx": _idx,
                "date": _date,
                "time": _time,
                "source": "local" if _vm_val == "local" else _vm_source_lookup.get(_vm_val, "?"),
                "vm": "local" if _vm_val == "local" else _vm_name_lookup.get(_vm_val, _vm_val),
                "job": _jobs_folder,
                "agent": _run.get("agent", "?"),
                "version": _run.get("agent_version") or "-",
                "provider": _provider,
                "vendor": _vendor,
                "model": _model_name,
                "model_display": _run.get("model_display") or "",
                "thinking": _thinking,
                "thinking_display": _run.get("thinking_display") or "",
                "score": _score_str,
                "pass": _run.get("n_passed", 0),
                "fail": _run.get("n_failed", 0),
                "tasks": _run.get("n_trials", 0),
                "timeout": _timeout_str,
                "timeouts": _agent_timeouts,
                "errors": _lost,
                "duration": _dur,
                "n": _n_str,
                "uncached_in": _fmt_tokens(_tok_in),
                "cached_in": _fmt_tokens(_tok_cache),
                "total_in": _fmt_tokens(_tok_prompt),
                "cached%": _cached_pct,
                "out": _fmt_tokens(_tok_out),
                "cost": f"${_cost:.2f}" if _cost else "-",
                "_classify": _reason,  # only classify_run (partial/test/total failure)
                "_infra_detail": _infra_summary or "",  # for enriching fail reasons
                "status": "",  # computed later by filter cell
            })

        # Sort by date+time descending (newest first)
        all_table_rows.sort(key=lambda r: (r["date"], r["time"]), reverse=True)

        _msg = mo.callout(
            mo.md(
                f"### Step 2: Review & Select Runs\n\n"
                f"**{len(all_table_rows)}** runs collected. "
                f"Use filters and valid condition below to curate."
            ),
            kind="info",
        )
    else:
        all_table_rows = []
        _msg = mo.md("")

    _msg
    return (all_table_rows,)


@app.cell
def _(all_table_rows, mo, scan_completed):
    if scan_completed and all_table_rows:
        row_filter = mo.ui.text(
            value="",
            label="Row filter (col=val, comma-separated — same col = OR):",
            full_width=True,
        )
        row_filter_apply = mo.ui.run_button(label="Apply")
        valid_condition = mo.ui.text(
            value="agent!=cline-cli,score!=0.0%,tasks=89,timeout=*s,errors<10",
            label="Valid condition (col op val, comma-separated — same col = OR):",
            full_width=True,
        )
        valid_condition_apply = mo.ui.run_button(label="Apply")
        _ui = mo.vstack([
            mo.hstack([row_filter, row_filter_apply], widths=[1, 0], align="end"),
            mo.hstack([valid_condition, valid_condition_apply], widths=[1, 0], align="end"),
        ])
    else:
        row_filter = None
        row_filter_apply = None
        valid_condition = None
        valid_condition_apply = None
        _ui = mo.md("")
    _ui
    return row_filter, row_filter_apply, valid_condition, valid_condition_apply


@app.cell
def _(all_table_rows, mo, row_filter, row_filter_apply, scan_completed,
      valid_condition, valid_condition_apply):
    _rf = row_filter_apply  # reactive dependency
    _vc = valid_condition_apply  # reactive dependency

    filtered_table_rows = []
    valid_indices = []

    if scan_completed and all_table_rows:
        # Parse expressions: supports =, !=, <=, >=, <, >
        # Order matters: check two-char ops before single-char
        _OPS = ["<=", ">=", "!=", "<", ">", "="]

        def _parse_exprs(_text):
            _rules = []
            if not _text or not _text.strip():
                return _rules
            for _expr in _text.split(","):
                _expr = _expr.strip()
                if not _expr:
                    continue
                for _op in _OPS:
                    if _op in _expr:
                        _col, _val = _expr.split(_op, 1)
                        # Normalize "=" to "==" internally
                        _op_norm = "==" if _op == "=" else _op
                        _rules.append((_col.strip(), _op_norm, _val.strip()))
                        break
            return _rules

        _filter_text = row_filter.value if row_filter is not None and row_filter.value else ""
        _filters = _parse_exprs(_filter_text)

        _valid_text = (
            valid_condition.value if valid_condition is not None and valid_condition.value
            else ""
        )
        _valid_rules = _parse_exprs(_valid_text)

        def _eval_rule(_col, _cell, _op, _val):
            """Evaluate a single rule. Returns True if the rule passes.
            Supports wildcards (*) for ==/!= and numeric comparisons.
            All string matching is case-insensitive.
            """
            from fnmatch import fnmatch

            # Status shorthand
            if _col == "status":
                _cl = _cell.lower()
                _vl = _val.lower()
                if _vl in ("valid", "✅ valid"):
                    return _cl.startswith("✅") if _op == "==" else not _cl.startswith("✅")
                if _vl in ("invalid", "excluded", "❌"):
                    return _cl.startswith("❌") if _op == "==" else not _cl.startswith("❌")

            # Numeric comparison for <, >, <=, >=
            if _op in ("<", ">", "<=", ">="):
                try:
                    # Strip non-numeric suffixes (e.g. "7200s" → 7200)
                    _cn = float("".join(c for c in _cell if c in "0123456789.-"))
                    _vn = float("".join(c for c in _val if c in "0123456789.-"))
                    if _op == "<": return _cn < _vn
                    if _op == ">": return _cn > _vn
                    if _op == "<=": return _cn <= _vn
                    if _op == ">=": return _cn >= _vn
                except (ValueError, TypeError):
                    return False

            # Equality / inequality: case-insensitive, with wildcard glob
            _cl = _cell.lower()
            _vl = _val.lower()
            if "*" in _vl:
                _m = fnmatch(_cl, _vl)
            else:
                _m = _cl == _vl
            if _op == "==":
                return _m
            if _op == "!=":
                return not _m
            return False

        # Group rules by column: same-column rules use OR, cross-column uses AND
        from collections import defaultdict

        _grouped_f = defaultdict(list)
        for _col, _op, _val in _filters:
            _grouped_f[_col].append((_op, _val))

        _grouped_v = defaultdict(list)
        for _col, _op, _val in _valid_rules:
            _grouped_v[_col].append((_op, _val))

        # Apply row filter and recompute status based on valid condition
        for _row in all_table_rows:
            # Check row filter (OR within same column, AND across columns)
            _keep = True
            for _col, _col_rules in _grouped_f.items():
                _cell = str(_row.get(_col, ""))
                if not any(_eval_rule(_col, _cell, _op, _val) for _op, _val in _col_rules):
                    _keep = False
                    break
            if not _keep:
                continue

            # Determine validity: classify_run reason + valid condition rules
            _classify_reason = _row.get("_classify")
            if _classify_reason is not None:
                # Auto-classified as excluded (sample, partial, failure)
                _row["status"] = f"❌ {_classify_reason}"
                _is_valid = False
            else:
                # Check user-defined valid condition rules
                _is_valid = True
                _fail_reason = None
                if _grouped_v:
                    for _col, _col_rules in _grouped_v.items():
                        _cell = str(_row.get(_col, ""))
                        if not any(_eval_rule(_col, _cell, _op, _val) for _op, _val in _col_rules):
                            _is_valid = False
                            _detail = _row.get("_infra_detail", "")
                            _fail_reason = (
                                f"{_col}={_cell} ({_detail})"
                                if _col == "errors" and _detail
                                else f"{_col}={_cell}"
                            )
                            break
                if _is_valid:
                    _row["status"] = "✅ VALID"
                else:
                    _row["status"] = f"❌ {_fail_reason}"

            filtered_table_rows.append(_row)
            if _is_valid:
                valid_indices.append(len(filtered_table_rows) - 1)

        _n_excl = len(filtered_table_rows) - len(valid_indices)
        _n_hidden = len(all_table_rows) - len(filtered_table_rows)
        _parts = [
            f"**{len(valid_indices)}** valid",
            f"**{_n_excl}** excluded",
        ]
        if _n_hidden:
            _parts.append(f"**{_n_hidden}** hidden by filter")
        _msg = mo.md(" · ".join(_parts))
    else:
        _msg = mo.md("")

    _msg
    return filtered_table_rows, valid_indices


@app.cell
def _(filtered_table_rows, mo, scan_completed):
    if scan_completed and filtered_table_rows:
        selection_preset = mo.ui.radio(
            options={
                "Select All": "all",
                "Deselect All": "none",
                "Reselect Valid": "valid",
            },
            value="Reselect Valid",
            inline=True,
        )
        _preset_ui = mo.hstack(
            [mo.md("**Selection preset:**"), selection_preset],
            justify="start",
            gap=1,
        )
    else:
        selection_preset = None
        _preset_ui = mo.md("")
    _preset_ui
    return (selection_preset,)


@app.cell
def _(filtered_table_rows, mo, scan_completed, selection_preset, valid_indices):
    if scan_completed and filtered_table_rows:
        if selection_preset is not None and selection_preset.value == "all":
            _init = list(range(len(filtered_table_rows)))
        elif selection_preset is not None and selection_preset.value == "none":
            _init = []
        else:
            _init = valid_indices
        results_table = mo.ui.table(
            data=filtered_table_rows,
            selection="multi",
            initial_selection=_init,
            page_size=100,
            label="Selected = valid, unselected = excluded",
        )
    else:
        results_table = None
    results_table if results_table is not None else mo.md("")
    return (results_table,)


@app.cell
def _(hcr, mo, raw_results, results_table, scan_completed):
    if scan_completed and results_table is not None and results_table.value:
        _selected_indices = {row["idx"] for row in results_table.value}
        selected_runs = [
            raw_results[i]
            for i in range(len(raw_results))
            if i in _selected_indices
        ]
        final_excluded = [
            {**raw_results[i], "exclude_reason": hcr.classify_run(raw_results[i]) or "manually excluded"}
            for i in range(len(raw_results))
            if i not in _selected_indices
        ]
        _msg = mo.md(
            f"**Selection:** {len(selected_runs)} valid, "
            f"{len(final_excluded)} excluded"
        )
    else:
        selected_runs = []
        final_excluded = []
        _msg = mo.md("")
    _msg
    return final_excluded, selected_runs


@app.cell
def _(OVERRIDES_FILE, json, mo):
    _initial = {}
    if OVERRIDES_FILE.exists():
        try:
            _initial = json.loads(OVERRIDES_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    get_overrides, set_overrides = mo.state(_initial)
    return get_overrides, set_overrides


@app.cell
def _(get_overrides, mo, selected_runs):
    # Build one row per unique (job, agent, version, model, thinking).
    # Two editable fields: model display + thinking display.
    display_name_inputs = {}
    thinking_inputs = {}

    def _norm_thinking(t):
        if t is None: return "-"
        if t is True or t == "enabled": return "on"
        if t is False or t == "disabled": return "off"
        return str(t)

    _stored = get_overrides()
    if selected_runs:
        _seen = {}
        for _r in selected_runs:
            _agent = _r.get("agent", "?")
            _model = _r.get("model", "unknown")
            _version = _r.get("agent_version") or "-"
            _thinking = _norm_thinking(_r.get("thinking"))
            _run_dir = _r.get("run_dir", "")
            _job = _run_dir.split("/")[-2] if "/" in _run_dir else "-"
            _key = f"{_job}|{_agent}|{_version}|{_model}|{_thinking}"
            if _key not in _seen:
                _se = _stored.get(_key, {})
                _existing_model = _se.get("model_display", "")
                _existing_thinking = _se.get("thinking_display", "")
                _short = _model.split("/")[-1] if "/" in _model else _model
                _parts = _model.split("/")
                _provider = _parts[0] if len(_parts) >= 2 else "-"
                _vendor = _parts[1] if len(_parts) >= 3 else _provider
                _seen[_key] = {
                    "job": _job, "agent": _agent, "model": _short,
                    "existing_model": _existing_model,
                    "existing_thinking": _existing_thinking,
                    "provider": _provider, "vendor": _vendor,
                    "version": _version, "thinking": _thinking,
                }
        # Header row
        _header = mo.hstack([
            mo.md("**job**"),
            mo.md("**agent**"),
            mo.md("**version**"),
            mo.md("**provider**"),
            mo.md("**vendor**"),
            mo.md("**model display**"),
            mo.md("**thinking**"),
        ], widths=[1.2, 1, 1, 1, 1, 2, 1], gap=0.5)
        _rows = [_header]
        for _key, _info in sorted(_seen.items()):
            _model_input = mo.ui.text(
                value=_info["existing_model"],
                placeholder=_info["model"],
                full_width=True,
            )
            _thinking_input = mo.ui.text(
                value=_info["existing_thinking"],
                placeholder=_info["thinking"],
                full_width=True,
            )
            display_name_inputs[_key] = _model_input
            thinking_inputs[_key] = _thinking_input
            _rows.append(
                mo.hstack([
                    mo.md(_info["job"]),
                    mo.md(_info["agent"]),
                    mo.md(_info["version"]),
                    mo.md(_info["provider"]),
                    mo.md(_info["vendor"]),
                    _model_input,
                    _thinking_input,
                ], widths=[1.2, 1, 1, 1, 1, 2, 1], gap=0.5, align="center")
            )
        _apply_btn = mo.ui.run_button(label="Apply Overrides")
        _output = mo.vstack([
            mo.md("### Edit Display Names"),
            mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Leave empty to use auto-detected values. Click Apply after editing.</span>'),
            *_rows,
            _apply_btn,
        ])
        apply_names_btn = _apply_btn
    else:
        apply_names_btn = None
        thinking_inputs = {}
        _output = mo.md("")
    _output
    return apply_names_btn, display_name_inputs, thinking_inputs


@app.cell
def _(OVERRIDES_FILE, apply_names_btn, display_name_inputs, json, set_overrides, thinking_inputs):
    # Collect widget values on Apply and merge into persistent session store.
    # Also writes to overrides.json for cross-session persistence (survives reload).
    # Uses set_overrides (NOT get_overrides) to avoid reactive cycle;
    # reads existing overrides from file instead of state for the merge.
    if (
        apply_names_btn is not None
        and apply_names_btn.value
        and display_name_inputs
    ):
        _new = {}
        for _key in display_name_inputs:
            _md = display_name_inputs[_key].value.strip()
            _td = thinking_inputs[_key].value.strip() if _key in thinking_inputs else ""
            _entry = {}
            if _md:
                _entry["model_display"] = _md
            if _td:
                _entry["thinking_display"] = _td
            if _entry:
                _new[_key] = _entry
        # Merge with existing file (reads file, not mo.state, to avoid cycle)
        _existing = {}
        if OVERRIDES_FILE.exists():
            try:
                _existing = json.loads(OVERRIDES_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        _merged = {**_existing, **_new}
        # Remove keys that were explicitly cleared (visible but empty)
        for _key in display_name_inputs:
            if _key not in _new and _key in _merged:
                del _merged[_key]
        if _merged:
            OVERRIDES_FILE.write_text(json.dumps(_merged, indent=2) + "\n")
        elif OVERRIDES_FILE.exists():
            OVERRIDES_FILE.unlink()
        # Update session state
        set_overrides(lambda _old: {**{k: v for k, v in _old.items() if k not in display_name_inputs}, **_new})
    return ()


@app.cell
def _(get_overrides, selected_runs):
    # Apply stored overrides to selected_runs. Runs on every change to
    # the override store or selection — overrides survive filter changes.

    def _norm_thinking(t):
        if t is None: return "-"
        if t is True or t == "enabled": return "on"
        if t is False or t == "disabled": return "off"
        return str(t)

    _stored = get_overrides()
    final_valid = []
    if selected_runs:
        for _r in selected_runs:
            _rd = _r.get("run_dir", "")
            _job = _rd.split("/")[-2] if "/" in _rd else "-"
            _key = (
                f"{_job}|{_r.get('agent', '?')}|{_r.get('agent_version') or '-'}"
                f"|{_r.get('model', 'unknown')}|{_norm_thinking(_r.get('thinking'))}"
            )
            if _key in _stored:
                _s = _stored[_key]
                _patch = {
                    "model_display": _s.get("model_display", ""),
                    "thinking_display": _s.get("thinking_display", ""),
                }
            else:
                # No active override — clear any stale display values
                # that were previously baked into config.json
                _patch = {"model_display": "", "thinking_display": ""}
            final_valid.append({**_r, **_patch})
    return (final_valid,)


@app.cell
def _(LOCAL_RUNS_DIR, Path, final_valid, get_dl_done, json, mo):
    _dl_done = get_dl_done()
    _vm_only = [r for r in final_valid if r.get("vm") != "local"]
    # Local runs without trajectories — can upgrade via Full download,
    # but only if a full download wasn't already attempted (source has none).
    _needs_traj = []
    for _r in final_valid:
        if _r.get("vm") != "local":
            continue
        if any(Path(_r["run_dir"]).glob("**/agent/trajectory.json")):
            continue
        # Check if we already tried a full download — source simply has no trajectories
        _mp = Path(_r["run_dir"]) / "_meta.json"
        if _mp.exists():
            try:
                _m = json.loads(_mp.read_text())
                if _m.get("download_mode") == "full":
                    continue  # Already tried full download, nothing to get
            except (json.JSONDecodeError, OSError):
                pass
        _needs_traj.append(_r)
    _n_meta = len(_vm_only)
    _n_full = len(_vm_only) + len(_needs_traj)
    # Disable based on completion state: full covers meta
    _meta_disabled = _n_meta == 0 or _dl_done in ("meta", "full")
    _full_disabled = _n_full == 0 or _dl_done == "full"
    download_meta_btn = mo.ui.run_button(
        label=(
            f"Download Metadata — done ✓" if _dl_done in ("meta", "full")
            else f"Download Metadata ({_n_meta} runs)"
        ),
        disabled=_meta_disabled,
    )
    download_full_btn = mo.ui.run_button(
        label=(
            f"Download Full + Trajectories — done ✓" if _dl_done == "full"
            else f"Download Full + Trajectories ({_n_full} runs)"
        ),
        disabled=_full_disabled,
    )
    if len(final_valid) == 0:
        _hint = mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: no runs selected</span>')
    elif _dl_done:
        _hint = mo.md(f'<span style="color:#9BA1A6;font-size:0.85rem;">Download complete ({_dl_done}). Re-scan to reset.</span>')
    elif _n_full == 0 and _n_meta == 0:
        _hint = mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: all runs already local (with trajectories)</span>')
    else:
        _parts = []
        if _needs_traj:
            _parts.append(f"{len(_needs_traj)} local run(s) missing trajectories")
        _parts.append(
            "Metadata = result.json + config.json (~fast). "
            "Full = includes trajectory.json files (~slow, needed for Weave trace upload)."
        )
        _hint = mo.md(f'<span style="color:#9BA1A6;font-size:0.85rem;">{" · ".join(_parts)}</span>')
    mo.vstack([
        mo.md(f"### Step 3: Download to Local Storage\n\n`{LOCAL_RUNS_DIR}`"),
        mo.hstack([download_meta_btn, download_full_btn], justify="start", gap=1),
        _hint,
    ])
    return download_full_btn, download_meta_btn


@app.cell
def _(LOCAL_RUNS_DIR, Path, download_full_btn, download_meta_btn, final_valid, hcr, json, mo, set_dl_done, set_dl_msg):
    _do_meta = download_meta_btn.value
    _do_full = download_full_btn.value

    if (_do_meta or _do_full) and final_valid:
        _vm_only = [r for r in final_valid if r.get("vm") != "local"]

        # For Full downloads, also include local runs missing trajectories
        _to_download = list(_vm_only)
        if _do_full:
            for _r in final_valid:
                if _r.get("vm") != "local":
                    continue
                if any(Path(_r["run_dir"]).glob("**/agent/trajectory.json")):
                    continue
                _meta_path = Path(_r["run_dir"]) / "_meta.json"
                if not _meta_path.exists():
                    continue
                try:
                    _meta = json.loads(_meta_path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                # Skip if we already tried a full download — source has no trajectories
                if _meta.get("download_mode") == "full":
                    continue
                _src_vm = _meta.get("source_vm")
                _src_dir = _meta.get("source_run_dir")
                if _src_vm and _src_dir:
                    _to_download.append({**_r, "vm": _src_vm, "run_dir": _src_dir})

        if _to_download:
            _include_traj = bool(_do_full)
            _mode = "full + trajectories" if _include_traj else "metadata"
            with mo.status.spinner(f"Downloading {len(_to_download)} runs ({_mode})..."):
                _results = hcr.download_runs(
                    _to_download,
                    LOCAL_RUNS_DIR,
                    include_trajectories=_include_traj,
                    max_workers=4,
                )
            _ok = sum(1 for r in _results if r["status"] == "ok")
            _skip = sum(1 for r in _results if r["status"] == "skipped")
            _err = sum(1 for r in _results if r["status"] == "error")
            if _err == 0:
                set_dl_done("full" if _do_full else "meta")
            set_dl_msg({
                "text": (
                    f"Downloaded **{_ok}**, skipped **{_skip}** (already complete), "
                    f"**{_err}** errors. Re-scan to see local copies in the table."
                ),
                "kind": "success" if _err == 0 else "warn",
            })
        else:
            set_dl_msg({
                "text": "Nothing to download — no source VMs available for trajectory retrieval.",
                "kind": "info",
            })
    return


@app.cell
def _(get_dl_msg, mo):
    _msg = get_dl_msg()
    mo.output.replace(_msg and mo.callout(mo.md(_msg["text"]), kind=_msg["kind"]) or mo.md(""))
    return


@app.cell
def _(Path):
    import importlib as _imp
    import sys as _sys

    _sd = str(Path(__file__).parent)
    if _sd not in _sys.path:
        _sys.path.insert(0, _sd)
    ww = _imp.import_module("wolfbench_weave")
    _imp.reload(ww)
    None
    return (ww,)


@app.cell
def _(Path, final_valid, get_upload_done, mo, weave_api_key, weave_project, ww):
    import os as _os

    _has_key = bool(weave_api_key.value.strip() or _os.environ.get("WANDB_API_KEY"))
    _has_runs = len(final_valid) > 0
    _can_upload = _has_key and _has_runs

    # Always-visible status summary from manifest
    _proj = weave_project.value.strip() or "wolfbench"
    _manifest_path = Path(__file__).parent / f"{_proj}-manifest.json"
    _manifest = ww.load_manifest(_manifest_path, project=_proj)
    _evals = _manifest.get("evaluations", {})

    # Count from final_valid (current runs), cross-reference manifest for upload status.
    # This way new scanned/downloaded runs increase the denominator immediately.
    _current_groups = ww.group_runs(final_valid) if _has_runs else {}
    _n_configs = len(_current_groups)
    _total_runs = sum(len(g) for g in _current_groups.values())
    _total_uploaded = 0
    _total_traces = 0
    for _key, _group in _current_groups.items():
        _eval_entry = _evals.get(_key, {})
        _manifest_runs = _eval_entry.get("runs", {})
        for _r in _group:
            _mr = _manifest_runs.get(_r["timestamp"], {})
            if _mr.get("uploaded"):
                _total_uploaded += 1
            if _mr.get("has_traces"):
                _total_traces += 1

    # "Done" = every run in final_valid is uploaded (manifest cross-reference).
    # Uses the same counts as the status line — no separate logic to drift out of sync.
    _all_current_done = _total_runs > 0 and _total_uploaded == _total_runs

    # Button is done if: just clicked upload this session, OR all current runs are uploaded
    _upload_done = get_upload_done() or _all_current_done

    weave_upload_btn = mo.ui.run_button(
        label="Upload to Weave — done ✓" if get_upload_done() else "Upload to Weave",
        disabled=not _can_upload or _upload_done,
    )
    weave_details_btn = mo.ui.run_button(label="Show Details")

    _reasons = []
    if not _has_key:
        _reasons.append("API key not set")
    if not _has_runs:
        _reasons.append("no runs selected")
    _hint = (
        mo.md(f'<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: {", ".join(_reasons)}</span>')
        if _reasons else mo.md("")
    )

    if _total_runs > 0:
        _status_line = mo.md(
            f'<span style="color:#9BA1A6;font-size:0.85rem;">'
            f'{_n_configs} config(s), {_total_uploaded}/{_total_runs} runs uploaded, '
            f'{_total_traces} with traces</span>'
        )
    else:
        _status_line = mo.md(
            '<span style="color:#9BA1A6;font-size:0.85rem;">No uploads yet</span>'
        )

    mo.vstack([
        mo.md("### Step 4: Upload to W&B Weave"),
        mo.hstack(
            [weave_upload_btn, weave_details_btn],
            justify="start",
            gap=1,
        ),
        _hint,
        _status_line,
    ])
    return weave_details_btn, weave_upload_btn


@app.cell
async def _(LOCAL_RUNS_DIR, Path, final_valid, mo, set_upload_done, set_upload_msg, weave_api_key, weave_entity, weave_project, weave_upload_btn, ww):
    import os as _os

    if weave_upload_btn.value and final_valid:
        _key = weave_api_key.value.strip()
        _proj = weave_project.value.strip() or "wolfbench"
        _manifest_path = Path(__file__).parent / f"{_proj}-manifest.json"
        _ent = weave_entity.value.strip() or None
        if _key:
            _os.environ["WANDB_API_KEY"] = _key
        if not _os.environ.get("WANDB_API_KEY"):
            set_upload_msg({
                "text": "**WANDB_API_KEY** is not set. Enter it above or export it before launching.",
                "kind": "warn",
            })
        else:
            try:
                with mo.status.spinner(
                    f"Uploading evaluations + traces to W&B Weave ({_proj})..."
                ):
                    _result = await ww.upload_evaluations(
                        runs=final_valid,
                        project=_proj,
                        entity=_ent,
                        manifest_path=_manifest_path,
                        local_runs_dir=LOCAL_RUNS_DIR,
                    )
                set_upload_done(True)
                set_upload_msg({
                    "text": _result.get("summary", "Done."),
                    "kind": "success",
                })
            except ImportError as _e:
                set_upload_msg({
                    "text": (
                        f"**Missing dependency:** {_e}\n\n"
                        f"Install with: `uv pip install weave wandb`"
                    ),
                    "kind": "danger",
                })
            except Exception as _e:
                set_upload_msg({
                    "text": f"**Upload failed:** {_e}",
                    "kind": "danger",
                })
    return


@app.cell
def _(get_upload_msg, mo):
    _msg = get_upload_msg()
    mo.output.replace(_msg and mo.callout(mo.md(_msg["text"]), kind=_msg["kind"]) or mo.md(""))
    return


@app.cell
def _(Path, mo, weave_details_btn, weave_project, ww):
    _msg = mo.md("")

    if weave_details_btn.value:
        _proj = weave_project.value.strip() or "wolfbench"
        _manifest_path = Path(__file__).parent / f"{_proj}-manifest.json"
        _manifest = ww.load_manifest(_manifest_path, project=_proj)
        _evals = _manifest.get("evaluations", {})

        if not _evals:
            _msg = mo.callout(mo.md("No uploads yet."), kind="info")
        else:
            _rows = []
            for _key, _ev in _evals.items():
                _runs = _ev.get("runs", {})
                _n_up = sum(1 for _r in _runs.values() if _r.get("uploaded"))
                _n_tr = sum(1 for _r in _runs.values() if _r.get("has_traces"))
                _rows.append({
                    "evaluation": _ev.get("eval_name", _key),
                    "runs": len(_runs),
                    "uploaded": f"{_n_up}/{len(_runs)}",
                    "with_traces": f"{_n_tr}/{len(_runs)}",
                    "url": _ev.get("weave_url", "-"),
                })
            _msg = mo.vstack([
                mo.md(
                    f"**Project:** {_manifest.get('project', '?')} · "
                    f"**Entity:** {_manifest.get('entity', '?')} · "
                    f"**Updated:** {_manifest.get('last_updated', '?')}"
                ),
                mo.ui.table(data=_rows, selection=None),
            ])

    _msg
    return


@app.cell
def _(final_valid, mo):
    save_button = mo.ui.run_button(
        label=f"Save Results ({len(final_valid)} valid runs)",
        disabled=len(final_valid) == 0,
    )
    _hint = (
        mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: no runs selected</span>')
        if len(final_valid) == 0 else mo.md("")
    )
    mo.vstack([mo.md("### Step 5: Save Results"), save_button, _hint])
    return (save_button,)


@app.cell
def _(Path, datetime, final_excluded, final_valid, json, mo, save_button):
    save_status = False
    save_ts = ""
    _save_msg = mo.md("")

    if save_button.value and final_valid:
        _dir = Path(__file__).parent
        _now = datetime.now().isoformat()

        _valid_data = {
            "collected_at": _now,
            "n_runs": len(final_valid),
            "benchmark": "terminal-bench-2.0",
            "expected_tasks": 89,
            "runs": final_valid,
        }
        _excluded_data = {
            "collected_at": _now,
            "n_runs": len(final_excluded),
            "runs": final_excluded,
        }

        save_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        _valid_path = _dir / f"wolfbench_results_{save_ts}.json"
        _excluded_path = _dir / f"wolfbench_results_excluded_{save_ts}.json"

        with open(_valid_path, "w") as _f:
            json.dump(_valid_data, _f, indent=2)
        with open(_excluded_path, "w") as _f:
            json.dump(_excluded_data, _f, indent=2)

        # Persist display overrides (model_display, thinking_display) to local config.json
        _n_overrides = 0
        for _r in final_valid:
            _md = _r.get("model_display") or ""
            _td = _r.get("thinking_display") or ""
            _rd = _r.get("run_dir", "")
            if not _rd:
                continue
            _cfg_path = Path(_rd) / "config.json"
            if not _cfg_path.exists():
                continue
            try:
                _cfg = json.loads(_cfg_path.read_text())
                _changed = False
                for _field, _val in [("model_display", _md), ("thinking_display", _td)]:
                    _old = _cfg.get(_field, "")
                    if _val != _old:
                        if _val:
                            _cfg[_field] = _val
                        elif _field in _cfg:
                            del _cfg[_field]
                        _changed = True
                if _changed:
                    _cfg_path.write_text(json.dumps(_cfg, indent=2) + "\n")
                    _n_overrides += 1
            except (json.JSONDecodeError, OSError):
                pass

        _override_note = f"\n\nWrote **{_n_overrides}** display override(s) to config.json" if _n_overrides else ""
        save_status = True
        _save_msg = mo.callout(
            mo.md(
                f"Saved **{len(final_valid)}** valid runs to "
                f"`{_valid_path.name}`\n\n"
                f"Saved **{len(final_excluded)}** excluded runs to "
                f"`{_excluded_path.name}`{_override_note}"
            ),
            kind="success",
        )

    _save_msg
    return save_status, save_ts


@app.cell
def _(date, mo, save_ts):
    chart_date_picker = mo.ui.date(value=date.today())
    chart_button = mo.ui.run_button(
        label="Generate Chart",
        disabled=not save_ts,
    )

    _hint = (
        mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: save results first (Step 5)</span>')
        if not save_ts else mo.md("")
    )

    mo.vstack([
        mo.md("### Step 6: Generate Chart"),
        mo.hstack(
            [mo.md("**Chart date:**"), chart_date_picker, chart_button],
            justify="start",
            gap=1,
        ),
        _hint,
    ])
    return chart_button, chart_date_picker


@app.cell
def _(Path, chart_button, chart_date_picker, mo, save_ts, subprocess, weave_project, webbrowser):
    _chart_msg = mo.md("")
    chart_html = ""

    if chart_button.value:
        _dir = Path(__file__).parent
        _input_path = _dir / f"wolfbench_results_{save_ts}.json"
        _date_str = str(chart_date_picker.value)
        _output_base = _dir / f"wolfbench_{save_ts}"

        if not _input_path.exists():
            _chart_msg = mo.callout(
                mo.md(
                    f"**{_input_path.name} not found.** "
                    f"Save results first (Step 5) before generating the chart."
                ),
                kind="danger",
            )
        else:
            _chart_script = _dir / "wolfbench-chart.py"
            _proj = weave_project.value.strip() or "wolfbench"
            _manifest_path = _dir / f"{_proj}-manifest.json"
            _cmd = [
                "python3",
                str(_chart_script),
                "-i",
                str(_input_path),
                "-o",
                str(_output_base),
                "--date",
                _date_str,
            ]
            if _manifest_path.exists():
                _cmd.extend(["--weave-manifest", str(_manifest_path)])
            with mo.status.spinner("Generating chart..."):
                _r = subprocess.run(_cmd, capture_output=True, text=True)
            if _r.returncode == 0:
                _out_file = _output_base.with_suffix(".html")
                chart_html = str(_out_file)
                webbrowser.open(_out_file.as_uri())
                _chart_msg = mo.callout(
                    mo.md(
                        f"Chart generated and opened: `{_out_file.name}`\n\n"
                        f"```\n{_r.stdout.strip()}\n```"
                    ),
                    kind="success",
                )
            else:
                _chart_msg = mo.callout(
                    mo.md(
                        f"**Chart generation failed.**\n\n"
                        f"```\n{(_r.stdout + _r.stderr).strip()}\n```"
                    ),
                    kind="danger",
                )

    _chart_msg
    return (chart_html,)


@app.cell
def _(chart_html, mo, upload_target):
    _has_target = bool(upload_target.value.strip())

    _can_upload = _has_target and chart_html

    upload_button = mo.ui.run_button(
        label="Upload Chart",
        disabled=not _can_upload,
    )
    symlink_checkbox = mo.ui.checkbox(
        label="Also symlink to index.html",
        value=False,
        disabled=not _has_target,
    )

    if not _has_target:
        _hint = mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: set upload target in Configuration above</span>')
    elif not chart_html:
        _hint = mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: generate a chart first (Step 6)</span>')
    else:
        _hint = mo.md("")

    mo.vstack([
        mo.md("### Step 7: Upload Chart"),
        mo.hstack([upload_button, symlink_checkbox], justify="start", gap=1),
        _hint,
    ])
    return symlink_checkbox, upload_button


@app.cell
def _(Path, chart_html, mo, subprocess, symlink_checkbox, upload_button, upload_target):
    _upload_msg = mo.md("")

    if upload_button is not None and upload_button.value and chart_html:
        _target = upload_target.value.strip()
        if not _target:
            _upload_msg = mo.callout(
                mo.md("**Upload target not set.** Configure it at the top of the dashboard."),
                kind="danger",
            )
        else:
            _html_path = Path(chart_html)
            _filename = _html_path.name

            # scp the HTML file
            with mo.status.spinner(f"Uploading `{_filename}` to `{_target}`..."):
                _r = subprocess.run(
                    ["scp", str(_html_path), _target],
                    capture_output=True, text=True,
                )

            if _r.returncode != 0:
                _upload_msg = mo.callout(
                    mo.md(
                        f"**Upload failed.**\n\n"
                        f"```\n{(_r.stdout + _r.stderr).strip()}\n```"
                    ),
                    kind="danger",
                )
            else:
                _parts = [f"Uploaded `{_filename}` to `{_target}`"]

                # Optionally symlink to index.html
                if symlink_checkbox.value:
                    # Parse host and remote dir from "user@server:path" or "server:path"
                    _host, _remote_dir = _target.split(":", 1)
                    # Ensure remote dir exists and is a directory
                    _check = subprocess.run(
                        ["ssh", _host, f"mkdir -p {_remote_dir} && test -d {_remote_dir}"],
                        capture_output=True, text=True,
                    )
                    if _check.returncode != 0:
                        _parts.append(
                            f"**Symlink failed:** `{_remote_dir}` is not a directory on `{_host}`"
                        )
                    else:
                        _r2 = subprocess.run(
                            ["ssh", _host, f"cd {_remote_dir} && ln -sf {_filename} index.html"],
                            capture_output=True, text=True,
                        )
                        if _r2.returncode == 0:
                            _parts.append(f"Symlinked `index.html` → `{_filename}`")
                        else:
                            _parts.append(
                                f"**Symlink failed:**\n```\n{(_r2.stdout + _r2.stderr).strip()}\n```"
                            )

                _upload_msg = mo.callout(
                    mo.md("\n\n".join(_parts)),
                    kind="success",
                )

    _upload_msg
    return


if __name__ == "__main__":
    app.run()
