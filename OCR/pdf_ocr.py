from OCR.image_ocr import OCR
from OCR.pdf_overlay import PdfGenerator


class PdfOverlay:
    def __init__(self):
        self.pdf = PdfGenerator()
 
    def validate_json(json):
        if not json["pages"][0]["Modified_image"]:
             raise ValueError("Error: 'image' field is either missing or empty.")




    def run_pdfoverlay(self,json,out_dir,output_name):
       self.validate_json(json)
       self.pdf.create_overlay_pdf(json,out_dir,output_name)
    

                