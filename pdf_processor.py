  ```python
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import os

def extract_pdf_text(pdf_path):
    """
    Extract text from PDF using both PyPDF2 and OCR.
    Returns combined text.
    """
    text = ""
    
    try:
        # Method 1: Try PyPDF2 first (for searchable PDFs)
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
    
    # If text is empty or too short, try OCR
    if len(text.strip()) < 100:
        try:
            print("Attempting OCR extraction...")
            images = convert_from_path(pdf_path, dpi=300)
            for img in images:
                ocr_text = pytesseract.image_to_string(img)
                text += "\n" + ocr_text
        except Exception as e:
            print(f"OCR extraction failed: {e}")
    
    return text

def extract_image_text(image_path):
    """
    Extract text from image files using OCR.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Image extraction failed: {e}")
        return ""
```
