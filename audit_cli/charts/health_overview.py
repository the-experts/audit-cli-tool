from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_QG_COLOR = {"OK": "rgba(39,174,96,.25)", "ERROR": "rgba(192,57,43,.25)", "WARN": "rgba(243,156,18,.25)"}


def _fmt(v: Any, dec: int = 0) -> str:
    if v is None:
        return "-"
    return f"{v:.{dec}f}"


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    names = [p["name"][:40] for p in projects]
    statuses = [p.get("qg_status", "N/A") for p in projects]
    cell_colors = [_QG_COLOR.get(s, "white") for s in statuses]

    table = go.Figure(
        go.Table(
            columnwidth=[220, 110, 65, 110, 100, 90, 100, 100],
            header=dict(
                values=[
                    "<b>Project</b>",
                    "<b>Quality Gate</b>",
                    "<b>Bugs</b>",
                    "<b>Vulnerabilities</b>",
                    "<b>Code Smells</b>",
                    "<b>Coverage %</b>",
                    "<b>Duplication %</b>",
                    "<b>Lines of Code</b>",
                ],
                fill_color="#2c3e50",
                font=dict(color="white", size=12),
                align="left",
                height=38,
            ),
            cells=dict(
                values=[
                    names,
                    statuses,
                    [_fmt(p.get("bugs")) for p in projects],
                    [_fmt(p.get("vulnerabilities")) for p in projects],
                    [_fmt(p.get("code_smells")) for p in projects],
                    [_fmt(p.get("coverage"), 1) for p in projects],
                    [_fmt(p.get("duplicated_lines_density"), 1) for p in projects],
                    [_fmt(p.get("ncloc")) for p in projects],
                ],
                fill_color=[
                    ["white"] * len(projects),
                    cell_colors,
                    *[["white"] * len(projects)] * 6,
                ],
                align="left",
                font=dict(size=11),
                height=28,
            ),
        )
    )
    table.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=max(350, 70 + 28 * len(projects)),
    )

    bar = go.Figure()
    for metric, color, label in [
        ("bugs", "#e74c3c", "Bugs"),
        ("vulnerabilities", "#e67e22", "Vulnerabilities"),
        ("security_hotspots", "#9b59b6", "Security Hotspots"),
    ]:
        bar.add_trace(
            go.Bar(
                name=label,
                x=names,
                y=[p.get(metric) or 0 for p in projects],
                marker_color=color,
            )
        )
    bar.update_layout(
        barmode="group",
        xaxis_tickangle=-40,
        yaxis_title="Count",
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=20, b=120),
        height=420,
    )

    return [("Health Dashboard", table), ("Issues by Project", bar)]
