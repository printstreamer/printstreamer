""" PDF-specific literals and code. """

import fitz  # PyMuPDF
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


def decode_color(color_int):
    # PyMuPDF returns color as int — decode to RGB
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)

def extract_pdf_content(input_pdf_path, output_dir="extracted"):
    # os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(input_pdf_path)
    extracted = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        text = page.get_text()
        # image_list = page.get_images(full=True)
        # images = []
        # for img_index, img in enumerate(image_list):
        #     xref = img[0]
        #     base_image = doc.extract_image(xref)
        #     image_bytes = base_image["image"]
        #     image_ext = base_image["ext"]
        #     image_filename = f"page{page_number + 1}_img{img_index + 1}.{image_ext}"
        #     image_path = os.path.join(output_dir, image_filename)
        #     with open(image_path, "wb") as img_file:
        #         img_file.write(image_bytes)
        #     images.append(image_path)
        extracted.append({
            "page": page_number + 1,
            "text": text,
            "images": []  # images
        })
    doc.close()
    return extracted

def create_pdf_from_content(output_pdf_path, content):
    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    width, height = A4
    for item in content:
        text = item["text"]
        images = item["images"]
        # Write text (basic)
        text_object = c.beginText(40, height - 40)
        for line in text.splitlines():
            text_object.textLine(line)
        c.drawText(text_object)
        # Add images (resized if necessary)
        y_offset = 150
        for img_path in images:
            try:
                img = Image.open(img_path)
                img.thumbnail((400, 400), Image.ANTIALIAS)
                c.drawImage(ImageReader(img), 40, height - y_offset - img.height, width=img.width, height=img.height)
                y_offset += img.height + 20
            except Exception as e:
                print(f"Failed to draw image {img_path}: {e}")
        c.showPage()
    c.save()


class StreamPDF:
    """ Code functions of pdf printstream files.

    # Extract example:
    input_pdf = "input.pdf"  # your source PDF
    extracted_data = extract_pdf_content(input_pdf)

    # Compose example:
    output_pdf = "output_generated.pdf"
    create_pdf_from_content(output_pdf, extracted_data)

    """

    def __init__(self):
        pass
