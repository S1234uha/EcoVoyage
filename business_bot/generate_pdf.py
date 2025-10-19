from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

ROOT = Path(__file__).parent
SUMMARY_PATH = ROOT / "business_summary.txt"
PDF_PATH = ROOT / "about_business.pdf"


def draw_wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, leading: float = 14):
    from textwrap import wrap
    lines = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(wrap(paragraph, width=90))

    for line in lines:
        c.drawString(x, y, line)
        y -= leading
        if y < 1 * inch:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 10.5 * inch
    return y


def main():
    text = SUMMARY_PATH.read_text(encoding="utf-8") if SUMMARY_PATH.exists() else "EcoVoyage Travel — About"

    c = canvas.Canvas(str(PDF_PATH), pagesize=LETTER)
    width, height = LETTER

    c.setTitle("About EcoVoyage Travel")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, 10.5 * inch, "EcoVoyage Travel — About")

    c.setFont("Helvetica", 11)
    y = 10 * inch
    y = draw_wrapped_text(c, text, 1 * inch, y, max_width=6.5 * inch)

    c.showPage()
    c.save()
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()

