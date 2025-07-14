from pyresparser import ResumeParser

def parse_resume(filepath):
    data = ResumeParser(filepath).get_extracted_data()
    return data