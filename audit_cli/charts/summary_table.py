from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

_MINUTES_PER_DAY = 480
_LOC_PER_DAY = 150  # industry estimate for development cost


def _parse_lang_dist(projects: List[Dict[str, Any]]) -> str:
    totals: Dict[str, int] = {}
    for p in projects:
        raw = p.get("ncloc_language_distribution")
        if not raw or not isinstance(raw, str):
            continue
        for part in raw.split(";"):
            if "=" in part:
                lang, count = part.split("=", 1)
                try:
                    totals[lang.strip()] = totals.get(lang.strip(), 0) + int(count)
                except ValueError:
                    pass
    if not totals:
        return "—"
    total = sum(totals.values())
    parts = []
    other_pct = 0.0
    for lang, count in sorted(totals.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        if pct >= 2:
            parts.append(f"{lang.capitalize()}: {pct:.0f}%")
        else:
            other_pct += pct
    if other_pct > 0:
        parts.append(f"Overig: {other_pct:.0f}%")
    return "  |  ".join(parts)


def _weighted_avg(projects, value_key, weight_key="ncloc"):
    pairs = [
        (p.get(value_key), p.get(weight_key) or 0)
        for p in projects
        if p.get(value_key) is not None
    ]
    total_w = sum(w for _, w in pairs)
    if not pairs or total_w == 0:
        return None
    return sum(v * w for v, w in pairs) / total_w


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    valid = [p for p in projects if not p.get("_error")]

    total_modules = len(valid)
    total_ncloc   = int(sum(p.get("ncloc") or 0 for p in valid))

    avg_coverage = _weighted_avg(valid, "coverage")
    avg_dup      = _weighted_avg(valid, "duplicated_lines_density")

    lang_dist   = _parse_lang_dist(valid)
    dev_cost    = total_ncloc / _LOC_PER_DAY if total_ncloc else 0
    debt_days   = sum(p.get("sqale_index") or 0 for p in valid) / _MINUTES_PER_DAY
    bugs        = int(sum(p.get("bugs") or 0 for p in valid))
    vulns       = int(sum(p.get("vulnerabilities") or 0 for p in valid))
    hotspots    = int(sum(p.get("security_hotspots") or 0 for p in valid))
    security    = vulns + hotspots
    dup_lines   = int(sum(p.get("duplicated_lines_density") or 0 for p in valid))

    rows = [
        ("Aantal modules",                              f"{total_modules}"),
        ("Aantal regels code (excl. commentaar)",       f"{total_ncloc:,}"),
        ("Gemiddelde testdekking",                      f"{avg_coverage:.1f}%" if avg_coverage is not None else "—"),
        ("Aandeel programmeertalen",                    lang_dist),
        ("Geschatte ontwikkelkosten (in mensdagen)",    f"{dev_cost:,.0f}  (op basis van {_LOC_PER_DAY} LOC/dag)"),
        ("Geschatte technische schuld (in mensdagen)",  f"{debt_days:,.1f}"),
        ("Aantal problemen / potentiële bugs",          f"{bugs:,}"),
        ("Aantal geschatte veiligheidsissues",          f"{security:,}  (kwetsbaarheden: {vulns:,}  +  hotspots: {hotspots:,})"),
        ("Hoeveelheid duplicate code",                  f"{avg_dup:.1f}%" if avg_dup is not None else "—"),
    ]

    properties = [r[0] for r in rows]
    values     = [r[1] for r in rows]

    row_colors = ["#f0f4f8" if i % 2 == 0 else "#ffffff" for i in range(len(rows))]

    fig = go.Figure(go.Table(
        columnwidth=[3, 4],
        header=dict(
            values=["<b>Eigenschap van systeem</b>", "<b>Waarde</b>"],
            fill_color="#2c3e50",
            font=dict(color="white", size=13),
            align="left",
            height=44,
        ),
        cells=dict(
            values=[properties, values],
            fill_color=[row_colors, row_colors],
            align=["left", "left"],
            font=dict(size=12),
            height=38,
        ),
    ))

    fig.update_layout(
        height=max(300, 80 + len(rows) * 44),
        margin=dict(t=20, b=20, l=10, r=10),
    )

    return [("Systeemeigenschappen", fig)]
