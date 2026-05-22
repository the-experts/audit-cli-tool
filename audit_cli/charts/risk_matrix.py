from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_QG_COLORS = {"OK": "#27ae60", "ERROR": "#e74c3c", "WARN": "#e67e22"}
_LOC_MIN, _LOC_MAX = 12, 55


def _marker_size(ncloc) -> float:
    loc = ncloc or 0
    if loc <= 0:
        return _LOC_MIN
    import math
    return min(_LOC_MAX, _LOC_MIN + math.log1p(loc) * 3)


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    fig = go.Figure()

    for qg_status, color in _QG_COLORS.items():
        group = [p for p in projects if p.get("qg_status") == qg_status]
        if not group:
            continue
        fig.add_trace(go.Scatter(
            x=[p.get("bugs") or 0 for p in group],
            y=[p.get("vulnerabilities") or 0 for p in group],
            mode="markers+text",
            name=qg_status,
            text=[p["name"][:28] for p in group],
            textposition="top center",
            textfont=dict(size=10),
            marker=dict(
                size=[_marker_size(p.get("ncloc")) for p in group],
                color=color,
                opacity=0.75,
                line=dict(color="white", width=1),
            ),
            customdata=[[p.get("ncloc") or 0, p.get("code_smells") or 0] for p in group],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Bugs: %{x}<br>"
                "Vulnerabilities: %{y}<br>"
                "LOC: %{customdata[0]:,}<br>"
                "Code Smells: %{customdata[1]:,}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Bugs",
        yaxis_title="Vulnerabilities",
        legend_title="Quality Gate",
        height=520,
        margin=dict(t=20, b=60, l=60, r=20),
    )
    return [("Risk Matrix — Bugs vs Vulnerabilities (size = LOC)", fig)]
