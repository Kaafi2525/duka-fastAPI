from fpdf import FPDF

pdf=FPDF()

def generate_pdf(text,file_name="receipts/generated.pdf"):
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(200, 10, txt=text, align='C')
    pdf.output(f"{file_name}")

