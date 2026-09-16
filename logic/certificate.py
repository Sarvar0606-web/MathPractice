"""Sertifikat (diplom) PDF generatsiyasi — fpdf2 yordamida.

Foydalanuvchi biror bo'lim (section) bo'yicha yetarlicha savolga (>=40)
yuqori aniqlik bilan (>=85%) javob bersa, shu bo'lim uchun chiroyli
PDF sertifikat generatsiya qilinadi."""
from pathlib import Path

from fpdf import FPDF

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

ACCENT = (99, 102, 241)
DARK = (30, 41, 59)


def generate_certificate_pdf(full_name: str, section_label: str, accuracy: int,
                              total: int, date_str: str) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.add_font("DejaVu", "", str(FONT_REGULAR))
    pdf.add_font("DejaVu", "B", str(FONT_BOLD))

    page_w, page_h = pdf.w, pdf.h

    # Dekorativ ramka
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(2.2)
    pdf.rect(8, 8, page_w - 16, page_h - 16)
    pdf.set_line_width(0.5)
    pdf.rect(12, 12, page_w - 24, page_h - 24)

    pdf.set_text_color(*ACCENT)
    pdf.set_font("DejaVu", "B", 34)
    pdf.set_xy(0, 32)
    pdf.cell(page_w, 15, "SERTIFIKAT", align="C")

    pdf.set_text_color(*DARK)
    pdf.set_font("DejaVu", "", 13)
    pdf.set_xy(0, 56)
    pdf.cell(page_w, 8, "Ushbu sertifikat quyidagi shaxsga topshiriladi:", align="C")

    pdf.set_text_color(*ACCENT)
    pdf.set_font("DejaVu", "B", 27)
    pdf.set_xy(0, 70)
    pdf.cell(page_w, 14, full_name, align="C")

    pdf.set_text_color(*DARK)
    pdf.set_font("DejaVu", "", 13.5)
    pdf.set_xy(30, 92)
    body = (
        f'"{section_label}" bo\'limi bo\'yicha {total} tadan ortiq savolga '
        f"{accuracy}% aniqlik bilan javob bergani uchun MathBot tomonidan taqdim etiladi."
    )
    pdf.multi_cell(page_w - 60, 8, body, align="C")

    pdf.set_font("DejaVu", "", 11.5)
    pdf.set_xy(20, page_h - 30)
    pdf.cell((page_w - 40) / 2, 8, f"Sana: {date_str}", align="L")

    pdf.set_font("DejaVu", "B", 13)
    pdf.set_xy(20, page_h - 30)
    pdf.cell(page_w - 40, 8, "MathBot", align="R")

    out = pdf.output()
    return bytes(out)
