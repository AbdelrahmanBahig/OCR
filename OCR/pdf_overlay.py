import base64
import glob
import json
import os
from collections import namedtuple
from io import BytesIO

from PIL import Image
from arabic_reshaper import *
from bidi.algorithm import get_display
from dotenv import load_dotenv
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


class PdfGenerator:
    """Generates overlay PDFs from OCR output."""

    def __init__(self, font_path="Arial.ttf", direction="rtl"):
        """Initializes the PdfGenerator with default values.

        Args:
            font_path (str, optional): Path to the font file to use. Defaults to "Arial".
            direction (str, optional): Text direction, either "rtl" (right-to-left) or "ltr" (left-to-right). Defaults to "rtl".
        """
        self.data_paths = json.loads(os.getenv("DATA_PATH"))
        self.font_path = font_path
        self.direction = direction
        self.fontname = "Arial"

        # Load and configure ArabicReshaper
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
        load_dotenv(dotenv_path)  # Load environment variables if present

        reshape_config = reshaper_config.default_config
        reshape_config["support_ligatures"] = False  # Adjust as needed
        self.reshape_class = ArabicReshaper(reshape_config)

        # Set DPI (dots per inch) for text measurement
        self.dpi = inch

    def process_data(self):
        for path in self.data_paths:
            print("Processing path:", path)
            self.process_files(path)

    def process_files(self, path):
        files = list(glob.glob(path + "**/*_sorted_scaled.json", recursive=True))
        files.extend(list(glob.glob(path + "**/*_sorted_scaled_thumbnail.json", recursive=True)))

        pdf_generator = PdfGenerator()  # Reuse the same instance for efficiency

        for in_dir in files:
            try:
                output_dir = "/".join(in_dir.split("/")[0:-1])
                output_name = in_dir.split("/")[-1].replace(".json", "_overlayed")
                pdf_path = os.path.join(output_dir, output_name + ".pdf")

                if os.path.exists(pdf_path):
                    continue

                print(f"Generating PDF for: {in_dir}")
                json_data = json.load(open(in_dir, encoding="utf-8"))
                pdf_generator.create_overlay_pdf(json_data, output_dir, output_name)
                print("PDF generated successfully.")

            except Exception as ex:
                print(f"Error: {ex}")

        print("Processing complete for path:", path)

    def parser(self, zones_data):
        """
        This Function used to parse zone from json File
        Inputs:
            zones_data List: a list of zones
        Returns:
            data : zones data after parsing it
        """
        data = []
        for zone in zones_data:
            paragraphs = zone["paragraphs"]
            for paragraph in paragraphs:
                lines = paragraph["lines"]
                for line in lines:
                    text = line["text"]
                    bottom_right_x = int(line["coordinates"]["bottom_right"]["x"])
                    bottom_right_y = int(line["coordinates"]["bottom_right"]["y"])
                    upper_left_x = int(line["coordinates"]["upper_left"]["x"])
                    upper_left_y = int(line["coordinates"]["upper_left"]["y"])
                    data.append([text, upper_left_x, upper_left_y, bottom_right_x, bottom_right_y])
        return data

    def register_font(self, fontname):
        """Attempts to register the given font with ReportLab."""
        try:
            pdfmetrics.registerFont(TTFont(fontname, self.font_path))
        except Exception as e:
            print(f"Error registering font: {e}", flush=True)

    def parse_zones(self, json_data):
        """Parses zone data from the JSON input."""
        zones = json_data["pages"][0]["zones"]
        return self.parser(zones)  # Assuming the 'parser' function is defined elsewhere

    def create_pdf_canvas(self, output_path, width, height):
        """Creates a PDF canvas with the specified dimensions."""
        return Canvas(output_path, pagesize=(width, height), pageCompression=1)

    def add_text_to_pdf(self, pdf, data, fontname, height):
        """Adds text elements from the parsed data to the PDF canvas."""
        for z in range(len(data)):
            elemtxt = data[z][0]

            # Apply Arabic reshaping (or remove this step if not needed)
            elemtxt = self.reshape_class.reshape(elemtxt)
            elemtxt = get_display(elemtxt)  # Assuming `get_display` is defined elsewhere

            if len(elemtxt) == 0:
                continue
            pxl_coords = data[z][1:]
            rect = namedtuple('Rect', ['x1', 'y1', 'x2', 'y2'])
            pt = rect._make(c for c in pxl_coords)

            text = pdf.beginText(direction=self.direction)
            fontsize = pt.y2 - pt.y1
            text.setFont(fontname, fontsize)

            # Calculate text width and adjust horizontal scaling if needed
            text_width = pdf.stringWidth(elemtxt, fontname, fontsize)
            if text_width != 0:
                # Convert pixel width to points using DPI
                adjusted_width = 100 * (pt.x2 - pt.x1) / (text_width / self.dpi)
                text.setHorizScale(adjusted_width)
            else:
                text.setHorizScale(0)

            text.setTextOrigin(pt.x1, height - pt.y2)
            text.textLine(elemtxt)
            pdf.drawText(text)

    def create_overlay_pdf(self, json_data, out_dir, output_name, hex_color="#000000"):
        """Generates an overlay PDF from OCR output."""
        try:
            self.register_font(self.fontname)
            image = Image.open(BytesIO(base64.b64decode(json_data["pages"][0]["image"])))
            width, height = image.size
            data = self.parse_zones(json_data)
            image_path = os.path.join(out_dir, output_name + ".jpg")
            image.save(image_path, quality=20, optimize=True)
            reader = ImageReader(image_path)
            pdf_path = os.path.join(out_dir, output_name + ".pdf")
            pdf = self.create_pdf_canvas(pdf_path, width, height)
            pdf.setFillColor(HexColor(hex_color))
            self.add_text_to_pdf(pdf, data, self.fontname, height)
            pdf.drawImage(reader, 0, 0, width=width, height=height)
            pdf.showPage()
            pdf.save()
            os.remove(image_path)
            return pdf_path
        except Exception as e:
            raise Exception(f"Unexpected Error: {e}") from e
