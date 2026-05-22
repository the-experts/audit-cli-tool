from math import ceil
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_CATEGORIES = ["Reliability", "Security", "Maintainability", "Coverage", "No Duplication"]
_CATS_CLOSED = _CATEGORIES + [_CATEGORIES[0]]


def _scores(p: Dict[str, Any]) -> List[float]:
    def _rating(v):
        return max(0.0, (6 - v) * 20) if v is not None else 0.0

    return [
        _rating(p.get("reliability_rating")),
        _rating(p.get("security_rating")),
        _rating(p.get("sqale_rating")),
        min(100.0, float(p.get("coverage") or 0)),
        max(0.0, 100.0 - float(p.get("duplicated_lines_density") or 0)),
    ]


def _color(scores: List[float]) -> str:
    avg = sum(scores) / len(scores) if scores else 0
    if avg >= 70:
        return "#27ae60"
    if avg >= 45:
        return "#e67e22"
    return "#e74c3c"


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    if not projects:
        return []

    n = len(projects)
    cols = min(3, n)
    rows = ceil(n / cols)

    specs = [[{"type": "polar"}] * cols for _ in range(rows)]
    titles = [p["name"][:35] for p in projects] + [""] * (rows * cols - n)

    fig = make_subplots(
        rows=rows, cols=cols,
        specs=specs,
        subplot_titles=titles,
        horizontal_spacing=0.06,
        vertical_spacing=0.12,
    )

    for i, proj in enumerate(projects):
        row, col = divmod(i, cols)
        row, col = row + 1, col + 1
        s = _scores(proj)
        color = _color(s)
        fig.add_trace(
            go.Scatterpolar(
                r=s + [s[0]],
                theta=_CATS_CLOSED,
                fill="toself",
                line=dict(color=color),
                opacity=0.6,
                showlegend=False,
                name=proj["name"][:35],
            ),
            row=row, col=col,
        )

    fig.update_polars(radialaxis=dict(range=[0, 100], showticklabels=False, ticks=""))
    fig.update_layout(
        height=max(500, rows * 500),
        margin=dict(t=80, b=40, l=40, r=40),
    )

    return [("Project Quality Radars", fig)]
