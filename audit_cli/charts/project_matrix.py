from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go

# (metric_key, column_label, higher_is_better)
# None = neutral / informational only (shown but not used for colour score)
_METRICS: List[Tuple[str, str, Optional[bool]]] = [
    ("qg_status",                "QG",           None),
    ("reliability_rating",       "Reliability",  False),
    ("security_rating",          "Security",     False),
    ("sqale_rating",             "Maintain.",    False),
    ("bugs",                     "Bugs",         False),
    ("vulnerabilities",          "Vulns",        False),
    ("code_smells",              "Smells",       False),
    ("security_hotspots",        "Hotspots",     False),
    ("coverage",                 "Coverage %",   True),
    ("duplicated_lines_density", "Duplication%", False),
    ("sqale_index",              "Debt (h)",     False),
    ("ncloc",                    "LOC",          None),
]

_RATING_LETTER = {1.0: "A", 2.0: "B", 3.0: "C", 4.0: "D", 5.0: "E"}
_QG_SCORE = {"OK": 1.0, "WARN": 0.5, "ERROR": 0.0}
_COLORSCALE = [
    [0.0,  "#c0392b"],
    [0.25, "#e67e22"],
    [0.5,  "#f4d03f"],
    [0.75, "#82e0aa"],
    [1.0,  "#1e8449"],
]


def _normalize(values: List[Optional[float]], higher_is_better: bool) -> List[Optional[float]]:
    valid = [v for v in values if v is not None]
    if not valid:
        return [None] * len(values)
    lo, hi = min(valid), max(valid)
    if hi == lo:
        return [0.5 if v is not None else None for v in values]
    out = []
    for v in values:
        if v is None:
            out.append(None)
        else:
            norm = (v - lo) / (hi - lo)
            out.append(norm if higher_is_better else 1.0 - norm)
    return out


def _fmt(key: str, value: Any) -> str:
    if value is None:
        return "—"
    if key == "qg_status":
        return str(value)
    if key in ("reliability_rating", "security_rating", "sqale_rating"):
        return _RATING_LETTER.get(float(value), str(value))
    if key == "sqale_index":
        return f"{float(value) / 60:.0f}h"
    if key in ("coverage", "duplicated_lines_density"):
        return f"{float(value):.1f}%"
    if key == "ncloc":
        v = int(float(value))
        return f"{v:,}"
    return str(int(float(value)))


def build(projects: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    if not projects:
        return []

    col_keys   = [m[0] for m in _METRICS]
    col_labels = [m[1] for m in _METRICS]
    col_dir    = [m[2] for m in _METRICS]

    # Collect raw values per column
    raw: Dict[str, List] = {k: [] for k in col_keys}
    for p in projects:
        for key in col_keys:
            raw[key].append(p.get(key))

    # Normalise scoreable columns; neutral columns get 0.5 (mid-grey)
    norm: Dict[str, List] = {}
    for key, _, direction in _METRICS:
        if direction is None:
            norm[key] = [0.5 if v is not None else None for v in raw[key]]
        elif key == "qg_status":
            norm[key] = [_QG_SCORE.get(str(v), None) if v is not None else None
                         for v in raw[key]]
        else:
            float_vals = [float(v) if v is not None else None for v in raw[key]]
            norm[key] = _normalize(float_vals, direction)

    # Sort projects by mean score (best first)
    def _score(i):
        vals = [norm[k][i] for k in col_keys if norm[k][i] is not None]
        return sum(vals) / len(vals) if vals else 0.0

    order = sorted(range(len(projects)), key=_score, reverse=True)
    sorted_projects = [projects[i] for i in order]

    proj_names = [p["name"][:45] for p in sorted_projects]

    z    = [[norm[k][order[r]] if norm[k][order[r]] is not None else 0.5
             for k in col_keys]
            for r in range(len(sorted_projects))]
    text = [[_fmt(k, sorted_projects[r].get(k))
             for k in col_keys]
            for r in range(len(sorted_projects))]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=col_labels,
        y=proj_names,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale=_COLORSCALE,
        zmin=0,
        zmax=1,
        showscale=False,
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
    ))

    fig.update_layout(
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        height=max(420, 80 + len(projects) * 26),
        margin=dict(t=80, b=20, l=20, r=20),
    )

    return [("Aggregated Project Matrix", fig)]
