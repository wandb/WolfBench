#!/usr/bin/env python3
"""WolfBench Chart — HTML/CSS Chart Generator.

Generates a WolfBench chart as a standalone HTML file with metallic-gradient
bars per model/agent, using the Four-Metric Framework.

Usage:
    python wolfbench-chart.py                    # Generate wolfbench.html
    python wolfbench-chart.py -i results.json    # Custom input
    python wolfbench-chart.py --min-runs 3       # Require ≥3 runs
"""

import argparse
import base64
import json
from collections import Counter, defaultdict
from datetime import date
from html import escape as _html_escape
from pathlib import Path

TOTAL_TASKS = 89

AGENT_CONFIG = {
    "terminus-2": {
        "label": "T2",
        "name": "Terminus-2",
        "gradient": {
            "solid":   ("linear-gradient(135deg, #0a3d1a 0%, #145a32 40%, #1e8449 70%, #27ae60 100%)",
                        "0 0 12px rgba(39,174,96,0.3)"),
            "average": ("linear-gradient(135deg, #1a7a3a 0%, #27ae60 40%, #2ecc71 70%, #58d68d 100%)",
                        "0 0 12px rgba(46,204,113,0.3)"),
            "best":    ("linear-gradient(135deg, #27ae60 0%, #58d68d 40%, #82e0aa 70%, #a9dfbf 100%)",
                        "0 0 12px rgba(88,214,141,0.3)"),
            "ceiling": ("linear-gradient(135deg, #58d68d 0%, #abebc6 40%, #d5f5e3 70%, #eafaf1 100%)",
                        "0 0 8px rgba(171,235,198,0.2)"),
        },
    },
    "claude-code": {
        "label": "CC",
        "name": "Claude Code",
        "gradient": {
            "solid":   ("linear-gradient(135deg, #5a2d00 0%, #7d3c00 40%, #b35900 70%, #e67e22 100%)",
                        "0 0 12px rgba(230,126,34,0.3)"),
            "average": ("linear-gradient(135deg, #7d3c00 0%, #e67e22 40%, #f0b27a 70%, #f5cba7 100%)",
                        "0 0 12px rgba(240,178,122,0.3)"),
            "best":    ("linear-gradient(135deg, #e67e22 0%, #f0b27a 40%, #f5cba7 70%, #fdebd0 100%)",
                        "0 0 12px rgba(245,203,167,0.3)"),
            "ceiling": ("linear-gradient(135deg, #f0b27a 0%, #fdebd0 40%, #fef5e7 70%, #fffaf2 100%)",
                        "0 0 8px rgba(253,235,208,0.2)"),
        },
    },
    "openclaw": {
        "label": "OC",
        "name": "OpenClaw",
        "gradient": {
            "solid":   ("linear-gradient(135deg, #641e16 0%, #922b21 40%, #c0392b 70%, #e74c3c 100%)",
                        "0 0 12px rgba(231,76,60,0.3)"),
            "average": ("linear-gradient(135deg, #922b21 0%, #e74c3c 40%, #ec7063 70%, #f1948a 100%)",
                        "0 0 12px rgba(241,148,138,0.3)"),
            "best":    ("linear-gradient(135deg, #e74c3c 0%, #f1948a 40%, #f5b7b1 70%, #fadbd8 100%)",
                        "0 0 12px rgba(245,183,177,0.3)"),
            "ceiling": ("linear-gradient(135deg, #f1948a 0%, #fadbd8 40%, #fdedec 70%, #fef9f8 100%)",
                        "0 0 8px rgba(250,219,216,0.2)"),
        },
    },
}

MODEL_DISPLAY = {
    "claude-opus-4-6":   "Claude Opus 4.6",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "Kimi-K2.5":         "Kimi K2.5",
    "MiniMax-M2.5":      "MiniMax M2.5",
    "GLM-5-FP8":         "GLM-5 FP8",
}

METRIC_LABELS = {
    "solid":   ("■", "Solid",   "always solved"),
    "average": ("∅", "Average", "mean score"),
    "best":    ("★", "Best-of", "peak run"),
    "ceiling": ("▲", "Ceiling", "ever solved"),
}


def compute_metrics(runs: list[dict]) -> dict | None:
    n_runs = len(runs)
    scores = [r["score"] for r in runs if r["score"] is not None]
    if not scores:
        return None

    task_pass_counts = Counter()
    for r in runs:
        for t in r["passed_tasks"]:
            task_pass_counts[t] += 1

    solid = sum(1 for c in task_pass_counts.values() if c == n_runs)
    ceiling = len(task_pass_counts)

    # Extract timeout (most common value; typically uniform per group)
    timeouts = [r.get("timeout_sec") for r in runs if r.get("timeout_sec") is not None]
    timeout_sec = max(set(timeouts), key=timeouts.count) if timeouts else None

    return {
        "n_runs": n_runs,
        "solid": round(solid / TOTAL_TASKS * 100),
        "average": round(sum(scores) / len(scores) * 100),
        "best": round(max(scores) * 100),
        "ceiling": round(ceiling / TOTAL_TASKS * 100),
        "solid_abs": solid,
        "avg_abs": round(sum(scores) / len(scores) * TOTAL_TASKS),
        "best_abs": round(max(scores) * TOTAL_TASKS),
        "ceiling_abs": ceiling,
        "timeout_sec": timeout_sec,
    }


def _fmt_timeout_h(sec: float | int | None) -> str:
    """Convert timeout seconds to compact hours string: 7200→'2h', 5400→'1.5h'."""
    if sec is None:
        return ""
    h = sec / 3600
    return f"{h:.0f}h" if h == int(h) else f"{h:.1f}h"


# Scale: pixels per percentage point
PX_PER_PCT = 6
CHART_HEIGHT = 100 * PX_PER_PCT  # 600px for 100%


def _bar_segments_html(metrics: dict, agent_cfg: dict) -> str:
    """Generate the stacked bar segments for one agent/model combo."""
    grads = agent_cfg["gradient"]
    _abs_px = lambda v: v / TOTAL_TASKS * 100 * PX_PER_PCT

    seg = [
        ("solid",   metrics["solid"],                       metrics["solid_abs"]),
        ("average", metrics["average"] - metrics["solid"],  metrics["avg_abs"] - metrics["solid_abs"]),
        ("best",    metrics["best"] - metrics["average"],   metrics["best_abs"] - metrics["avg_abs"]),
        ("ceiling", metrics["ceiling"] - metrics["best"],   metrics["ceiling_abs"] - metrics["best_abs"]),
    ]

    # Segment divs (no labels inside — labels are positioned separately)
    parts = []
    for key, height_pct, height_abs in seg:
        if height_pct <= 0 and height_abs <= 0:
            continue
        gradient, shadow = grads[key]
        px_h = max(height_pct * PX_PER_PCT, 2)
        px_h_abs = max(_abs_px(height_abs), 2)
        parts.append(f'''
            <div class="segment segment-{key}" data-metric="{key}"
                 data-h-pct="{px_h:.1f}" data-h-abs="{px_h_abs:.1f}" style="
                height: {px_h}px;
                background: {gradient};
                box-shadow: {shadow}, inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.2);
            ">
                <div class="segment-shine"></div>
            </div>''')

    # Reverse so ceiling is on top (we build bottom-up)
    parts.reverse()

    # Collect labels, then nudge to avoid overlap
    total_h = metrics["ceiling"] * PX_PER_PCT
    total_h_abs = _abs_px(metrics["ceiling_abs"])

    if metrics["n_runs"] == 1:
        # Single run: all four metrics are identical — just show the value, no symbols
        val = metrics["ceiling"]
        abs_val = metrics["ceiling_abs"]
        bottom_px = val * PX_PER_PCT
        abs_bottom_px = _abs_px(abs_val)
        label_parts = [
            f'<span class="seg-label"'
            f' data-true-bottom="{bottom_px:.1f}"'
            f' data-bottom-pct="{bottom_px:.1f}" data-bottom-abs="{abs_bottom_px:.1f}"'
            f' style="bottom: {bottom_px:.1f}px;">'
            f'<span class="seg-pct" data-pct="{val}%" data-abs="{abs_val}">{val}%</span></span>'
        ]
    else:
        _abs_key = {"solid": "solid_abs", "average": "avg_abs",
                    "best": "best_abs", "ceiling": "ceiling_abs"}
        labels = []
        for key in ("solid", "average", "best", "ceiling"):
            val = metrics[key]
            abs_val = metrics[_abs_key[key]]
            sym, name, _ = METRIC_LABELS[key]
            labels.append((val, abs_val, sym, f"{val}%", str(abs_val), key))

        labels.sort(key=lambda t: t[0])

        # Collision avoidance helper
        def _snap_positions(raw_px: list[float], max_bottom: float) -> list[float]:
            min_gap_px = 15  # ~label height at 0.7rem
            positions = list(raw_px)
            for _ in range(40):
                changed = False
                for i in range(len(positions) - 1):
                    gap = positions[i + 1] - positions[i]
                    if gap < min_gap_px:
                        push = (min_gap_px - gap) / 2
                        positions[i] -= push
                        positions[i + 1] += push
                        changed = True
                if positions and positions[-1] > max_bottom:
                    overshoot = positions[-1] - max_bottom
                    positions = [p - overshoot for p in positions]
                    changed = True
                if positions and positions[0] < 0:
                    undershoot = -positions[0]
                    positions = [p + undershoot for p in positions]
                    changed = True
                if not changed:
                    break
            return positions

        # Compute positions for both percentage and absolute modes
        pct_raw = [val * PX_PER_PCT for val, _, _, _, _, _ in labels]
        abs_raw = [abs_v / TOTAL_TASKS * 100 * PX_PER_PCT for _, abs_v, _, _, _, _ in labels]
        pct_positions = _snap_positions(pct_raw, total_h)
        abs_positions = _snap_positions(abs_raw, total_h)

        label_parts = []
        for (val, abs_v, sym, pct, abs_val, metric_key), bottom_px, abs_bottom_px in zip(
                labels, pct_positions, abs_positions):
            true_px = val * PX_PER_PCT
            label_parts.append(
                f'<span class="seg-label" data-metric="{metric_key}"'
                f' data-true-bottom="{true_px:.1f}"'
                f' data-bottom-pct="{bottom_px:.1f}" data-bottom-abs="{abs_bottom_px:.1f}"'
                f' style="bottom: {bottom_px:.1f}px;">'
                f'<span class="seg-sym">{sym}</span>'
                f'<span class="seg-pct" data-pct="{pct}" data-abs="{abs_val}">{pct}</span></span>'
            )

    segments_html = "\n".join(parts)
    labels_html = "\n".join(label_parts)

    return f'''
        <div class="bar-inner" style="height: {total_h}px;"
             data-h-pct="{total_h:.1f}" data-h-abs="{total_h_abs:.1f}"
             data-h-solid="{metrics['solid'] * PX_PER_PCT:.1f}"
             data-h-average="{metrics['average'] * PX_PER_PCT:.1f}"
             data-h-best="{metrics['best'] * PX_PER_PCT:.1f}"
             data-h-ceiling="{total_h:.1f}">
            <div class="bar-segments">{segments_html}</div>
            <div class="bar-labels">{labels_html}</div>
        </div>'''


def _build_runs_table_html(runs: list[dict]) -> str:
    """Build a collapsed HTML <details> table showing individual run data."""
    if not runs:
        return ""

    def _fmt_tok(n):
        if not n:
            return "-"
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)

    # Sort: date descending (latest first)
    sorted_runs = sorted(runs, key=lambda r: r.get("timestamp", ""), reverse=True)

    rows: list[str] = []
    for r in sorted_runs:
        # Date+Time merged: "2026-03-01 13:43"
        ts = r.get("timestamp", "")
        dt = ts[:10] if ts else "-"
        tm = ts[12:17].replace("-", ":") if len(ts) >= 17 else ""
        date_time = f"{dt} {tm}".strip() if dt != "-" else "-"

        # Agent (full name) + version in brackets: "OpenClaw (v2026.2.17)"
        agent = r.get("agent", "?")
        agent_name = AGENT_CONFIG.get(agent, {}).get("name", agent)
        ver = r.get("agent_version") or "-"
        agent_ver = f"{agent_name} ({ver})" if ver != "-" else agent_name

        # Provider / Vendor from full model path
        model_full = r.get("model", "unknown")
        model_parts = model_full.split("/")
        if len(model_parts) >= 3:
            provider = model_parts[0]
            vendor = model_parts[1]
        elif len(model_parts) == 2:
            provider = model_parts[0]
            vendor = model_parts[0]
        else:
            provider = "-"
            vendor = "-"

        model = r.get("model_display", model_full)

        t = r.get("thinking")
        if t is None:
            think = "-"
        elif t is True or t == "enabled":
            think = "on"
        elif t is False or t == "disabled":
            think = "off"
        else:
            think = str(t)

        score = f'{r["score"]:.1%}' if r.get("score") is not None else "?"
        n_p = r.get("n_passed", 0)
        n_f = r.get("n_failed", 0)
        n_t = r.get("n_trials", 0)

        to_sec = r.get("timeout_sec")
        to_str = f"{int(to_sec)}s" if to_sec is not None else "-"

        eb = r.get("error_breakdown", {})
        ato = eb.get("AgentTimeoutError", 0)
        lost = max(0, n_t - n_p - n_f)

        dur = "-"
        if r.get("duration_sec"):
            h, rem = divmod(int(r["duration_sec"]), 3600)
            m, _ = divmod(rem, 60)
            dur = f"{h}h{m:02d}m"

        # Total In = uncached input + cached input
        tok_in_raw = r.get("tokens_in")
        tok_cache_raw = r.get("tokens_cache")
        tok_total_in = None
        if tok_in_raw is not None or tok_cache_raw is not None:
            tok_total_in = (tok_in_raw or 0) + (tok_cache_raw or 0)
        tok_in = _fmt_tok(tok_total_in)
        tok_out = _fmt_tok(r.get("tokens_out"))

        # Cost (commented out for now — uncomment when more models have cost)
        # cost = r.get("cost_usd")
        # cost_str = f"${cost:.2f}" if cost else "-"

        rows.append(
            f"<tr>"
            f"<td>{_html_escape(date_time)}</td>"
            f"<td>{_html_escape(agent_ver)}</td>"
            f"<td>{_html_escape(provider)}</td>"
            f"<td>{_html_escape(vendor)}</td>"
            f"<td>{_html_escape(model)}</td>"
            f"<td>{think}</td>"
            f"<td class='n'>{score}</td>"
            f"<td class='n'>{n_p}</td>"
            f"<td class='n'>{n_f}</td>"
            f"<td>{to_str}</td>"
            f"<td class='n'>{ato}</td>"
            f"<td class='n'>{lost}</td>"
            f"<td>{dur}</td>"
            f"<td class='n'>{tok_in}</td>"
            f"<td class='n'>{tok_out}</td>"
            # f"<td class='n'>{cost_str}</td>"
            f"</tr>"
        )

    return (
        f'<details class="runs-details">\n'
        f'<summary>Run Details ({len(runs)} runs)</summary>\n'
        f'<div class="runs-table-wrap">\n'
        f'<table class="runs-table">\n'
        f'<thead><tr>'
        f'<th data-sort="desc">Date</th><th>Agent</th>'
        f'<th>Provider</th><th>Vendor</th><th>Model</th><th>Think</th>'
        f'<th>Score</th><th>Pass</th><th>Fail</th>'
        f'<th>Timeout</th><th>T/O</th><th>Err</th>'
        f'<th>Duration</th>'
        f'<th>In</th><th>Out</th>'
        # f'<th>Cost</th>'
        f'</tr></thead>\n'
        f'<tbody>\n{"".join(rows)}\n</tbody>\n'
        f'</table>\n'
        f'</div>\n'
        f'</details>'
    )


def generate_html(
    groups: dict[tuple[str, str, str, float | None], dict],
    output_path: Path,
    min_runs: int = 1,
    agent_versions: dict[str, set[str]] | None = None,
    chart_date: str | None = None,
    runs: list[dict] | None = None,
    weave_urls: dict[tuple, str] | None = None,
) -> Path:
    # Embed logo as base64
    _logo_path = Path(__file__).parent / "Endorsed_secondary_goldwhite.png"
    logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")

    # Filter
    groups = {k: v for k, v in groups.items() if v["n_runs"] >= min_runs}
    if not groups:
        print("No groups meet the minimum run threshold.")
        return None

    # Organize by model — keyed by (agent, version, timeout) tuple
    models_with_data: dict[str, dict[tuple[str, str, float | None], dict]] = defaultdict(dict)
    for (agent, ver, model, timeout), metrics in groups.items():
        models_with_data[model][(agent, ver, timeout)] = metrics

    model_order = sorted(
        models_with_data.keys(),
        key=lambda m: max(v["average"] for v in models_with_data[m].values()),
        reverse=True,
    )

    # Ordered (agent, version, timeout) triples: AGENT_CONFIG order, then version asc, timeout asc
    _seen_triples: set[tuple[str, str, float | None]] = set()
    for m_data in models_with_data.values():
        _seen_triples.update(m_data.keys())
    agent_ver_order: list[tuple[str, str, float | None]] = []
    for a in AGENT_CONFIG:
        matches = sorted(
            ((ver, to) for (ag, ver, to) in _seen_triples if ag == a),
            key=lambda x: (x[0], x[1] or 0),
        )
        for v, t in matches:
            agent_ver_order.append((a, v, t))
    # Flat agent list (unique, preserving AGENT_CONFIG order) for legend/footer
    agent_order = [a for a in AGENT_CONFIG
                   if any(ag == a for ag, _, _ in agent_ver_order)]

    # Build model groups HTML
    model_groups_html = []
    model_group_widths = []
    for model in model_order:
        bars_html = []
        group_bar_widths = []
        for agent, ver, timeout in agent_ver_order:
            if (agent, ver, timeout) not in models_with_data[model]:
                continue
            m = models_with_data[model][(agent, ver, timeout)]
            cfg = AGENT_CONFIG[agent]
            segments = _bar_segments_html(m, cfg)
            n_runs = m["n_runs"]
            bar_w = max(28, round(68 / 5 * min(n_runs, 10)))
            group_bar_widths.append(bar_w)
            timeout_str = f"@{_fmt_timeout_h(m.get('timeout_sec'))}" if m.get("timeout_sec") else ""
            ver_display = ver if ver != "unknown" else "-"
            _wurl = (weave_urls or {}).get((agent, ver, model, m.get("timeout_sec")))
            _wopen = f'<a href="{_html_escape(_wurl)}" target="_blank" class="bar-link" title="View on W&amp;B Weave">' if _wurl else ""
            _wclose = "</a>" if _wurl else ""
            bars_html.append(f'''
                <div class="bar-wrapper" data-agent="{agent}" data-runs="{n_runs}">
                    <div class="bar-top-label">{cfg["label"]}<br><span class="version-label">{ver_display}</span></div>
                    {_wopen}<div class="bar" data-agent="{agent}" style="width: {bar_w}px;">
                        {segments}
                    </div>{_wclose}
                    <div class="bar-bottom-label"><span class="run-count">{n_runs}R{timeout_str}</span></div>
                </div>''')

        group_w = (sum(group_bar_widths) + max(0, len(group_bar_widths) - 1) * 8) if group_bar_widths else 0
        if group_bar_widths:
            model_group_widths.append(group_w)

        display = MODEL_DISPLAY.get(model, model)
        model_groups_html.append(f'''
            <div class="model-group" data-model="{_html_escape(model)}" data-width="{group_w}">
                <div class="model-label">{display}</div>
                <div class="bars-row">
                    {"".join(bars_html)}
                </div>
            </div>''')

    # Minimum chart width based on actual bar content
    n_groups = len(model_group_widths)
    chart_min_w = (
        sum(model_group_widths) + max(0, n_groups - 1) * 48 + n_groups * 40
    ) if n_groups else 400

    # Legend
    legend_agents = []
    for agent in agent_order:
        cfg = AGENT_CONFIG[agent]
        legend_agents.append(
            f'<span class="legend-agent legend-agent-{agent}">'
            f'{cfg["label"]} = {cfg["name"]}</span>'
        )

    legend_metrics = []
    for key in ("ceiling", "best", "average", "solid"):
        sym, name, desc = METRIC_LABELS[key]
        legend_metrics.append(
            f'<span class="legend-metric legend-metric-{key}" data-metric="{key}">'
            f'{sym} {name}&nbsp;<small>({desc})</small></span>'
        )

    # Model bar buttons (toggle visibility + drag to reorder)
    model_bar_buttons = []
    for model in model_order:
        display = MODEL_DISPLAY.get(model, model)
        model_bar_buttons.append(
            f'<span class="model-btn" data-model="{_html_escape(model)}" draggable="true">'
            f'{display}</span>'
        )

    # Build agent version line for footer + JS lookup
    _agent_version_map: dict[str, str] = {}
    _version_parts = []
    for _a in agent_order:
        _cfg = AGENT_CONFIG[_a]
        _vers = agent_versions.get(_a, set()) if agent_versions else set()
        if _vers:
            _ver_list = ", ".join(sorted(_vers))
            _entry = f"{_cfg['name']} ({_ver_list})"
        else:
            _entry = _cfg["name"]
        _version_parts.append(_entry)
        _agent_version_map[_a] = _entry
    agent_version_line = " &middot; ".join(_version_parts)

    # ------------------------------------------------------------------
    # Metric-filter CSS — generated from AGENT_CONFIG gradients.
    # Built as a plain string, interpolated into the f-string template
    # via {metric_filter_css}.
    # ------------------------------------------------------------------
    _METRIC_ORDER = ["solid", "average", "best", "ceiling"]
    _mf_parts: list[str] = []
    for _fi, _fkey in enumerate(_METRIC_ORDER):
        # Hide segments above the selected metric level
        for _above in _METRIC_ORDER[_fi + 1:]:
            _mf_parts.append(
                f".chart-area.metric-filter-{_fkey} .segment-{_above}"
                f" {{ display: none !important; }}"
            )
        # Hide non-matching labels
        _mf_parts.append(
            f'.chart-area.metric-filter-{_fkey} .seg-label:not([data-metric="{_fkey}"])'
            f" {{ display: none !important; }}"
        )
        # Border-radius on the new topmost visible segment
        if _fkey == "solid":
            _mf_parts.append(
                f".chart-area.metric-filter-solid .segment-solid"
                f" {{ border-radius: 8px !important; }}"
            )
        elif _fkey != "ceiling":
            _mf_parts.append(
                f".chart-area.metric-filter-{_fkey} .segment-{_fkey}"
                f" {{ border-radius: 8px 8px 0 0 !important; }}"
            )
        # Per-agent color overrides: apply the original full-range gradient
        # to the .bar-segments container and make individual segments
        # transparent.  The container renders one seamless gradient across
        # the whole bar — no per-segment restart, full 3D look.
        for _agent, _cfg in AGENT_CONFIG.items():
            _grad, _shad = _cfg["gradient"][_fkey]
            _mf_parts.append(
                f'.chart-area.metric-filter-{_fkey} .bar[data-agent="{_agent}"]'
                f" .bar-segments {{ background: {_grad};"
                f" box-shadow: {_shad},"
                f" inset 0 1px 0 rgba(255,255,255,0.15),"
                f" inset 0 -1px 0 rgba(0,0,0,0.2); }}"
            )
    # Hide single-run bars when any metric filter is active (metrics are meaningless for 1R)
    _mf_parts.append(
        '.chart-area[class*="metric-filter"] .bar-wrapper[data-runs="1"]'
        ' { display: none !important; }'
    )
    metric_filter_css = "\n".join(_mf_parts)

    # ------------------------------------------------------------------
    # Runs-table CSS — plain string, interpolated via {runs_table_css}.
    # ------------------------------------------------------------------
    runs_table_css = """
/* Run details table */
.runs-details {
    margin: 20px 0 0;
    padding: 18px 28px;
    background: rgba(26,28,31,0.8);
    border: 1px solid #2E3338;
    border-radius: 12px;
}
.runs-details summary {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #FFCC33;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
}
.runs-details summary:hover { opacity: 0.85; }
.runs-table-wrap {
    overflow-x: auto;
    margin-top: 16px;
}
.runs-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    white-space: nowrap;
}
.runs-table th {
    position: sticky;
    top: 0;
    background: #22262A;
    color: #9BA1A6;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border-bottom: 2px solid #2E3338;
}
.runs-table td {
    padding: 6px 10px;
    color: #c9d1d9;
    border-bottom: 1px solid rgba(46,51,56,0.6);
}
.runs-table td.n {
    text-align: right;
    font-variant-numeric: tabular-nums;
}
.runs-table tbody tr:nth-child(even) {
    background: rgba(46,51,56,0.25);
}
.runs-table tbody tr:hover {
    background: rgba(255,204,51,0.06);
}
.runs-table th::after {
    display: inline-block;
    width: 1em;
    margin-left: 2px;
    text-align: center;
    content: '';
    vertical-align: middle;
}
.runs-table th[data-sort='asc']::after { content: '\\25B2'; color: #FFCC33; }
.runs-table th[data-sort='desc']::after { content: '\\25BC'; color: #FFCC33; }
"""

    # Build runs table HTML
    runs_table_html = _build_runs_table_html(runs or [])

    # ------------------------------------------------------------------
    # JavaScript for interactivity
    # Defined as regular Python strings to avoid f-string brace escaping.
    # Interpolated into the HTML template via {all_js}.
    # ------------------------------------------------------------------
    _agent_ver_js_entries = []
    for _ak, _av in _agent_version_map.items():
        _agent_ver_js_entries.append(f"        '{_ak}': '{_av}'")
    _agent_versions_js = (
        "    var agentVersions = {\n"
        + ",\n".join(_agent_ver_js_entries)
        + "\n    };"
    )

    agent_toggle_js = """(function() {
AGENT_VERSIONS_PLACEHOLDER
    var activeAgent = null;
    var agentLegends = document.querySelectorAll('.legend-agent');
    var barWrappers = document.querySelectorAll('.bar-wrapper');
    var modelGroups = document.querySelectorAll('.model-group');
    var modelsRow = document.querySelector('.models-row');
    var versionLine = document.getElementById('agentVersionLine');
    var versionLineDefault = versionLine ? versionLine.innerHTML : '';

    agentLegends.forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            var agent = null;
            el.classList.forEach(function(cls) {
                if (cls.indexOf('legend-agent-') === 0 && cls !== 'legend-agent') {
                    agent = cls.replace('legend-agent-', '');
                }
            });
            if (!agent) return;

            if (activeAgent === agent) {
                activeAgent = null;
                agentLegends.forEach(function(l) { l.classList.remove('dimmed'); });
                barWrappers.forEach(function(b) { b.classList.remove('agent-hidden'); });
                modelGroups.forEach(function(g) { g.classList.remove('model-hidden'); });
                if (modelsRow) modelsRow.classList.remove('agent-filtered');
                if (versionLine) versionLine.innerHTML = versionLineDefault;
                if (window.updateChartWidth) window.updateChartWidth();
            } else {
                activeAgent = agent;
                agentLegends.forEach(function(l) {
                    l.classList.toggle('dimmed', !l.classList.contains('legend-agent-' + agent));
                });
                barWrappers.forEach(function(b) {
                    b.classList.toggle('agent-hidden', b.getAttribute('data-agent') !== agent);
                });
                modelGroups.forEach(function(g) {
                    var hasAgent = g.querySelector('.bar-wrapper[data-agent="' + agent + '"]') !== null;
                    g.classList.toggle('model-hidden', !hasAgent);
                });
                if (modelsRow) modelsRow.classList.add('agent-filtered');
                if (versionLine && agentVersions[agent]) {
                    versionLine.innerHTML = agentVersions[agent];
                }
                if (window.updateChartWidth) window.updateChartWidth();
            }
        });
    });
})();""".replace("AGENT_VERSIONS_PLACEHOLDER", _agent_versions_js)

    metric_filter_js = """(function() {
    var activeMetric = null;
    var chartArea = document.querySelector('.chart-area');
    var metricLegends = document.querySelectorAll('.legend-metric');
    var allLabels = document.querySelectorAll('.seg-label');

    // Save the collision-avoided positions on first load
    allLabels.forEach(function(lbl) {
        lbl.setAttribute('data-nudged-bottom', lbl.style.bottom);
    });

    function adjustLabelPositions(metric) {
        allLabels.forEach(function(lbl) {
            if (metric) {
                // Snap visible label to true Y position
                if (lbl.getAttribute('data-metric') === metric) {
                    lbl.style.bottom = lbl.getAttribute('data-true-bottom') + 'px';
                }
            } else {
                // Restore collision-avoided position
                lbl.style.bottom = lbl.getAttribute('data-nudged-bottom');
            }
        });
    }

    function adjustTopLabels(metric) {
        document.querySelectorAll('.bar-wrapper').forEach(function(wrapper) {
            var barInner = wrapper.querySelector('.bar-inner');
            var topLabel = wrapper.querySelector('.bar-top-label');
            if (!barInner || !topLabel) return;
            if (metric) {
                var ceilH = parseFloat(barInner.getAttribute('data-h-ceiling'));
                var metricH = parseFloat(barInner.getAttribute('data-h-' + metric));
                topLabel.style.transform = 'translateY(' + (ceilH - metricH) + 'px)';
            } else {
                topLabel.style.transform = '';
            }
        });
    }

    metricLegends.forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            var metric = el.getAttribute('data-metric');
            if (!metric) return;

            if (activeMetric === metric) {
                activeMetric = null;
                chartArea.className = chartArea.className.replace(/metric-filter-\\w+/g, '').trim();
                metricLegends.forEach(function(l) {
                    l.classList.remove('active');
                    l.classList.remove('dimmed');
                });
                adjustLabelPositions(null);
                adjustTopLabels(null);
            } else {
                activeMetric = metric;
                chartArea.className = chartArea.className.replace(/metric-filter-\\w+/g, '').trim();
                chartArea.classList.add('metric-filter-' + metric);
                metricLegends.forEach(function(l) {
                    var isActive = l.getAttribute('data-metric') === metric;
                    l.classList.toggle('active', isActive);
                    l.classList.toggle('dimmed', !isActive);
                });
                adjustLabelPositions(metric);
                adjustTopLabels(metric);
            }
        });
    });
})();"""

    unit_toggle_js = """(function() {
    var toggle = document.getElementById('unitToggle');
    if (!toggle) return;
    toggle.addEventListener('click', function() {
        var mode = toggle.getAttribute('data-mode');
        var newMode = (mode === 'pct') ? 'abs' : 'pct';
        toggle.setAttribute('data-mode', newMode);
        toggle.textContent = (newMode === 'pct') ? '%' : '#';
        var attr = 'data-h-' + newMode;
        // Swap bar-inner total heights
        document.querySelectorAll('.bar-inner').forEach(function(el) {
            var h = el.getAttribute(attr);
            if (h) el.style.height = h + 'px';
        });
        // Swap segment heights
        document.querySelectorAll('.segment').forEach(function(el) {
            var h = el.getAttribute(attr);
            if (h) el.style.height = h + 'px';
        });
        // Swap label text
        document.querySelectorAll('.seg-pct').forEach(function(el) {
            el.textContent = el.getAttribute('data-' + newMode);
        });
        // Swap label positions
        document.querySelectorAll('.seg-label').forEach(function(el) {
            var b = el.getAttribute('data-bottom-' + newMode);
            if (b) el.style.bottom = b + 'px';
        });
        // Swap y-axis ticks
        document.querySelectorAll('.y-tick').forEach(function(el) {
            el.textContent = el.getAttribute('data-' + newMode);
        });
    });
})();"""

    table_sort_js = """(function() {
    var table = document.querySelector('.runs-table');
    if (!table) return;
    var thead = table.tHead;
    var tbody = table.tBodies[0];
    if (!thead || !tbody) return;
    var headers = thead.rows[0].cells;
    // Initial state: Date column (0) descending — matches Python sort order
    var sortCol = 0;
    var sortAsc = false;

    function parseVal(text) {
        var s = text.replace(/^\\$/, '').replace(/[%s]$/, '').trim();
        var m = s.match(/^([\\d.]+)([MK])$/i);
        if (m) {
            var n = parseFloat(m[1]);
            return m[2].toUpperCase() === 'M' ? n * 1e6 : n * 1e3;
        }
        m = s.match(/^(\\d+)h(\\d+)m$/);
        if (m) return parseInt(m[1]) * 60 + parseInt(m[2]);
        // Only treat as number if the ENTIRE string is numeric
        // (avoids parseFloat("2026-03-01 13:43") → 2026)
        if (/^-?\\d+(\\.\\d+)?$/.test(s)) return parseFloat(s);
        return null;
    }

    function cmp(a, b, col) {
        var at = a.cells[col].textContent.trim();
        var bt = b.cells[col].textContent.trim();
        var an = parseVal(at);
        var bn = parseVal(bt);
        if (an !== null && bn !== null) return an - bn;
        return at.toLowerCase().localeCompare(bt.toLowerCase());
    }

    for (var i = 0; i < headers.length; i++) {
        (function(col) {
            headers[col].style.cursor = 'pointer';
            headers[col].addEventListener('click', function() {
                if (sortCol === col) {
                    sortAsc = !sortAsc;
                } else {
                    sortCol = col;
                    sortAsc = true;
                }
                for (var j = 0; j < headers.length; j++) {
                    headers[j].removeAttribute('data-sort');
                }
                headers[col].setAttribute('data-sort', sortAsc ? 'asc' : 'desc');
                var rows = Array.prototype.slice.call(tbody.rows);
                rows.sort(function(a, b) {
                    var r = cmp(a, b, col);
                    return sortAsc ? r : -r;
                });
                rows.forEach(function(row) { tbody.appendChild(row); });
            });
        })(i);
    }
})();"""

    model_toggle_js = """(function() {
    var hiddenModels = {};
    var modelBtns = document.querySelectorAll('.model-btn');
    var modelGroups = document.querySelectorAll('.model-group');
    var modelsRow = document.querySelector('.models-row');
    var modelBar = document.querySelector('.model-bar');
    var chartArea = document.querySelector('.chart-area');
    var dragSrc = null;

    // Recalculate chart min-width based on visible model groups
    window.updateChartWidth = function() {
        if (!chartArea) return;
        var totalW = 0, n = 0;
        modelGroups.forEach(function(g) {
            if (!g.classList.contains('model-hidden') && !g.classList.contains('model-hidden-user')) {
                totalW += parseInt(g.getAttribute('data-width')) || 0;
                n++;
            }
        });
        if (n > 0) totalW += (n - 1) * 48 + n * 40;
        chartArea.style.minWidth = totalW + 'px';
    };

    // Toggle visibility
    modelBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (btn.getAttribute('data-just-dragged') === 'true') {
                btn.removeAttribute('data-just-dragged');
                return;
            }
            var model = btn.getAttribute('data-model');
            if (!model) return;
            if (hiddenModels[model]) {
                delete hiddenModels[model];
                btn.classList.remove('dimmed');
            } else {
                hiddenModels[model] = true;
                btn.classList.add('dimmed');
            }
            modelGroups.forEach(function(g) {
                g.classList.toggle('model-hidden-user', !!hiddenModels[g.getAttribute('data-model')]);
            });
            syncVisToggle();
            window.updateChartWidth();
        });
    });

    // Drag to reorder
    modelBtns.forEach(function(btn) {
        btn.addEventListener('dragstart', function(e) {
            dragSrc = btn;
            btn.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', btn.getAttribute('data-model'));
        });
        btn.addEventListener('dragend', function() {
            btn.classList.remove('dragging');
            btn.setAttribute('data-just-dragged', 'true');
            setTimeout(function() { btn.removeAttribute('data-just-dragged'); }, 50);
            modelBtns.forEach(function(b) { b.classList.remove('drag-over'); });
            dragSrc = null;
        });
        btn.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (btn !== dragSrc) btn.classList.add('drag-over');
        });
        btn.addEventListener('dragleave', function() { btn.classList.remove('drag-over'); });
        btn.addEventListener('drop', function(e) {
            e.preventDefault();
            btn.classList.remove('drag-over');
            if (!dragSrc || dragSrc === btn) return;
            var allBtns = Array.prototype.slice.call(modelBar.querySelectorAll('.model-btn'));
            var srcIdx = allBtns.indexOf(dragSrc);
            var tgtIdx = allBtns.indexOf(btn);
            if (srcIdx < tgtIdx) {
                modelBar.insertBefore(dragSrc, btn.nextSibling);
            } else {
                modelBar.insertBefore(dragSrc, btn);
            }
            // Reorder chart model groups to match button order
            Array.prototype.slice.call(modelBar.querySelectorAll('.model-btn')).forEach(function(b) {
                var group = modelsRow.querySelector('.model-group[data-model="' + b.getAttribute('data-model') + '"]');
                if (group) modelsRow.appendChild(group);
            });
        });
    });

    // Show/hide all toggle
    var visToggle = document.getElementById('modelVisToggle');
    function syncVisToggle() {
        if (visToggle) visToggle.classList.toggle('dimmed', Object.keys(hiddenModels).length > 0);
    }
    if (visToggle) {
        visToggle.addEventListener('click', function() {
            var allVisible = Object.keys(hiddenModels).length === 0;
            if (allVisible) {
                // Hide all
                modelBtns.forEach(function(btn) {
                    var model = btn.getAttribute('data-model');
                    hiddenModels[model] = true;
                    btn.classList.add('dimmed');
                });
            } else {
                // Show all
                hiddenModels = {};
                modelBtns.forEach(function(btn) { btn.classList.remove('dimmed'); });
            }
            modelGroups.forEach(function(g) {
                g.classList.toggle('model-hidden-user', !!hiddenModels[g.getAttribute('data-model')]);
            });
            syncVisToggle();
            window.updateChartWidth();
        });
    }
})();"""

    all_js = (agent_toggle_js + "\n" + metric_filter_js + "\n"
              + unit_toggle_js + "\n" + model_toggle_js + "\n" + table_sort_js)

    ch = CHART_HEIGHT  # alias
    ppx = PX_PER_PCT

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WolfBench</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700;800&family=Source+Serif+4:wght@600;700;800&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Source Sans 3', -apple-system, sans-serif;
    background: #1A1C1F;
    color: #e6edf3;
    min-height: 100vh;
    padding: 48px 32px;
}}

.container {{
    margin: 0 auto;
}}

/* Header */
.header {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-bottom: 8px;
}}

.header-logo {{
    flex-shrink: 0;
}}

h1 {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFCC33;
}}

.subtitle {{
    text-align: center;
    color: #9BA1A6;
    font-size: 1rem;
    margin-bottom: 28px;
    font-weight: 500;
}}

/* Preview note */
.preview-note {{
    max-width: 680px;
    margin: 0 auto 28px;
    padding: 14px 20px;
    background: rgba(46,51,56,0.4);
    border: 1px solid #2E3338;
    border-left: 3px solid #FFCC33;
    border-radius: 6px;
    color: #9BA1A6;
    font-size: 0.92rem;
    line-height: 1.6;
}}
.preview-note strong {{
    color: #e6edf3;
}}

/* Hook / intro */
.hook {{
    text-align: center;
    max-width: 680px;
    margin: 0 auto 36px;
}}
.hook-headline {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 800;
    color: #FFCC33;
    margin-bottom: 10px;
}}
.hook p {{
    color: #9BA1A6;
    font-size: 0.95rem;
    line-height: 1.65;
}}
.hook strong {{ color: #e6edf3; }}


/* Legend */
.legend {{
    position: relative;
    z-index: 10;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
    margin-bottom: 8px;
    padding: 18px 28px;
    background: rgba(26,28,31,0.8);
    border: 1px solid #2E3338;
    border-radius: 12px;
    backdrop-filter: blur(8px);
}}

.legend-agent {{
    display: inline-flex;
    align-items: center;
    padding: 7px 14px 6px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.95rem;
    line-height: 1;
    cursor: pointer;
    user-select: none;
    transition: opacity 0.25s ease, transform 0.15s ease;
}}
.legend-agent:hover {{ transform: translateY(-1px); }}
.legend-agent.dimmed {{ opacity: 0.3; }}
.legend-agent-terminus-2  {{ background: rgba(39,174,96,0.2); color: #58d68d; border: 1px solid rgba(39,174,96,0.3); }}
.legend-agent-openclaw    {{ background: rgba(231,76,60,0.2);  color: #f1948a; border: 1px solid rgba(231,76,60,0.3); }}
.legend-agent-claude-code {{ background: rgba(230,126,34,0.2); color: #f0b27a; border: 1px solid rgba(230,126,34,0.3); }}

.legend-toggle {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    padding: 7px 0 6px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.95rem;
    line-height: 1;
    cursor: pointer;
    user-select: none;
    background: rgba(46,51,56,0.5);
    border: 1px solid #2E3338;
    color: #FFCC33;
    transition: opacity 0.25s ease, transform 0.15s ease, border-color 0.2s ease;
}}
.legend-toggle:hover {{ transform: translateY(-1px); border-color: #FFCC33; background: rgba(255,204,51,0.1); }}

.legend-sep {{
    width: 1px;
    background: #2E3338;
    margin: 0 6px;
}}

.legend-metric {{
    display: inline-flex;
    align-items: center;
    padding: 7px 12px 6px;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    background: rgba(46,51,56,0.5);
    border: 1px solid #2E3338;
    line-height: 1;
    cursor: pointer;
    user-select: none;
    transition: opacity 0.25s ease, transform 0.15s ease, border-color 0.2s ease;
}}
.legend-metric:hover {{ transform: translateY(-1px); }}
.legend-metric.active {{ border-color: #FFCC33; background: rgba(255,204,51,0.1); }}
.legend-metric.dimmed {{ opacity: 0.3; }}
.legend-metric small {{ color: #6B7280; }}

/* Model bar — toggle visibility and drag to reorder */
.model-bar {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 48px;
    padding: 14px 28px;
    background: rgba(26,28,31,0.8);
    border: 1px solid #2E3338;
    border-radius: 12px;
    backdrop-filter: blur(8px);
}}
.model-btn {{
    display: inline-flex;
    align-items: center;
    padding: 7px 14px 6px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.92rem;
    line-height: 1;
    cursor: grab;
    user-select: none;
    background: rgba(46,51,56,0.5);
    border: 1px solid #2E3338;
    color: #e6edf3;
    transition: opacity 0.25s ease, transform 0.15s ease, border-color 0.2s ease;
}}
.model-btn:hover {{
    transform: translateY(-1px);
    border-color: #FFCC33;
    background: rgba(255,204,51,0.08);
}}
.model-btn.dimmed {{ opacity: 0.3; }}
.model-btn:active {{ cursor: grabbing; }}
.model-btn.dragging {{ opacity: 0.5; transform: scale(0.95); }}
.model-btn.drag-over {{ border-color: #FFCC33; background: rgba(255,204,51,0.15); }}
#modelVisToggle.dimmed {{ opacity: 0.5; filter: grayscale(1); }}

/* Chart wrapper — flex layout with sticky y-axis */
.chart-wrapper {{
    display: flex;
    align-items: flex-start;
    margin-bottom: 28px;
}}
.y-axis {{
    width: 60px;
    flex-shrink: 0;
    position: relative;
    height: {ch}px;
    margin-top: 54px;
}}
.chart-scroll {{
    flex: 1;
    overflow-x: auto;
    overflow-y: hidden;
    min-width: 0;
    padding-top: 54px;
    padding-bottom: 30px;
}}
.chart-area {{
    position: relative;
    height: {ch}px;
    min-width: {chart_min_w}px;
}}

/* Y-axis ticks — positioned absolutely relative to chart-area */
.y-tick {{
    position: absolute;
    right: 4px;
    font-size: 0.85rem;
    color: #9BA1A6;
    font-weight: 500;
    transform: translateY(50%);
    text-align: right;
    width: 48px;
}}

/* Grid lines */
.grid-line {{
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background: #2E3338;
    pointer-events: none;
}}

/* Models container — fills chart area, bars anchored to bottom */
.models-row {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: {ch}px;
    display: flex;
    justify-content: space-evenly;
    gap: 24px;
}}
.models-row.agent-filtered {{
    justify-content: center;
    gap: 80px;
}}

.model-group {{
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
}}
.model-group.model-hidden {{
    display: none;
}}
.model-group.model-hidden-user {{
    display: none;
}}

.bars-row {{
    display: flex;
    gap: 8px;
    align-items: flex-end;
    justify-content: center;
    margin-top: auto;
}}

.model-label {{
    position: absolute;
    top: -44px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 1.1rem;
    font-weight: 700;
    color: #e6edf3;
    text-align: center;
    letter-spacing: -0.01em;
    width: max-content;
    max-width: calc(100% + 40px);
    overflow-wrap: break-word;
    line-height: 1.2;
}}

/* Bar */
.bar-wrapper {{
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    transition: opacity 0.3s ease;
}}
.bar-wrapper.agent-hidden {{
    display: none;
}}

.bar-top-label {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #e6edf3;
    text-align: center;
    margin-bottom: 14px;
    line-height: 1.2;
    transition: transform 0.3s ease;
}}
.version-label {{
    font-size: 0.75rem;
    font-weight: 500;
    color: #9BA1A6;
}}
.bar-bottom-label {{
    position: absolute;
    bottom: -22px;
    left: 50%;
    transform: translateX(-50%);
    text-align: center;
    white-space: nowrap;
}}
.run-count {{
    font-size: 0.7rem;
    font-weight: 500;
    color: #6B7280;
}}
.bar-link {{
    text-decoration: none;
    display: block;
    cursor: pointer;
}}
.bar-link:hover .bar {{
    filter: brightness(1.15);
    transition: filter 0.2s;
}}

.bar {{
    position: relative;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 0 1px rgba(255,255,255,0.1);
}}


.bar-inner {{
    position: relative;
    width: 100%;
}}

.bar-segments {{
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 100%;
    width: 100%;
    border-radius: 8px 8px 4px 4px;
    overflow: hidden;
}}

.bar-labels {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 100%;
    pointer-events: none;
}}

/* Segment */
.segment {{
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(0,0,0,0.2);
    transition: background 0.3s ease, box-shadow 0.3s ease;
}}

.segment:first-child {{
    border-radius: 8px 8px 0 0;
}}
.segment:last-child {{
    border-radius: 0 0 4px 4px;
    border-bottom: none;
}}

/* Metallic shine overlay */
.segment-shine {{
    position: absolute;
    top: 0; left: 12%; bottom: 0;
    width: 28%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.13), transparent);
    pointer-events: none;
}}

.seg-label {{
    position: absolute;
    left: 50%;
    transform: translateX(-50%) translateY(50%);
    display: inline-flex;
    align-items: baseline;
    gap: 1px;
    font-size: 0.85rem;
    font-weight: 800;
    color: white;
    text-shadow:
        -1px -1px 0 rgba(0,0,0,0.8),
         1px -1px 0 rgba(0,0,0,0.8),
        -1px  1px 0 rgba(0,0,0,0.8),
         1px  1px 0 rgba(0,0,0,0.8),
         0 0 6px rgba(0,0,0,0.6);
    z-index: 2;
    white-space: nowrap;
    letter-spacing: 0.02em;
}}
.seg-sym {{
    display: inline-block;
    width: 1em;
    text-align: center;
    flex-shrink: 0;
}}
.seg-pct {{
    text-align: right;
}}

/* Footer */
.footer {{
    text-align: center;
    margin-top: 40px;
    color: #4B5563;
    font-size: 0.8rem;
}}

/* About section */
.about {{
    max-width: 760px;
    margin: 48px auto 0;
}}
.about h2 {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFCC33;
    margin-bottom: 12px;
}}
.about h3 {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #e6edf3;
    margin-top: 28px;
    margin-bottom: 8px;
}}
.about p {{
    color: #c9d1d9;
    font-size: 0.95rem;
    line-height: 1.7;
    margin-bottom: 12px;
}}
.about strong {{ color: #e6edf3; }}
.about em {{ color: #10BFCC; font-style: italic; }}
.about ul {{
    color: #c9d1d9;
    font-size: 0.95rem;
    line-height: 1.7;
    margin: 8px 0 16px 20px;
}}
.about li {{ margin-bottom: 4px; }}
.about a {{
    color: #FFCC33;
    text-decoration: none;
    border-bottom: 1px solid rgba(255,204,51,0.3);
}}
.about a:hover {{ border-bottom-color: #FFCC33; }}
.about .tagline a:has(> .avatar) {{
    border-bottom: none;
    line-height: 0;
}}
.about .tagline {{
    color: #9BA1A6;
    font-style: italic;
    font-size: 0.95rem;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.about .tagline span {{
    flex: 1;
}}
.about .tagline .avatar {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    flex-shrink: 0;
}}
.about .metric-block {{
    background: rgba(46,51,56,0.4);
    border: 1px solid #2E3338;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.about .metric-block h3 {{
    margin-top: 0;
    margin-bottom: 4px;
    font-size: 1.05rem;
}}
.about .metric-block p {{ margin-bottom: 6px; }}
.about .metric-block p:last-child {{ margin-bottom: 0; }}
.about .spread-list {{ margin-top: 12px; }}
.about .spread-list li {{
    padding: 4px 0;
}}
.about .build-info {{
    color: #6B7280;
    font-size: 0.85rem;
    margin-top: 32px;
    padding-top: 20px;
    border-top: 1px solid #2E3338;
    text-align: center;
}}

/* Metric-filter overrides (generated from AGENT_CONFIG gradients) */
.chart-area[class*="metric-filter"] .bar {{
    box-shadow: none !important;
}}
.chart-area[class*="metric-filter"] .bar-segments {{
    height: auto;
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
}}
.chart-area[class*="metric-filter"] .segment {{
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
}}
.chart-area[class*="metric-filter"] .segment-shine {{
    display: none !important;
}}
{metric_filter_css}
{runs_table_css}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <img class="header-logo" src="data:image/png;base64,{logo_b64}" alt="Weights &amp; Biases by CoreWeave" height="48">
        <h1>WolfBench ({chart_date or date.today().isoformat()})</h1>
    </div>
    <p class="subtitle">Wolfram Ravenwolf&rsquo;s Four-Metric Framework &middot; based on Terminal-Bench 2.0{' &middot; min ' + str(min_runs) + ' runs' if min_runs > 1 else ''}</p>

    <div class="hook">
        <div class="hook-headline">One score is not enough.<br>Because performance is a distribution, not a point.</div>
        <p>Most benchmarks report just a single average. <strong>WolfBench</strong> shows four metrics: the <strong>rock-solid base</strong> you can always count on, the <strong>average</strong> you can expect, the <strong>best</strong> a single run achieved, and the <strong>ceiling</strong> of what&rsquo;s theoretically possible. The spread between them tells you how consistent &ndash; or how unpredictable &ndash; an AI agent really is.<br><a href="#about" style="color:#FFCC33; text-decoration:none; border-bottom:1px solid rgba(255,204,51,0.3);">Learn&nbsp;more&nbsp;&darr;</a></p>
    </div>

    <div class="legend">
        <span class="legend-toggle" id="unitToggle" data-mode="pct">%</span>
        <div class="legend-sep"></div>
        {"".join(legend_agents)}
        <div class="legend-sep"></div>
        {"".join(legend_metrics)}
    </div>

    <div class="model-bar">
        <span class="legend-toggle" id="modelVisToggle" title="Show/hide all models">&#x1F441;</span>
        <div class="legend-sep"></div>
        {"".join(model_bar_buttons)}
    </div>

    <div class="chart-wrapper">
        <div class="y-axis">
            {"".join(f'<span class="y-tick" style="bottom: {v * ppx}px;" data-pct="{v}%" data-abs="{round(v / 100 * TOTAL_TASKS)}">{v}%</span>' for v in range(0, 101, 10))}
        </div>
        <div class="chart-scroll">
            <div class="chart-area">
                {"".join(f'<div class="grid-line" style="bottom: {v * ppx}px;"></div>' for v in range(0, 101, 10))}

                <div class="models-row">
                    {"".join(model_groups_html)}
                </div>
            </div>
        </div>
    </div>

    <p class="footer">Terminal-Bench 2.0 &middot; 4 CPUs, 8 GB RAM, 10 GB Storage per task<br><span id="agentVersionLine">{agent_version_line}</span></p>

    {runs_table_html}

    <div class="about" id="about">
        <h2>About WolfBench</h2>
        <p class="tagline"><a href="https://x.com/WolframRvnwlf"><img class="avatar" src="data:image/jpeg;base64,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" alt="Wolfram Ravenwolf"></a><span>by <a href="https://x.com/WolframRvnwlf">Wolfram Ravenwolf</a> &ndash; who evaluates models for breakfast, builds agents at night, and preaches AI usefulness all day long.</span></p>

        <blockquote class="preview-note">
            <strong>Welcome to WolfBench &ndash; we&rsquo;re just getting started.</strong> What you see here is an early preview with only a handful of models and agents tested so far. I&rsquo;m continuously expanding the lineup, running fresh evals, and sharing interesting findings and insights along the way. Watch this space.
        </blockquote>

        <p>AI agents are becoming essential tools. Every week, a new model comes out and claims to be &ldquo;the best at coding&rdquo; or &ldquo;SOTA on agentic tasks.&rdquo; But what does that actually mean for you &ndash; the person who&rsquo;s going to throw real work at these things?</p>
        <p><strong>A single score tells you almost nothing.</strong></p>
        <p>Most benchmarks give you one number: &ldquo;Model X scored 42% on Benchmark Y.&rdquo; Great. But can you <em>rely</em> on it? Was that a lucky run? Would it score the same tomorrow? What&rsquo;s the floor &ndash; the tasks it <em>always</em> nails? What&rsquo;s the ceiling &ndash; what it <em>could</em> do if the stars align?</p>
        <p><strong>WolfBench</strong> exists because I got tired of incomplete leaderboards. I wanted to know which model, which harness, and which settings actually deliver the best results on real agentic tasks &ndash; not just on paper, but in practice, consistently, across multiple runs.</p>

        <h3>What is it?</h3>
        <p><strong>WolfBench</strong> is an evaluation framework built on top of Terminal-Bench 2.0, a popular agentic benchmark consisting of 89 diverse real-world tasks. These aren&rsquo;t just coding puzzles. They span the kind of work you&rsquo;d actually ask an AI agent to do:</p>
        <ul>
            <li><strong>System administration:</strong> headless terminal interaction, Git server configuration, Nginx request logging</li>
            <li><strong>DevOps &amp; infrastructure:</strong> package distribution search, database WAL recovery, PyPI server setup</li>
            <li><strong>Security:</strong> code vulnerability fixes, 7z hash cracking, ELF binary extraction, Git leak recovery</li>
            <li><strong>Data &amp; ML ops:</strong> financial document processing, HuggingFace model inference, scientific stack modernization</li>
            <li><strong>Problem solving:</strong> constraint scheduling, adaptive rejection sampling, concurrent task cancellation</li>
        </ul>
        <p>The key word is <em>agentic</em>: these tasks require the model to plan, execute shell commands, inspect results, debug failures, and iterate &ndash; just like a human developer or sysadmin would. No multiple-choice shortcuts. No toy puzzles. Real work in real sandboxed environments.</p>

        <h3>Why WolfBench is different</h3>
        <ul>
            <li><strong>Four-metric framework:</strong> Instead of a single average score, I report four complementary metrics that together paint a far more complete picture of what an AI agent can actually do.</li>
            <li><strong>Uniform conditions:</strong> Instead of Terminal-Bench 2.0&rsquo;s default task-specific timeouts and varying sandbox resources, every task in a run gets the same timeout and identical sandbox resources. This ensures scores reflect model and agent capability &ndash; not whether an inference endpoint was temporarily overloaded or a sandbox ran out of memory.</li>
            <li><strong>Multi-harness comparison:</strong> Same model, different agent harnesses. Same harness, different models. Different timeouts, concurrency levels, thinking modes. The goal is to understand <em>what matters</em> &ndash; not just <em>what scored highest in one particular instance</em>.</li>
            <li><strong>Multi-run methodology:</strong> A single run is statistically meaningless &ndash; variance can swing results widely. I run 5+ replicates per configuration to get stable, trustworthy numbers.</li>
            <li><strong>Transparency:</strong> Every run is collected, classified, and curated with full metadata: tokens consumed, cache hit rates, duration, timeout, concurrency, agent version, thinking mode, etc. Nothing is hidden.</li>
        </ul>

        <h3>The Four-Metric Framework</h3>
        <p><strong>Performance is a distribution, not a point.</strong> One number can&rsquo;t capture what an AI agent is truly capable of. Four numbers get a lot closer.</p>

        <div class="metric-block">
            <h3>&#9650; Ceiling: <em>What&rsquo;s theoretically possible?</em></h3>
            <p>The union of all tasks ever solved across all runs. If the model solved task A in run 3 and task B in run 5 (but never both in the same run), both count toward the ceiling.</p>
            <p>It tells you the theoretical maximum performance this model is <em>capable of</em> within a given harness and settings &ndash; even if no single run achieves it. It reveals variance-limited tasks: solvable, but not reliably.</p>
        </div>

        <div class="metric-block">
            <h3>&#9733; Best-of: <em>What&rsquo;s the peak in a single run?</em></h3>
            <p>The highest score from any individual run.</p>
            <p>This is the &ldquo;marketing number&rdquo; &ndash; but with context. The closer the best-of is to the average, the more <em>consistent</em> the model performs. A large gap between best-of and average means you&rsquo;re rolling dice every time you run it.</p>
        </div>

        <div class="metric-block">
            <h3>&empty; Average: <em>What can you normally expect?</em></h3>
            <p>The mean score across all valid runs (e.g., 5 or more replicates).</p>
            <p>This is the most commonly reported metric &ndash; and it <em>is</em> useful, but only with enough runs to be stable. With a single run? It&rsquo;s a coin flip.</p>
        </div>

        <div class="metric-block">
            <h3>&#9632; Solid: <em>What does it always get right?</em></h3>
            <p>Tasks that the model solves across all runs &ndash; the rock-solid base with zero variance.</p>
            <p>The higher the solid base, the more <em>dependable</em> the agent is. These are the tasks you can confidently delegate and expect success every time. A model with a high solid base and moderate average is often more reliable in practice than one with a high average but low solid base &ndash; because you know what you&rsquo;re getting.</p>
        </div>

        <h3>Reading the Chart</h3>
        <p>The four metrics stack vertically for each model/configuration. The <em>spread</em> between them tells you as much as the numbers themselves:</p>
        <ul class="spread-list">
            <li><strong>Tight spread</strong> (metrics close together) = consistent, predictable AI agent</li>
            <li><strong>Wide spread</strong> (big gap between solid and ceiling) = high variance, unreliable</li>
            <li><strong>High ceiling, low average</strong> = the model <em>can</em> do it, but usually doesn&rsquo;t &ndash; needs more runs or better settings</li>
            <li><strong>High solid, close to average</strong> = rock-solid workhorse you can count on</li>
        </ul>

        <h3>The Bottom Line</h3>
        <p>Performance is more complex than a single average score &ndash; and the decisions you make based on benchmarks deserve better data than that. <strong>WolfBench</strong> gives you four angles on every model and configuration, so you can form a more complete and realistic judgement of what an AI agent will actually deliver when you put it to work.</p>
        <p>Because at the end of the day, you don&rsquo;t just want to know which model <em>scored</em> the highest. You want to know which one you can <em>trust</em>.</p>

        <h3>What&rsquo;s Next</h3>
        <p>I will continuously add models and agents to the chart, publish the traces and evals on <a href="https://wandb.ai/">W&amp;B Weave</a>, and release regular blog posts detailing interesting and insightful findings.</p>
        <p>This benchmark offers enormous potential for discovery. For instance: Why does Sonnet currently outperform Opus so significantly with OpenClaw? How does Claude Code fare when running a GPT or Gemini model compared to running directly with Opus or Sonnet &ndash; or Codex with Claude or Gemini? Is a &ldquo;cheap&rdquo; model actually cost-effective if it consumes far more tokens than a more expensive alternative? How does quantization affect performance of local models in agentic tasks?</p>
        <p>So many possibilities for analysis &ndash; and for posting about it! <em>Stay tuned</em> &ndash; and if you want to be the first to know when new results come in, follow me on <a href="https://x.com/WolframRvnwlf">X</a> and <a href="https://www.linkedin.com/in/wolframravenwolf/">LinkedIn</a>.</p>

        <p class="build-info">Inference sponsored by <a href="https://www.coreweave.com/">CoreWeave</a>: The Essential Cloud for AI.<br>Sandbox compute by <a href="https://www.daytona.io/">Daytona</a> &ndash; Secure Infrastructure for Running AI-Generated Code.<br>Built with <a href="https://harborframework.com/">Harbor</a> for orchestration, <a href="https://www.tbench.ai/">Terminal-Bench 2.0</a> for tasks, and <a href="https://wandb.ai/">W&amp;B Weave</a> for tracking.<br>Charts and dashboards generated with <a href="https://marimo.io/">marimo</a> notebooks.</p>
    </div>
</div>
<script>
{all_js}
</script>
</body>
</html>'''

    out = output_path.with_suffix(".html")
    out.write_text(html)
    print(f"Saved: {out}")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="WolfBench Chart — HTML chart generator",
    )
    parser.add_argument(
        "-i", "--input", type=Path,
        default=Path(__file__).parent / "harbor_results.json",
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        default=Path(__file__).parent / "wolfbench",
    )
    parser.add_argument("--min-runs", type=int, default=1)
    parser.add_argument(
        "--date", type=str, default=None,
        help="Chart date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--weave-manifest", type=Path, default=None,
        help="Path to weave_manifest.json for embedding Weave links in bars.",
    )
    args = parser.parse_args()
    args.chart_date = args.date or date.today().isoformat()

    with open(args.input) as f:
        data = json.load(f)
    print(f"Loaded {data['n_runs']} valid runs from {args.input}")

    run_groups: dict[tuple[str, str, str, float | None], list[dict]] = defaultdict(list)
    agent_versions: dict[str, set[str]] = defaultdict(set)
    for r in data["runs"]:
        ver = r.get("agent_version") or "unknown"
        run_groups[(r["agent"], ver, r["model_display"], r.get("timeout_sec"))].append(r)
        if ver != "unknown":
            agent_versions[r["agent"]].add(ver)

    metrics = {}
    for key, runs in sorted(run_groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3] or 0)):
        m = compute_metrics(runs)
        if m:
            metrics[key] = m
            agent, ver, model, _timeout = key
            print(f"  {agent:>12} v{ver:<14} {model:>20}  {m['n_runs']}R  "
                  f"solid={m['solid_abs']:>2}  avg={m['average']}%  "
                  f"best={m['best']}%  ceil={m['ceiling_abs']:>2}")

    weave_urls = None
    if args.weave_manifest and args.weave_manifest.exists():
        try:
            import importlib
            _ww = importlib.import_module("wolfbench_weave")
            weave_urls = _ww.get_evaluation_urls(args.weave_manifest)
        except Exception as e:
            print(f"Warning: could not load weave manifest: {e}")

    generate_html(metrics, args.output, min_runs=args.min_runs,
                  agent_versions=dict(agent_versions),
                  chart_date=args.chart_date,
                  runs=data["runs"],
                  weave_urls=weave_urls)


if __name__ == "__main__":
    main()
