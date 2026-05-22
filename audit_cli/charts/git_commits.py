from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_COLOR_ALL = "#3498db"
_COLOR_REPO = "#27ae60"
_COLOR_AUTHOR = "#e74c3c"
_HEATMAP_SCALE = [[0, "#f0f4f8"], [0.15, "#d6eaf8"], [0.5, "#3498db"], [1.0, "#1a5276"]]
_REPO_PALETTE = [
    "#27ae60", "#e67e22", "#9b59b6", "#1abc9c", "#f39c12",
    "#2980b9", "#c0392b", "#16a085", "#8e44ad", "#d35400",
]


def _make_grid(subset: List[Dict]) -> List[List[int]]:
    grid = [[0] * 24 for _ in range(7)]
    for c in subset:
        grid[c["weekday"]][c["hour"]] += 1
    return grid


def _make_cumulative(dates: List[str], day_counts: Dict[str, int]) -> List[int]:
    total, cum = 0, []
    for d in dates:
        total += day_counts.get(d, 0)
        cum.append(total)
    return cum


def _add_three_traces(fig, dates, day_counts, subset, color, label, visible):
    """Add the daily bar, heatmap, and cumulative line for one filter (all/repo/author)."""
    hover_prefix = f"<b>{label}</b><br>" if label else ""
    fig.add_trace(go.Bar(
        x=dates,
        y=[day_counts.get(d, 0) for d in dates],
        marker_color=color,
        showlegend=False,
        visible=visible,
        hovertemplate=f"{hover_prefix}%{{x}}<br>Commits: %{{y}}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Heatmap(
        z=_make_grid(subset),
        x=list(range(24)),
        y=_WEEKDAYS,
        colorscale=_HEATMAP_SCALE,
        showscale=False,
        visible=visible,
        hovertemplate=f"{hover_prefix}Day: %{{y}}<br>Hour: %{{x}}:00<br>Commits: %{{z}}<extra></extra>",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=dates,
        y=_make_cumulative(dates, day_counts),
        mode="lines",
        fill="tozeroy",
        line=dict(color=color, width=2),
        showlegend=False,
        visible=visible,
        hovertemplate=f"{hover_prefix}%{{x}}<br>Total commits: %{{y}}<extra></extra>",
    ), row=3, col=1)


def build(commits: List[Dict[str, Any]]) -> List[Tuple[str, go.Figure]]:
    if not commits:
        return []

    dates = sorted(set(c["date"] for c in commits))
    repos = sorted(set(c["repo"] for c in commits))
    top_authors = [a for a, _ in Counter(c["name"] for c in commits).most_common(30)]

    n_repos = len(repos)
    n_authors = len(top_authors)
    has_multi_repo = n_repos > 1

    # Group commits
    repo_commits: Dict[str, List] = defaultdict(list)
    author_commits: Dict[str, List] = defaultdict(list)
    for c in commits:
        repo_commits[c["repo"]].append(c)
        author_commits[c["name"]].append(c)

    # Trace layout:
    #   [0,1,2]            → All
    #   [3 .. 3+n_repos*3) → per-repo  (only when multi-repo)
    #   [3+n_repos*3 ..]   → per-author
    repo_block = 3 if has_multi_repo else 0   # traces before per-repo block
    author_base = 3 + (n_repos * 3 if has_multi_repo else 0)
    total_traces = author_base + n_authors * 3

    def _vis(repo_idx=None, author_idx=None):
        v = [False] * total_traces
        if repo_idx is None and author_idx is None:
            v[0] = v[1] = v[2] = True
        elif repo_idx is not None:
            base = 3 + repo_idx * 3
            v[base] = v[base + 1] = v[base + 2] = True
        else:
            base = author_base + author_idx * 3
            v[base] = v[base + 1] = v[base + 2] = True
        return v

    # Build figure
    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.38, 0.32, 0.30],
        vertical_spacing=0.09,
        subplot_titles=["Commits per Day", "Activity Heatmap (Weekday × Hour)", "Cumulative Commits"],
    )

    day_counts = dict(Counter(c["date"] for c in commits))
    _add_three_traces(fig, dates, day_counts, commits, _COLOR_ALL, "", True)

    if has_multi_repo:
        for i, repo in enumerate(repos):
            rc = repo_commits[repo]
            _add_three_traces(fig, dates, dict(Counter(c["date"] for c in rc)),
                               rc, _REPO_PALETTE[i % len(_REPO_PALETTE)], repo, False)

    for author in top_authors:
        ac = author_commits[author]
        _add_three_traces(fig, dates, dict(Counter(c["date"] for c in ac)),
                          ac, _COLOR_AUTHOR, author, False)

    # ── dropdowns ─────────────────────────────────────────────────────────
    repo_buttons = [dict(label="All Repos", method="update", args=[{"visible": _vis()}])]
    for i, repo in enumerate(repos):
        repo_buttons.append(dict(label=repo, method="update", args=[{"visible": _vis(repo_idx=i)}]))

    author_buttons = [dict(label="All Authors", method="update", args=[{"visible": _vis()}])]
    for i, author in enumerate(top_authors):
        author_buttons.append(dict(label=author, method="update", args=[{"visible": _vis(author_idx=i)}]))

    dropdown_style = dict(type="dropdown", bgcolor="#f0f4f8", bordercolor="#aaa",
                          font=dict(size=12), yanchor="top")

    updatemenus = [
        dict(**dropdown_style, buttons=author_buttons, x=0.52 if has_multi_repo else 0,
             xanchor="left", y=1.06),
    ]
    if has_multi_repo:
        updatemenus.insert(0, dict(**dropdown_style, buttons=repo_buttons,
                                   x=0, xanchor="left", y=1.06))

    # Labels for the dropdowns (annotations added after existing subplot title annotations)
    extra_annotations = []
    if has_multi_repo:
        extra_annotations.append(dict(
            text="<b>Repository</b>", x=0, xanchor="left", y=1.10,
            xref="paper", yref="paper", showarrow=False, font=dict(size=11),
        ))
    extra_annotations.append(dict(
        text="<b>Author</b>", x=0.52 if has_multi_repo else 0, xanchor="left", y=1.10,
        xref="paper", yref="paper", showarrow=False, font=dict(size=11),
    ))

    fig.update_layout(
        updatemenus=updatemenus,
        annotations=list(fig.layout.annotations) + extra_annotations,
        height=940,
        margin=dict(t=150, b=60, l=120, r=20),
    )
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Commits", row=1, col=1)
    fig.update_xaxes(title_text="Hour of Day (UTC)", tickmode="linear", tick0=0, dtick=2, row=2, col=1)
    fig.update_yaxes(autorange="reversed", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Cumulative Commits", row=3, col=1)

    sections = [("Git Activity Overview", fig)]

    # ── commits per author ────────────────────────────────────────────────
    author_counts = Counter(c["name"] for c in commits).most_common(25)
    fig2 = go.Figure(go.Bar(
        x=[v for _, v in reversed(author_counts)],
        y=[a for a, _ in reversed(author_counts)],
        orientation="h",
        marker_color=_COLOR_ALL,
        text=[v for _, v in reversed(author_counts)],
        textposition="outside",
        hovertemplate="%{y}<br>Commits: %{x}<extra></extra>",
    ))
    fig2.update_layout(
        xaxis_title="Commits",
        height=max(320, 60 + len(author_counts) * 30),
        margin=dict(t=20, b=40, l=20, r=60),
        showlegend=False,
    )
    sections.append(("Commits per Author", fig2))

    # ── commits per repo (multi-repo only) ────────────────────────────────
    if has_multi_repo:
        fig3 = make_subplots(rows=1, cols=2, subplot_titles=["Total Commits", "Cumulative over Time"])
        repo_counts = Counter(c["repo"] for c in commits)
        fig3.add_trace(go.Bar(
            x=[repo_counts[r] for r in repos],
            y=repos,
            orientation="h",
            marker_color=[_REPO_PALETTE[i % len(_REPO_PALETTE)] for i in range(n_repos)],
            text=[repo_counts[r] for r in repos],
            textposition="outside",
            showlegend=False,
            hovertemplate="%{y}<br>Commits: %{x}<extra></extra>",
        ), row=1, col=1)
        for i, repo in enumerate(repos):
            rc = dict(Counter(c["date"] for c in repo_commits[repo]))
            fig3.add_trace(go.Scatter(
                x=dates, y=_make_cumulative(dates, rc),
                mode="lines", name=repo,
                line=dict(color=_REPO_PALETTE[i % len(_REPO_PALETTE)], width=2),
                hovertemplate=f"<b>{repo}</b><br>%{{x}}<br>Total: %{{y}}<extra></extra>",
            ), row=1, col=2)
        fig3.update_layout(
            height=max(360, 80 + n_repos * 32),
            margin=dict(t=40, b=40, l=20, r=20),
            legend_title="Repository",
        )
        fig3.update_xaxes(title_text="Commits", row=1, col=1)
        fig3.update_xaxes(title_text="Date", row=1, col=2)
        fig3.update_yaxes(title_text="Cumulative Commits", row=1, col=2)
        sections.append(("Commits per Repository", fig3))

    return sections
