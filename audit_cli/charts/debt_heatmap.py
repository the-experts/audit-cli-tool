from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_RATING_LABEL = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}
_DIMENSIONS = ["Maintainability", "Reliability", "Security"]
_DIM_METRIC = {
    "Maintainability": "sqale_rating",
    "Reliability": "reliability_rating",
    "Security": "security_rating",
}
_COLORSCALE = [
    [0.0, "#27ae60"],   # A
    [0.25, "#82e0aa"],  # B
    [0.5, "#f39c12"],   # C
    [0.75, "#e67e22"],  # D
    [1.0, "#c0392b"],   # E
]


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    names = [p["name"][:35] for p in projects]

    z, text = [], []
    for p in projects:
        row_z, row_t = [], []
        for dim in _DIMENSIONS:
            rating = p.get(_DIM_METRIC[dim])
            val = int(rating) if rating is not None else 0
            row_z.append(val)
            row_t.append(_RATING_LABEL.get(val, "?") if val else "-")
        z.append(row_z)
        text.append(row_t)

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=_DIMENSIONS,
            y=names,
            text=text,
            texttemplate="<b>%{text}</b>",
            textfont=dict(size=14),
            colorscale=_COLORSCALE,
            zmin=1,
            zmax=5,
            showscale=True,
            colorbar=dict(
                title="Rating",
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["A", "B", "C", "D", "E"],
            ),
        )
    )
    fig.update_layout(
        xaxis_title="Dimension",
        yaxis_title="Project",
        height=max(350, 60 + 35 * len(projects)),
        margin=dict(l=200, t=20, b=40, r=80),
        yaxis=dict(autorange="reversed"),
    )

    return [("Technical Debt Heatmap (SQALE Ratings A–E)", fig)]
