import os
from typing import List, Tuple

import plotly.graph_objects as go

_PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
_PNG_WIDTH = 1600

_PAGE_STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0; padding: 24px; background: #f0f2f5; color: #2c3e50;
}
h1 { border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 24px; }
h2 { color: #34495e; margin: 0 0 12px; font-size: 1.1rem; }
.chart-wrapper {
    background: #fff; padding: 20px; margin-bottom: 24px;
    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.08);
}
"""


def _save_png(sections: List[Tuple[str, go.Figure]], base_path: str) -> List[str]:
    try:
        import kaleido  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "PNG export requires kaleido. Install it with:\n"
            "  pip install 'audit-cli[png]'"
        )

    stem, _ = os.path.splitext(base_path)
    dir_name = os.path.dirname(base_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    paths = []
    for i, (title, fig) in enumerate(sections):
        suffix = f"_{i + 1}" if len(sections) > 1 else ""
        path = f"{stem}{suffix}.png"
        height = fig.layout.height or 600
        fig.write_image(path, width=_PNG_WIDTH, height=height, scale=2)
        paths.append(path)
    return paths


def save_html(
    sections: List[Tuple[str, go.Figure]],
    output_path: str,
    page_title: str = "SonarQube Report",
) -> List[str]:
    if output_path.endswith(".png"):
        return _save_png(sections, output_path)

    parts = [
        "<!DOCTYPE html><html><head>",
        '<meta charset="utf-8">',
        f"<title>{page_title}</title>",
        f'<script src="{_PLOTLY_CDN}"></script>',
        f"<style>{_PAGE_STYLE}</style>",
        "</head><body>",
        f"<h1>{page_title}</h1>",
    ]
    for section_title, fig in sections:
        parts.append('<div class="chart-wrapper">')
        if section_title:
            parts.append(f"<h2>{section_title}</h2>")
        parts.append(fig.to_html(full_html=False, include_plotlyjs=False))
        parts.append("</div>")
    parts.append("</body></html>")

    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))

    return [output_path]
