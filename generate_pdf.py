"""
Generate manuscript PDF from manuscript.md using weasyprint.
Tables are embedded in the markdown (no CSV build needed).
Figures are inserted from output/figures/.
"""

import re
from pathlib import Path

import markdown
import weasyprint

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
MANUSCRIPT_MD = PROJECT_DIR / "manuscript.md"

FIGURE_FILES = {
    "Figure 1": "figure1_scatter.png",
    "Figure 2": "figure2_forest.png",
}

CSS = """
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center { content: counter(page); font-size: 10pt; color: #666; }
}
body {
    font-family: "Times New Roman", "DejaVu Serif", Georgia, serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #111;
}
h1 { font-size: 16pt; margin-top: 0; margin-bottom: 8pt; line-height: 1.3; }
h2 { font-size: 13pt; margin-top: 20pt; margin-bottom: 6pt;
     border-bottom: 1px solid #ccc; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin-top: 14pt; margin-bottom: 4pt; }
p { margin: 6pt 0; text-align: justify; }
sup { font-size: 0.75em; }
table {
    border-collapse: collapse; width: 100%; margin: 10pt 0;
    font-size: 9pt;
}
th, td {
    border: 1px solid #999; padding: 3pt 5pt; text-align: left;
}
th { background: #e8e8e8; font-weight: bold; }
hr { border: none; border-top: 1px solid #ccc; margin: 16pt 0; }
img { max-width: 100%; height: auto; margin: 10pt 0; }
strong { font-weight: bold; }
em { font-style: italic; }
.figure-block {
    page-break-inside: avoid;
    margin: 1.5em 0;
    text-align: center;
}
.figure-block img {
    display: block;
    margin: 0 auto;
    max-width: 95%;
}
.figure-caption {
    font-size: 10pt;
    text-align: justify;
    margin-top: 0.5em;
}
"""


def extract_figure_legends(md_text: str) -> dict[str, str]:
    """Extract figure legend text from manuscript."""
    legends = {}
    pattern = r'\*\*Figure (\d+)\.\*\*\s*(.*?)(?=\n\n|\*\*Figure|\Z)'
    for m in re.finditer(pattern, md_text, re.DOTALL):
        fig_num = m.group(1)
        text = m.group(2).strip().replace("\n", " ")
        legends[f"Figure {fig_num}"] = text
    return legends


def build_figures_html(legends: dict[str, str]) -> str:
    """Build HTML for figures section."""
    html = '<div style="page-break-before:always"></div>\n'
    html += "<h2>Figures</h2>\n"

    for fig_label, fig_file in FIGURE_FILES.items():
        fig_path = FIGURES_DIR / fig_file
        if not fig_path.exists():
            print(f"[WARN] {fig_path} not found, skipping")
            continue
        caption = legends.get(fig_label, "")
        html += '<div class="figure-block">'
        html += f'<img src="file://{fig_path.resolve()}" alt="{fig_label}">'
        html += f'<p class="figure-caption"><strong>{fig_label}.</strong> '
        html += f"{caption}</p></div>\n"

    return html


def convert():
    md_text = MANUSCRIPT_MD.read_text(encoding="utf-8")

    legends = extract_figure_legends(md_text)

    # Remove Figure Legends section (will be rebuilt with actual images)
    md_text = re.sub(
        r"### Figure Legends.*",
        "",
        md_text,
        flags=re.DOTALL,
    )

    # Convert pandoc-style superscripts ^text^ to <sup>text</sup>
    md_text = re.sub(r'\^([^^]+?)\^', r'<sup>\1</sup>', md_text)

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "smarty"],
    )

    figures_html = build_figures_html(legends)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{html_body}{figures_html}</body></html>"""

    out_path = OUTPUT_DIR / "manuscript.pdf"
    weasyprint.HTML(string=html, base_url=str(PROJECT_DIR)).write_pdf(
        str(out_path)
    )
    print(f"[OK] {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    convert()
