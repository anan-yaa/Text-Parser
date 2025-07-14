import pdfplumber
import re

def parse_invoice(filepath):
    with pdfplumber.open(filepath) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    total = re.search(r"Total\s*[:\-]?\s*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    total_value = total.group(1) if total else "Not found"
    line_items = []
    for match in re.finditer(r"(\w+)\s+(\d+)\s+\$([\d,]+\.\d{2})", text):
        line_items.append({
            "Item": match.group(1),
            "Quantity": match.group(2),
            "Price": match.group(3)
        })
    return {
        "Total": total_value,
        "Line Items": line_items if line_items else "Not found"
    }