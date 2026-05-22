from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_TYPE_COLORS = {
    "BUG": "#e74c3c",
    "VULNERABILITY": "#e67e22",
    "CODE_SMELL": "#3498db",
}
_TYPE_LABELS = {"BUG": "Bugs", "VULNERABILITY": "Vulnerabilities", "CODE_SMELL": "Code Smells"}
_SEV_COLORS = {
    "BLOCKER": "#7b241c",
    "CRITICAL": "#e74c3c",
    "MAJOR": "#e67e22",
    "MINOR": "#f4d03f",
    "INFO": "#3498db",
}
_SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]


def build(data: Dict[str, Any]) -> List[Tuple[str, go.Figure]]:
    by_type = data.get("by_type", {})
    by_sev = data.get("by_severity", {})

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Totals by Issue Type", "Totals by Severity"],
        column_widths=[0.4, 0.6],
    )

    for itype in ["BUG", "VULNERABILITY", "CODE_SMELL"]:
        fig.add_trace(
            go.Bar(
                x=[_TYPE_LABELS[itype]],
                y=[by_type.get(itype, 0)],
                name=_TYPE_LABELS[itype],
                marker_color=_TYPE_COLORS[itype],
                showlegend=False,
                text=[by_type.get(itype, 0)],
                textposition="outside",
            ),
            row=1, col=1,
        )

    for sev in _SEVERITIES:
        fig.add_trace(
            go.Bar(
                x=[sev.capitalize()],
                y=[by_sev.get(sev, 0)],
                name=sev,
                marker_color=_SEV_COLORS[sev],
                showlegend=False,
                text=[by_sev.get(sev, 0)],
                textposition="outside",
            ),
            row=1, col=2,
        )

    fig.update_layout(
        height=420,
        margin=dict(t=40, b=60, l=20, r=20),
    )
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)

    return [("Issues Breakdown", fig)]
