from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_RATING_COLORS = {
    1: "#27ae60",
    2: "#82e0aa",
    3: "#e67e22",
    4: "#e74c3c",
    5: "#7b241c",
}
_RATING_LABELS = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    filtered = [p for p in projects if not p.get("_error")]
    if not filtered:
        return []

    sorted_projects = sorted(
        filtered,
        key=lambda p: (p.get("vulnerabilities") or 0) + (p.get("security_hotspots") or 0),
        reverse=True,
    )
    names = [p["name"][:40] for p in sorted_projects]

    # ── chart 1: vulnerabilities + hotspots per project ───────────────────
    fig1 = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Vulnerabilities", "Security Hotspots"],
        shared_yaxes=True,
    )

    vuln_colors = [
        _RATING_COLORS.get(int(p.get("security_rating") or 3), "#e67e22")
        for p in sorted_projects
    ]
    fig1.add_trace(
        go.Bar(
            x=[p.get("vulnerabilities") or 0 for p in sorted_projects],
            y=names,
            orientation="h",
            marker_color=vuln_colors,
            showlegend=False,
            hovertemplate="<b>%{y}</b><br>Vulnerabilities: %{x}<extra></extra>",
        ),
        row=1, col=1,
    )
    fig1.add_trace(
        go.Bar(
            x=[p.get("security_hotspots") or 0 for p in sorted_projects],
            y=names,
            orientation="h",
            marker_color="#9b59b6",
            showlegend=False,
            hovertemplate="<b>%{y}</b><br>Security Hotspots: %{x}<extra></extra>",
        ),
        row=1, col=2,
    )

    # invisible legend traces for security rating colours
    for rating, color in _RATING_COLORS.items():
        fig1.add_trace(go.Bar(
            x=[None], y=[None],
            orientation="h",
            name=f"Rating {_RATING_LABELS[rating]}",
            marker_color=color,
            showlegend=True,
        ))

    fig1.update_xaxes(title_text="Count", row=1, col=1)
    fig1.update_xaxes(title_text="Count", row=1, col=2)
    fig1.update_layout(
        legend_title="Security Rating",
        height=max(400, 60 + len(sorted_projects) * 28),
        margin=dict(t=40, b=40, l=20, r=20),
        barmode="overlay",
    )

    # ── chart 2: remediation effort per project ────────────────────────────
    effort_projects = sorted(
        filtered,
        key=lambda p: p.get("security_remediation_effort") or 0,
        reverse=True,
    )
    effort_hours = [(p.get("security_remediation_effort") or 0) / 60 for p in effort_projects]
    effort_names = [p["name"][:40] for p in effort_projects]

    fig2 = go.Figure(go.Bar(
        x=effort_hours,
        y=effort_names,
        orientation="h",
        marker_color=[
            _RATING_COLORS.get(int(p.get("security_rating") or 3), "#e67e22")
            for p in effort_projects
        ],
        hovertemplate="<b>%{y}</b><br>Security Remediation: %{x:.1f}h<extra></extra>",
    ))
    fig2.update_layout(
        xaxis_title="Hours",
        height=max(400, 60 + len(effort_projects) * 28),
        margin=dict(t=20, b=40, l=20, r=20),
        showlegend=False,
    )

    return [
        ("Vulnerabilities & Hotspots per Project (colour = security rating)", fig1),
        ("Security Remediation Effort per Project", fig2),
    ]
