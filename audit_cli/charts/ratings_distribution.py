from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_DIMENSIONS = [
    ("reliability_rating", "Reliability"),
    ("security_rating", "Security"),
    ("sqale_rating", "Maintainability"),
]
_RATINGS = ["A", "B", "C", "D", "E"]
_COLORS = ["#27ae60", "#82e0aa", "#e67e22", "#e74c3c", "#7b241c"]


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    counts: Dict[str, List[int]] = {label: [0] * 5 for _, label in _DIMENSIONS}
    for p in projects:
        for metric, label in _DIMENSIONS:
            v = p.get(metric)
            if v is not None:
                idx = int(v) - 1
                if 0 <= idx < 5:
                    counts[label][idx] += 1

    dim_labels = [label for _, label in _DIMENSIONS]
    fig = go.Figure()
    for j, (rating, color) in enumerate(zip(_RATINGS, _COLORS)):
        fig.add_trace(go.Bar(
            name=rating,
            x=dim_labels,
            y=[counts[label][j] for label in dim_labels],
            marker_color=color,
            text=[counts[label][j] or "" for label in dim_labels],
            textposition="inside",
        ))

    fig.update_layout(
        barmode="stack",
        yaxis_title="Number of Projects",
        legend_title="Rating",
        height=400,
        margin=dict(t=20, b=40, l=60, r=20),
    )
    return [("Ratings Distribution across Portfolio", fig)]
