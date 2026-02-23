import pytesseract
from pdf2image import convert_from_path

def extract_cbc_content(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    page = pages[0]
    w, h = page.size

    # Ignore left menu completely
    content = page.crop((int(w * 0.25), 0, w, h))

    text = pytesseract.image_to_string(
        content,
        lang="eng",
        config="--psm 6"
    ) or ""

    return text

