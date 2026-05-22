from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build(
    teams: List[Dict[str, Any]],
    projects_data: List[Dict[str, Any]],
) -> List[Tuple[str, go.Figure]]:
    """
    teams: [{'name': str, 'projects': [key, ...]}, ...]
    projects_data: list of project dicts from data.fetch_projects_data
    """
    by_key = {p["key"]: p for p in projects_data}

    team_stats = []
    for team in teams:
        team_projects = [by_key[k] for k in team["projects"] if k in by_key]
        total = len(team_projects)
        passing = sum(1 for p in team_projects if p.get("qg_status") == "OK")
        pass_rate = (passing / total * 100) if total else 0
        bugs = sum(p.get("bugs") or 0 for p in team_projects)
        vulns = sum(p.get("vulnerabilities") or 0 for p in team_projects)
        smells = sum(p.get("code_smells") or 0 for p in team_projects)
        debt_h = sum((p.get("sqale_index") or 0) + (p.get("reliability_remediation_effort") or 0) + (p.get("security_remediation_effort") or 0) for p in team_projects) / 60
        team_stats.append({
            "name": team["name"],
            "total": total,
            "passing": passing,
            "pass_rate": pass_rate,
            "bugs": bugs,
            "vulns": vulns,
            "smells": smells,
            "debt_h": debt_h,
        })

    team_names = [t["name"] for t in team_stats]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Quality Gate Pass Rate (%)",
            "Total Projects",
            "Bug & Vulnerability Count",
            "Total Debt (hours)",
        ],
    )

    colors = [f"hsl({i * 360 // max(len(team_stats), 1)},60%,55%)" for i in range(len(team_stats))]

    fig.add_trace(
        go.Bar(
            x=team_names,
            y=[t["pass_rate"] for t in team_stats],
            marker_color=[("#27ae60" if t["pass_rate"] >= 80 else "#e74c3c") for t in team_stats],
            text=[f"{t['pass_rate']:.0f}%" for t in team_stats],
            textposition="outside",
            showlegend=False,
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Bar(
            x=team_names,
            y=[t["total"] for t in team_stats],
            marker_color=colors,
            text=[str(t["total"]) for t in team_stats],
            textposition="outside",
            showlegend=False,
        ),
        row=1, col=2,
    )

    fig.add_trace(
        go.Bar(name="Bugs", x=team_names, y=[t["bugs"] for t in team_stats], marker_color="#e74c3c"),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(name="Vulnerabilities", x=team_names, y=[t["vulns"] for t in team_stats], marker_color="#e67e22"),
        row=2, col=1,
    )

    fig.add_trace(
        go.Bar(
            x=team_names,
            y=[t["debt_h"] for t in team_stats],
            marker_color="#9b59b6",
            text=[f"{t['debt_h']:.0f}h" for t in team_stats],
            textposition="outside",
            showlegend=False,
        ),
        row=2, col=2,
    )

    fig.update_layout(
        barmode="group",
        height=620,
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", y=0.46),
    )
    fig.update_yaxes(range=[0, 105], row=1, col=1)

    return [("Ownership & Responsibility Map", fig)]
