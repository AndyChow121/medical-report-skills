"""用 fpdf2 生成一个真实的测试 PDF：含 Figure 标题 + 关键统计量，
供 ocr --pdf 路径做端到端 smoke test。
"""
from fpdf import FPDF
from pathlib import Path

OUT = Path("figure_sample.pdf")

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=14)
pdf.cell(0, 10, "Figure 2. Kaplan-Meier survival curves for OS by treatment arm.", ln=1)
pdf.ln(2)
pdf.set_font("Helvetica", size=12)
pdf.cell(0, 8, "HR = 0.72 (95% CI 0.58-0.89), p = 0.003, N = 480.", ln=1)
pdf.ln(2)
pdf.set_font("Helvetica", size=11)
pdf.cell(0, 8, "Median OS: 19.6 months (experimental) vs 14.2 months (control).", ln=1)
pdf.cell(0, 8, "Schoenfeld residual test p = 0.42 (no violation of PH assumption).", ln=1)

pdf.output(str(OUT))
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
