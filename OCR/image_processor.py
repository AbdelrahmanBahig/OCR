from OCR.image_ocr import OCRProcess , OCRParagraph
import os
import json
class OCR:
    def __init__(self):
        self.configurations = {
            'engine_urls': [],
            'payload': {},
            'save_text': False,
            'remove_modified_image': False,
        }
        self.ocr_process = OCRProcess(self.configurations['engine_urls'], self.configurations['payload'])       
    def set_configurations(self, config ):
        for key,value in config.items():
            if key in self.configurations:
             self.configurations[key] = value

    def validate_manadatory_config(self , config):
       
       mandatory_keys = ['engine_url', 'payload']
       missing_keys = [key for key in mandatory_keys if key not in config]
       if missing_keys:
          raise ValueError (f"Missing mandatory keys {', '.join(missing_keys)}")
       
    #    for key in mandatory_keys:
    #        if not isinstance(config[key], list) or not config[key]:
    #         raise ValueError(f"{key} must be a non-empty ")

    def save_json(self , img , ocr_result):
        try:
            txt_file = img.replace(".jpg", ".json")
            if os.path.exists(txt_file):
                return 0
            json.dump(ocr_result, open(txt_file, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            print("done: ", img)
        except Exception as e:
            print(e)

    def perform_image_ocr(self , image):
        config = self.configurations
        self.validate_manadatory_config(config)
        ocr_result = self.ocr_process.ocr_recognition(image)
        if self.configurations['remove_modified_image']:
            ocr_result = self.remove_modified_image(ocr_result)

        if self.ocr.configurations['save_text']:
            self.ocr_process.save_ocr_text(image, ocr_result)
        

        # SAVE JSON 
        self.save_json(image,ocr_result)

        return ocr_result