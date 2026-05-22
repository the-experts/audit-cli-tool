from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_SEVERITIES = [
    ("blocker_violations", "Blocker", "#7b241c"),
    ("critical_violations", "Critical", "#e74c3c"),
    ("major_violations", "Major", "#e67e22"),
    ("minor_violations", "Minor", "#f4d03f"),
    ("info_violations", "Info", "#3498db"),
]


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    sorted_projects = sorted(
        projects,
        key=lambda p: sum(p.get(m) or 0 for m, _, _ in _SEVERITIES),
        reverse=True,
    )
    names = [p["name"][:35] for p in sorted_projects]

    fig = go.Figure()
    for metric, label, color in _SEVERITIES:
        values = [p.get(metric) or 0 for p in sorted_projects]
        fig.add_trace(go.Bar(
            name=label,
            y=names,
            x=values,
            orientation="h",
            marker_color=color,
            hovertemplate=f"<b>%{{y}}</b><br>{label}: %{{x}}<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        xaxis_title="Violations",
        legend_title="Severity",
        height=max(400, 40 + len(projects) * 30),
        margin=dict(t=20, b=40, l=20, r=20),
    )
    return [("Violations by Severity per Project", fig)]
