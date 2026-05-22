from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_METRIC_LABELS = {
    "bugs": "Bugs",
    "vulnerabilities": "Vulnerabilities",
    "code_smells": "Code Smells",
    "coverage": "Coverage (%)",
    "duplicated_lines_density": "Duplication (%)",
    "sqale_index": "Technical Debt (min)",
    "security_hotspots": "Security Hotspots",
    "ncloc": "Lines of Code",
    "reliability_remediation_effort": "Reliability Effort (min)",
    "security_remediation_effort": "Security Effort (min)",
}
_COLORS = ["#3498db", "#e74c3c", "#27ae60", "#e67e22", "#9b59b6", "#1abc9c", "#f39c12", "#95a5a6"]


def build(history: Dict[str, List], project_name: str = "") -> List[Tuple[str, go.Figure]]:
    fig = go.Figure()
    for idx, (metric, series) in enumerate(history.items()):
        valid = [(d, float(v)) for d, v in series if v is not None]
        if not valid:
            continue
        dates, values = zip(*valid)
        fig.add_trace(
            go.Scatter(
                x=list(dates),
                y=list(values),
                name=_METRIC_LABELS.get(metric, metric),
                mode="lines+markers",
                line=dict(color=_COLORS[idx % len(_COLORS)], width=2),
                marker=dict(size=5),
            )
        )

    title_suffix = f" — {project_name}" if project_name else ""
    fig.update_layout(
        xaxis_title="Analysis Date",
        yaxis_title="Value",
        legend=dict(orientation="h", y=1.12),
        height=500,
        margin=dict(t=20, b=60),
        hovermode="x unified",
    )

    return [(f"Trend Over Time{title_suffix}", fig)]
