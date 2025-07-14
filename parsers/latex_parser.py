import latex2mathml.converter

def parse_latex(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        latex_code = f.read()
    try:
        mathml = latex2mathml.converter.convert(latex_code)
        return {"MathML": mathml}
    except Exception as e:
        return {"Raw LaTeX": latex_code, "Error": str(e)}