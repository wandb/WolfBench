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

    mo.vstack([
        mo.md("### W&B Weave Configuration"),
        mo.hstack([weave_project, weave_entity], widths=[1, 1]),
        weave_api_key,
        mo.md(
            '<span style="color:#9BA1A6;font-size:0.85rem;">'
            "Pre-filled from WANDB_API_KEY / WANDB_PROJECT / WANDB_ENTITY env vars. "
            "Entity = W&B team/org namespace (leave empty for default account). "
            "Override here for testing."
            "</span>"
        ),
    ])
    return weave_api_key, weave_entity, weave_project


@app.cell
def _(Path):
    import sys as _sys
    import importlib as _importlib

    _script_dir = str(Path(__file__).parent)
    if _script_dir not in _sys.path:
        _sys.path.insert(0, _script_dir)

    hcr = _importlib.import_module("wolfbench_collect")
    _importlib.reload(hcr)
    LOCAL_RUNS_DIR = Path(__file__).parent / "runs"
    None
    return LOCAL_RUNS_DIR, hcr


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
    return get_exe_vms, get_hz_vms, set_exe_vms, set_hz_vms


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
                "thinking": _thinking,
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
            value="timeout=3600s,tasks=89,errors<3",
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
        final_valid = [
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
            f"**Selection:** {len(final_valid)} valid, "
            f"{len(final_excluded)} excluded"
        )
    else:
        final_valid = []
        final_excluded = []
        _msg = mo.md("")
    _msg
    return final_excluded, final_valid


@app.cell
def _(LOCAL_RUNS_DIR, final_valid, mo):
    _vm_only = [r for r in final_valid if r.get("vm") != "local"]
    _n_vm = len(_vm_only)
    download_meta_btn = mo.ui.run_button(
        label=f"Download Metadata ({_n_vm} runs)",
        disabled=_n_vm == 0,
    )
    download_full_btn = mo.ui.run_button(
        label=f"Download Full + Trajectories ({_n_vm} runs)",
        disabled=_n_vm == 0,
    )
    _hint = (
        mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: all runs already local</span>')
        if _n_vm == 0 and len(final_valid) > 0
        else mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: no runs selected</span>')
        if len(final_valid) == 0
        else mo.md(
            '<span style="color:#9BA1A6;font-size:0.85rem;">'
            "Metadata = result.json + config.json (~fast). "
            "Full = includes trajectory.json files (~slow, needed for Tier 2 Weave upload)."
            "</span>"
        )
    )
    mo.vstack([
        mo.md(f"### Step 3: Download to Local Storage\n\n`{LOCAL_RUNS_DIR}`"),
        mo.hstack([download_meta_btn, download_full_btn], justify="start", gap=1),
        _hint,
    ])
    return download_full_btn, download_meta_btn


@app.cell
def _(LOCAL_RUNS_DIR, download_full_btn, download_meta_btn, final_valid, hcr, mo):
    download_status = False
    _dl_msg = mo.md("")

    _do_meta = download_meta_btn.value
    _do_full = download_full_btn.value

    if (_do_meta or _do_full) and final_valid:
        _vm_only = [r for r in final_valid if r.get("vm") != "local"]
        if _vm_only:
            _include_traj = bool(_do_full)
            _mode = "full + trajectories" if _include_traj else "metadata"
            with mo.status.spinner(f"Downloading {len(_vm_only)} runs ({_mode})..."):
                _results = hcr.download_runs(
                    _vm_only,
                    LOCAL_RUNS_DIR,
                    include_trajectories=_include_traj,
                    max_workers=4,
                )
            _ok = sum(1 for r in _results if r["status"] == "ok")
            _skip = sum(1 for r in _results if r["status"] == "skipped")
            _err = sum(1 for r in _results if r["status"] == "error")
            download_status = True
            _dl_msg = mo.callout(
                mo.md(
                    f"Downloaded **{_ok}**, skipped **{_skip}** (already local), "
                    f"**{_err}** errors.\n\n"
                    f"Re-scan to see local copies in the table."
                ),
                kind="success" if _err == 0 else "warn",
            )

    _dl_msg
    return (download_status,)


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
    mo.vstack([mo.md("### Step 4: Save Results"), save_button, _hint])
    return (save_button,)


@app.cell
def _(Path, datetime, final_excluded, final_valid, json, mo, save_button):
    save_status = False
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

        _ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        _valid_path = _dir / f"harbor_results_{_ts}.json"
        _excluded_path = _dir / f"harbor_results_excluded_{_ts}.json"

        with open(_valid_path, "w") as _f:
            json.dump(_valid_data, _f, indent=2)
        with open(_excluded_path, "w") as _f:
            json.dump(_excluded_data, _f, indent=2)

        # Also write the canonical files for wolfbench-chart.py
        with open(_dir / "harbor_results.json", "w") as _f:
            json.dump(_valid_data, _f, indent=2)
        with open(_dir / "harbor_results_excluded.json", "w") as _f:
            json.dump(_excluded_data, _f, indent=2)

        save_status = True
        _save_msg = mo.callout(
            mo.md(
                f"Saved **{len(final_valid)}** valid runs to "
                f"`{_valid_path.name}`\n\n"
                f"Saved **{len(final_excluded)}** excluded runs to "
                f"`{_excluded_path.name}`\n\n"
                f"Also updated `harbor_results.json` / "
                f"`harbor_results_excluded.json`"
            ),
            kind="success",
        )

    _save_msg
    return (save_status,)


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
def _(final_valid, mo, weave_api_key):
    import os as _os

    _has_key = bool(weave_api_key.value.strip() or _os.environ.get("WANDB_API_KEY"))
    _has_runs = len(final_valid) > 0
    _can_upload = _has_key and _has_runs

    weave_tier1_btn = mo.ui.run_button(
        label="Upload Evaluations (Tier 1)",
        disabled=not _can_upload,
    )
    weave_tier2_btn = mo.ui.run_button(
        label="Upload Traces (Tier 2)",
        disabled=not _can_upload,
    )
    weave_status_btn = mo.ui.run_button(label="Show Upload Status")

    _reasons = []
    if not _has_key:
        _reasons.append("API key not set")
    if not _has_runs:
        _reasons.append("no runs selected")
    _hint = (
        mo.md(f'<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: {", ".join(_reasons)}</span>')
        if _reasons else mo.md("")
    )

    mo.vstack([
        mo.md("### Step 5: Upload to W&B Weave"),
        mo.hstack(
            [weave_tier1_btn, weave_tier2_btn, weave_status_btn],
            justify="start",
            gap=1,
        ),
        _hint,
    ])
    return weave_status_btn, weave_tier1_btn, weave_tier2_btn


@app.cell
async def _(Path, final_valid, mo, weave_api_key, weave_entity, weave_project, weave_tier1_btn, ww):
    import os as _os

    weave_tier1_result = {}
    _msg = mo.md("")

    if weave_tier1_btn.value and final_valid:
        _key = weave_api_key.value.strip()
        _proj = weave_project.value.strip() or "wolfbench"
        _manifest_path = Path(__file__).parent / f"{_proj}-manifest.json"
        _ent = weave_entity.value.strip() or None
        if _key:
            _os.environ["WANDB_API_KEY"] = _key
        if not _os.environ.get("WANDB_API_KEY"):
            _msg = mo.callout(
                mo.md("**WANDB_API_KEY** is not set. Enter it above or export it before launching."),
                kind="warn",
            )
        else:
            try:
                with mo.status.spinner(f"Uploading evaluations to W&B Weave ({_proj})..."):
                    weave_tier1_result = await ww.upload_evaluations(
                        runs=final_valid,
                        project=_proj,
                        entity=_ent,
                        manifest_path=_manifest_path,
                    )
                _msg = mo.callout(
                    mo.md(weave_tier1_result.get("summary", "Done.")),
                    kind="success",
                )
            except ImportError as _e:
                _msg = mo.callout(
                    mo.md(
                        f"**Missing dependency:** {_e}\n\n"
                        f"Install with: `uv pip install weave wandb`"
                    ),
                    kind="danger",
                )
            except Exception as _e:
                _msg = mo.callout(
                    mo.md(f"**Upload failed:** {_e}"),
                    kind="danger",
                )

    _msg
    return (weave_tier1_result,)


@app.cell
async def _(LOCAL_RUNS_DIR, Path, final_valid, mo, weave_api_key, weave_entity, weave_project, weave_tier2_btn, ww):
    import os as _os

    _msg = mo.md("")

    if weave_tier2_btn.value and final_valid:
        _key = weave_api_key.value.strip()
        _proj = weave_project.value.strip() or "wolfbench"
        _manifest_path = Path(__file__).parent / f"{_proj}-manifest.json"
        _ent = weave_entity.value.strip() or None
        if _key:
            _os.environ["WANDB_API_KEY"] = _key
        if not _os.environ.get("WANDB_API_KEY"):
            _msg = mo.callout(
                mo.md("**WANDB_API_KEY** is not set. Enter it above or export it before launching."),
                kind="warn",
            )
        else:
            try:
                with mo.status.spinner(
                    f"Loading trajectories & uploading traces ({_proj})..."
                ):
                    _t2_result = await ww.upload_all_traces(
                        runs=final_valid,
                        project=_proj,
                        entity=_ent,
                        manifest_path=_manifest_path,
                        local_runs_dir=LOCAL_RUNS_DIR,
                    )
                _msg = mo.callout(
                    mo.md(_t2_result.get("summary", "Done.")),
                    kind="success",
                )
            except ImportError as _e:
                _msg = mo.callout(
                    mo.md(
                        f"**Missing dependency:** {_e}\n\n"
                        f"Install with: `uv pip install weave wandb`"
                    ),
                    kind="danger",
                )
            except Exception as _e:
                _msg = mo.callout(
                    mo.md(f"**Trace upload failed:** {_e}"),
                    kind="danger",
                )

    _msg
    return


@app.cell
def _(Path, mo, weave_project, weave_status_btn, ww):
    _msg = mo.md("")

    if weave_status_btn.value:
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
                _t1 = sum(1 for _r in _runs.values() if _r.get("tier1_uploaded"))
                _t2 = sum(1 for _r in _runs.values() if _r.get("tier2_uploaded"))
                _rows.append({
                    "evaluation": _ev.get("eval_name", _key),
                    "runs": len(_runs),
                    "tier1": f"{_t1}/{len(_runs)}",
                    "tier2": f"{_t2}/{len(_runs)}",
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
def _(Path, date, mo, save_status):
    chart_date_picker = mo.ui.date(value=date.today())
    _has_saved = save_status or (Path(__file__).parent / "harbor_results.json").exists()
    chart_button = mo.ui.run_button(
        label="Generate Chart",
        disabled=not _has_saved,
    )

    _hint = (
        mo.md('<span style="color:#9BA1A6;font-size:0.85rem;">Disabled: no saved harbor_results.json (save results first)</span>')
        if not _has_saved else mo.md("")
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
def _(Path, chart_button, chart_date_picker, mo, subprocess, weave_project, webbrowser):
    _chart_msg = mo.md("")

    if chart_button.value:
        _dir = Path(__file__).parent
        _input_path = _dir / "harbor_results.json"
        _date_str = str(chart_date_picker.value)
        _output_base = _dir / f"wolfbench_{_date_str}"

        if not _input_path.exists():
            _chart_msg = mo.callout(
                mo.md(
                    "**harbor_results.json not found.** "
                    "Save results first (Step 3) before generating the chart."
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
    return


if __name__ == "__main__":
    app.run()
