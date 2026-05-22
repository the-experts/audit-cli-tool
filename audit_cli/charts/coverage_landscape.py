import math
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_QG_MARKER_COLOR = {"OK": "#27ae60", "ERROR": "#e74c3c", "WARN": "#f39c12"}


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    valid = [p for p in projects if p.get("coverage") is not None and p.get("duplicated_lines_density") is not None]
    if not valid:
        fig = go.Figure()
        fig.update_layout(title="No coverage data available")
        return [("Coverage & Duplication Landscape", fig)]

    max_loc = max((p.get("ncloc") or 1 for p in valid), default=1)

    sizes = [max(8, 60 * math.sqrt((p.get("ncloc") or 1) / max_loc)) for p in valid]
    colors = [_QG_MARKER_COLOR.get(p.get("qg_status", ""), "#95a5a6") for p in valid]
    labels = [p["name"] for p in valid]
    hover = [
        f"<b>{p['name']}</b><br>"
        f"Coverage: {p['coverage']:.1f}%<br>"
        f"Duplication: {p['duplicated_lines_density']:.1f}%<br>"
        f"Lines: {int(p['ncloc'] or 0):,}<br>"
        f"QG: {p.get('qg_status','?')}"
        for p in valid
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[p["coverage"] for p in valid],
            y=[p["duplicated_lines_density"] for p in valid],
            mode="markers+text",
            text=labels,
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(size=sizes, color=colors, opacity=0.75, line=dict(width=1, color="white")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover,
        )
    )

    fig.add_shape(type="line", x0=80, x1=80, y0=0, y1=100, line=dict(dash="dot", color="#7f8c8d", width=1))
    fig.add_shape(type="line", x0=0, x1=100, y0=3, y1=3, line=dict(dash="dot", color="#7f8c8d", width=1))

    fig.add_annotation(x=95, y=1, text="✓ Good zone", showarrow=False, font=dict(color="#27ae60", size=11))
    fig.add_annotation(x=30, y=15, text="⚠ Risk zone", showarrow=False, font=dict(color="#e74c3c", size=11))

    for qg, color in _QG_MARKER_COLOR.items():
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=12, color=color),
                name=f"QG: {qg}",
            )
        )

    fig.update_layout(
        xaxis=dict(title="Test Coverage (%)", range=[-2, 102]),
        yaxis=dict(title="Code Duplication (%)", range=[-0.5, max(10, max(p["duplicated_lines_density"] for p in valid) + 1)]),
        height=550,
        margin=dict(t=20, b=60),
        legend=dict(orientation="h", y=1.08),
        showlegend=True,
    )

    return [("Coverage vs. Duplication Landscape (bubble size = lines of code)", fig)]
