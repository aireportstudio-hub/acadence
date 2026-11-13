"""Render and inspect four outputs from one synthetic academic report fixture."""

import argparse
import html
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

TITLE = "Campus Reading Study"
HEADER = "Acadence compatibility sample"
FOOTER = "P00 fixture"
SECTIONS = [
    ("Introduction", "This sample report describes a campus reading study."),
    ("Methodology", "The student confirmed that a reading diary was used."),
]
TEX = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "\\": r"\textbackslash{}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape_tex(value: str) -> str:
    return "".join(TEX.get(char, char) for char in value)


def make_html(path: Path) -> None:
    chapters = "".join(f"<section><h2>{html.escape(h)}</h2><p>{html.escape(p)}</p></section>" for h, p in SECTIONS)
    path.write_text(f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>{html.escape(TITLE)}</title>
<style>
@page {{ size: A4; margin: 2cm }}
body {{ font: 11pt/1.5 Georgia, serif; max-width: 44rem; margin: 2rem auto; padding: 0 1rem }}
.cover {{ break-after: page }}
header, footer {{ font-size: 9pt }}
</style>
<header>{html.escape(HEADER)}</header>
<article class="cover"><h1>{html.escape(TITLE)}</h1></article>
{chapters}<footer>{html.escape(FOOTER)}</footer></html>
""", encoding="utf-8")


def make_docx(path: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Cm(2)
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(11)
    section.header.paragraphs[0].text = HEADER
    section.footer.paragraphs[0].text = FOOTER
    doc.add_heading(TITLE, 0)
    doc.add_page_break()
    for heading, body in SECTIONS:
        doc.add_heading(heading, 1)
        doc.add_paragraph(body)
    doc.save(path)
    reopened = Document(path)
    assert [p.text for p in reopened.paragraphs if p.text] == [TITLE, *(item for pair in SECTIONS for item in pair)]
    assert reopened.sections[0].header.paragraphs[0].text == HEADER
    assert reopened.sections[0].footer.paragraphs[0].text == FOOTER


def make_pdf(path: Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=56.7, rightMargin=56.7, topMargin=56.7, bottomMargin=56.7)
    content = [Paragraph(html.escape(TITLE), styles["Title"]), PageBreak()]
    for heading, body in SECTIONS:
        content.extend((Paragraph(html.escape(heading), styles["Heading1"]), Paragraph(html.escape(body), styles["BodyText"])))

    def decorate(canvas, _document):
        canvas.setFont("Times-Roman", 9)
        canvas.drawString(56.7, A4[1] - 34, HEADER)
        canvas.drawString(56.7, 34, FOOTER)

    doc.build(content, onFirstPage=decorate, onLaterPages=decorate)


def make_tex(path: Path) -> None:
    chapters = "\n".join(r"\section{" + escape_tex(heading) + "}\n" + escape_tex(body) for heading, body in SECTIONS)
    path.write_text(r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2cm,headheight=15pt]{geometry}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\lhead{""" + escape_tex(HEADER) + r"""}
\lfoot{""" + escape_tex(FOOTER) + r"""}
\begin{document}
{\LARGE """ + escape_tex(TITLE) + r"""}
\newpage
""" + chapters + "\n" + r"\end{document}" + "\n", encoding="utf-8")


def verify_pdf(path: Path) -> None:
    pages = PdfReader(path).pages
    assert len(pages) == 2
    first, second = (" ".join(page.extract_text().split()) for page in pages)
    assert TITLE in first and SECTIONS[0][0] not in first
    assert HEADER in first and HEADER in second and FOOTER in first and FOOTER in second
    for heading, body in SECTIONS:
        assert heading in second and body in second


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    preview = output / "sample.html"
    make_html(preview)
    preview_html = preview.read_text(encoding="utf-8")
    expected_text = (TITLE, HEADER, FOOTER, *(item for pair in SECTIONS for item in pair))
    assert all(html.escape(text) in preview_html for text in expected_text)
    make_docx(output / "sample.docx")
    make_pdf(output / "sample.pdf")
    verify_pdf(output / "sample.pdf")
    tex = output / "sample.tex"
    make_tex(tex)
    latex_source = tex.read_text(encoding="utf-8")
    assert all(escape_tex(text) in latex_source for text in expected_text)
    engine = shutil.which("pdflatex")
    if engine and shutil.which("kpsewhich") and subprocess.run(
        ["kpsewhich", "pdflatex.fmt"], capture_output=True, check=False
    ).returncode == 0:
        result = subprocess.run(
            [engine, "-no-shell-escape", "-halt-on-error", "-interaction=nonstopmode", "-jobname=sample-latex", tex.name],
            cwd=output, capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise RuntimeError(result.stdout[-2500:])
        verify_pdf(output / "sample-latex.pdf")
        print("PASS: LaTeX compiled with pdfLaTeX. Content and two pages verified.")
    else:
        print("SKIP: usable pdfLaTeX format unavailable. Verified generated LaTeX source text.")
    print("PASS: HTML content, DOCX structure and ReportLab PDF text and two pages verified.")


if __name__ == "__main__":
    main()
