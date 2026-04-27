import fitz  # This is PyMuPDF

def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    doc = fitz.open(pdf_path)
    text = ""
    
    # Loop through every page and grab the text
    for page in doc:
        text += page.get_text()
        
    return text

# Test it out
# (You'll need to put a sample resume PDF in your folder and change 'resume.pdf' to its name)
# print(extract_text_from_pdf("resume.pdf"))