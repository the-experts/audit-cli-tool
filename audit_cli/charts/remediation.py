from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go


def _mins_to_h(v: Any) -> float:
    try:
        return float(v or 0) / 60
    except (TypeError, ValueError):
        return 0.0


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    sorted_p = sorted(projects, key=lambda p: (
        _mins_to_h(p.get("sqale_index")) +
        _mins_to_h(p.get("reliability_remediation_effort")) +
        _mins_to_h(p.get("security_remediation_effort"))
    ), reverse=True)

    names = [p["name"][:30] for p in sorted_p]
    maintainability = [_mins_to_h(p.get("sqale_index")) for p in sorted_p]
    reliability = [_mins_to_h(p.get("reliability_remediation_effort")) for p in sorted_p]
    security = [_mins_to_h(p.get("security_remediation_effort")) for p in sorted_p]
    totals = [m + r + s for m, r, s in zip(maintainability, reliability, security)]

    stacked = go.Figure()
    stacked.add_trace(go.Bar(name="Maintainability (Code Smells)", x=names, y=maintainability, marker_color="#3498db"))
    stacked.add_trace(go.Bar(name="Reliability (Bugs)", x=names, y=reliability, marker_color="#e74c3c"))
    stacked.add_trace(go.Bar(name="Security (Vulnerabilities)", x=names, y=security, marker_color="#e67e22"))
    stacked.update_layout(
        barmode="stack",
        yaxis_title="Estimated Hours",
        xaxis_tickangle=-40,
        legend=dict(orientation="h", y=1.12),
        height=480,
        margin=dict(t=20, b=120),
    )

    pie = go.Figure(
        go.Pie(
            labels=["Maintainability", "Reliability", "Security"],
            values=[sum(maintainability), sum(reliability), sum(security)],
            marker=dict(colors=["#3498db", "#e74c3c", "#e67e22"]),
            hole=0.4,
            textinfo="label+percent+value",
            texttemplate="%{label}<br>%{value:.0f}h (%{percent})",
        )
    )
    total_all = sum(totals)
    pie.update_layout(
        title=f"Total: {total_all:.0f} hours across all projects",
        height=400,
        margin=dict(t=60, b=20),
    )

    return [
        ("Remediation Effort per Project (stacked by type)", stacked),
        ("Remediation Effort Distribution (all projects)", pie),
    ]
