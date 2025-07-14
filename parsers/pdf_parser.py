import pdfplumber

def parse_pdf(filepath):
    with pdfplumber.open(filepath) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text