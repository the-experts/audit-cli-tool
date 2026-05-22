from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_OWASP_LABELS = {
    "a1": "A1 - Injection",
    "a2": "A2 - Broken Auth",
    "a3": "A3 - Sensitive Data",
    "a4": "A4 - XXE",
    "a5": "A5 - Broken Access",
    "a6": "A6 - Security Misconfig",
    "a7": "A7 - XSS",
    "a8": "A8 - Insecure Deserialize",
    "a9": "A9 - Vulnerable Components",
    "a10": "A10 - Logging",
    "unknown": "Other",
}
_SEV_COLORS = {
    "BLOCKER": "#7b241c",
    "CRITICAL": "#e74c3c",
    "MAJOR": "#e67e22",
    "MINOR": "#f1c40f",
    "INFO": "#3498db",
}


def build(sec_data: Dict[str, Any]) -> List[Tuple[str, go.Figure]]:
    owasp = sec_data.get("owasp", {})
    vuln_sev = sec_data.get("vuln_by_severity", {})
    to_review = sec_data.get("hotspots_to_review", 0)
    reviewed = sec_data.get("hotspots_reviewed", 0)

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["OWASP Top 10 Breakdown", "Vulnerabilities by Severity", "Security Hotspots"],
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "pie"}]],
        column_widths=[0.45, 0.3, 0.25],
    )

    if owasp:
        sorted_owasp = sorted(owasp.items(), key=lambda x: x[1], reverse=True)
        labels = [_OWASP_LABELS.get(k.lower(), k) for k, _ in sorted_owasp]
        counts = [v for _, v in sorted_owasp]
        fig.add_trace(
            go.Bar(x=counts, y=labels, orientation="h", marker_color="#e74c3c", showlegend=False),
            row=1, col=1,
        )
    else:
        fig.add_annotation(text="No OWASP data", row=1, col=1, showarrow=False)

    if vuln_sev:
        for sev, count in vuln_sev.items():
            fig.add_trace(
                go.Bar(
                    name=sev, x=[sev], y=[count],
                    marker_color=_SEV_COLORS.get(sev, "#95a5a6"),
                    showlegend=False,
                ),
                row=1, col=2,
            )

    total_hs = to_review + reviewed
    if total_hs > 0:
        fig.add_trace(
            go.Pie(
                labels=["To Review", "Reviewed"],
                values=[to_review, reviewed],
                marker=dict(colors=["#e74c3c", "#27ae60"]),
                hole=0.45,
                textinfo="label+percent",
                showlegend=False,
            ),
            row=1, col=3,
        )
    else:
        fig.add_annotation(
            text="No hotspot data",
            xref="paper", yref="paper",
            x=0.875, y=0.5,
            showarrow=False,
        )

    fig.update_layout(height=450, margin=dict(t=60, b=40, l=10, r=10))
    fig.update_xaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Category", row=1, col=1)
    fig.update_xaxes(title_text="Severity", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)

    return [("Security Vulnerability Distribution", fig)]
