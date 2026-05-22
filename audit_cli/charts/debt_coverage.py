import math
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_MINUTES_PER_DAY = 480  # 8-hour working day

_RATING_COLOR = {
    1: "#27ae60",  # A – green
    2: "#82e0aa",  # B – light green
    3: "#e67e22",  # C – orange
    4: "#e74c3c",  # D – red
    5: "#7b241c",  # E – dark red
}
_RATING_LABEL = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}

_ZONE_R1 = 0.38   # high / medium quality boundary (normalised radius)
_ZONE_R2 = 0.72   # medium / attention boundary


def _zone_traces(max_debt: float) -> List[go.Scatter]:
    """Quarter-circle zone fills + boundary arcs, centred at (0, 100)."""
    n = 100
    thetas = [i * math.pi / (2 * (n - 1)) for i in range(n)]

    def ax(r): return [r * math.sin(t) * max_debt for t in thetas]
    def ay(r): return [100 - r * math.cos(t) * 100 for t in thetas]

    x1, y1 = ax(_ZONE_R1), ay(_ZONE_R1)
    x2, y2 = ax(_ZONE_R2), ay(_ZONE_R2)

    return [
        # Gemiddelde kwaliteit – annular sector (orange tint)
        go.Scatter(
            x=x2 + x1[::-1] + [x2[0]],
            y=y2 + y1[::-1] + [y2[0]],
            fill="toself",
            fillcolor="rgba(243, 156, 18, 0.10)",
            line=dict(width=0),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        ),
        # Hoge kwaliteit – inner pie slice (green tint)
        go.Scatter(
            x=[0] + x1 + [0],
            y=[100] + y1 + [100],
            fill="toself",
            fillcolor="rgba(39, 174, 96, 0.14)",
            line=dict(width=0),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        ),
        # Inner arc boundary (dotted green)
        go.Scatter(
            x=x1, y=y1,
            mode="lines",
            line=dict(color="rgba(39, 174, 96, 0.50)", width=1.5, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ),
        # Outer arc boundary (dotted orange)
        go.Scatter(
            x=x2, y=y2,
            mode="lines",
            line=dict(color="rgba(243, 156, 18, 0.50)", width=1.5, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ),
    ]


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    valid = [
        p for p in projects
        if p.get("coverage") is not None and p.get("sqale_index") is not None
    ]
    if not valid:
        fig = go.Figure()
        fig.update_layout(annotations=[dict(
            text="No debt/coverage data available",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        )])
        return [("Technische schuld vs. testdekking", fig)]

    max_loc  = max((p.get("ncloc") or 1 for p in valid), default=1)
    max_debt = max(p["sqale_index"] / _MINUTES_PER_DAY for p in valid)

    def _worst_rating(p):
        r = p.get("reliability_rating")
        s = p.get("security_rating")
        vals = [v for v in (r, s) if v is not None]
        return int(max(vals)) if vals else 3

    by_rating: Dict[int, List] = {r: [] for r in range(1, 6)}
    for p in valid:
        by_rating[_worst_rating(p)].append(p)

    fig = go.Figure()

    # Light-red background rectangle for "Aandacht vereist" (worst zone)
    fig.add_shape(
        type="rect",
        x0=0, y0=0,
        x1=max_debt * 1.15, y1=100,
        fillcolor="rgba(231, 76, 60, 0.06)",
        line=dict(width=0),
        layer="below",
    )

    for trace in _zone_traces(max_debt):
        fig.add_trace(trace)

    # Zone labels at 45° mid-angle of each zone
    theta_mid = math.pi / 4
    for label, r_mid, color in [
        ("Hoge kwaliteit",       _ZONE_R1 * 0.50,                     "rgba(27, 153, 78, 0.95)"),
        ("Gemiddelde kwaliteit", (_ZONE_R1 + _ZONE_R2) / 2,           "rgba(211, 128, 9, 0.95)"),
        ("Aandacht vereist",     _ZONE_R2 + (1.0 - _ZONE_R2) * 0.38, "rgba(192, 57, 43, 0.95)"),
    ]:
        lx = r_mid * math.sin(theta_mid) * max_debt
        ly = 100 - r_mid * math.cos(theta_mid) * 100
        fig.add_annotation(
            x=lx, y=ly,
            text=label,
            showarrow=False,
            font=dict(size=10, color=color),
            bgcolor="rgba(255,255,255,0.60)",
            borderpad=3,
        )

    for rating in range(1, 6):
        group = by_rating[rating]
        if not group:
            continue
        debt_days   = [p["sqale_index"] / _MINUTES_PER_DAY for p in group]
        coverage    = [p["coverage"] for p in group]
        sizes       = [max(10, 80 * math.sqrt((p.get("ncloc") or 1) / max_loc)) for p in group]
        hover_texts = [
            f"<b>{p['name']}</b><br>"
            f"Debt: {p['sqale_index'] / _MINUTES_PER_DAY:.1f} days<br>"
            f"Coverage: {p['coverage']:.1f}%<br>"
            f"LOC: {int(p.get('ncloc') or 0):,}<br>"
            f"Reliability: {_RATING_LABEL.get(int(p.get('reliability_rating') or 3), '?')}<br>"
            f"Security: {_RATING_LABEL.get(int(p.get('security_rating') or 3), '?')}"
            for p in group
        ]
        fig.add_trace(go.Scatter(
            x=debt_days,
            y=coverage,
            mode="markers+text",
            name=f"Rating {_RATING_LABEL[rating]}",
            text=[p["name"] for p in group],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=sizes,
                color=_RATING_COLOR[rating],
                opacity=0.80,
                line=dict(width=1, color="white"),
                sizemode="diameter",
            ),
            customdata=hover_texts,
            hovertemplate="%{customdata}<extra></extra>",
        ))

    title = (
        "Technische schuld van de modules (horizontale as; in dagen) t.o.v. de testdekking "
        "(verticale as; in %). De grootte van de cirkels is gebaseerd op de grootte van de modules "
        "(aantal regels code; excl. commentaar). De kleur van de cirkels is gebaseerd op de "
        "betrouwbaarheid en veiligheid (slechtste resultaat is afgebeeld)."
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=12), x=0, xanchor="left"),
        xaxis=dict(title="Technische schuld (dagen)", rangemode="tozero",
                   range=[-max_debt * 0.03, max_debt * 1.10]),
        yaxis=dict(title="Testdekking (%)", range=[102, -2]),
        legend=dict(title="Betrouwbaarheid &<br>Veiligheid (slechtste)", orientation="v"),
        height=600,
        margin=dict(t=120, b=60, l=60, r=20),
    )

    return [("Technische schuld vs. testdekking", fig)]
