from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)
pdf.multi_cell(0, 6, "Why: Why")
pdf.output("test.pdf")
print("Done")
