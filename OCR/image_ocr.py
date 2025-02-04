import requests
import os
import json

class OCRServerProcess:
    def __init__(self, ocr_urls):
        self.OCR_URLs = ocr_urls
        self.current_url_index = 0
        self.headers = {}

    def get_headers(self):
        return {}

    def get_body(self):
        return {}

    def get_ocr_url(self):
        url = self.OCR_URLs[0]
       # self.current_url_index = (self.current_url_index + 1) % len(self.OCR_URLs)
        return url

    def ocr_recognition(self, image_path):
        """
            @return dict: The parsed JSON response from the OCR server, or an empty dict if the request fails.
        """
        files = [('file', (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg'))]
        headers = self.get_headers()
        general_payload = self.get_body()
        url = self.get_ocr_url()
        response = requests.request("POST", url, headers=headers, data=general_payload, files=files, verify=False,
                                    timeout=40000)
        if response.status_code == 200:
            print("OCR request successful")
            return response.json()
        print("OCR request failed:", response.json())
        return {}

class TitlesOCRProcess(OCRServerProcess):
    def __init__(self, ocr_urls, payload):
        super().__init__(ocr_urls)
        self.payload = payload

    def _get_language(self):
        lang = {'en': 'English/Latest', 'ar': 'Arabic/Latest', 'ar-en': 'Multi/Ar-En'}
        language = self.payload.get('lanaguage')
        return lang.get(language, 'Multi/Ar-En')

    def get_body(self):
        return {
            "enable_line_segmentation": self.payload.get('enable_line_segmentation' , True),
            "language": self._get_language(),
            "additional_features":  self.payload.get('additional_features' , True),  # Add extra features
        }


class OCRProcess(OCRServerProcess):
    def __init__(self, ocr_urls, payload):
        self.OCR = TitlesOCRProcess(ocr_urls, payload)
    def get_text(self, ocr_output):
        text = []
        for page in ocr_output["pages"]:
            for zone in page["zones"]:
                for paragraph in zone["paragraphs"]:
                    text.extend(line["text"] for line in paragraph["lines"])
        return " ".join(text)

    def is_there_text_file(self, img):
        txt_file = img.replace(".jpg", ".txt")
        if os.path.exists(txt_file):
            return True
        return os.path.splitext(img)[0] + ".txt"  # Create filename with .txt extension

    def save_ocr_text(self, img, ocr_result):
        """Saves OCR text to a text file with the same name as the image."""
        txt_path = os.path.splitext(img)[0] + ".txt"  # Create filename with .txt extension
        with open(txt_path, "w", encoding="utf-8") as text_file:
            text_file.write(self.get_text(ocr_result))  # Write text to file

    def remove_modified_image(self, json):
        json["pages"][0]["Modified_image"] = ""
        return json

    

    def my_run(self, img,ocr_result):
        try:
            if any([self.is_there_text_file(img), ocr_result]):
                self.save_ocr_text(img, ocr_result)
                print("done: ", img)
        except Exception as e:
            print(e)

