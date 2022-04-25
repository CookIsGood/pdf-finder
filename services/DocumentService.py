import cv2, pytesseract, re, io
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError
import codecs
from fuzzywuzzy import fuzz
import binascii
import numpy as np
import logging


class DocumentRecognizerCore:
    def __init__(self, pattern: str = "e-mail:"):
        self._pattern = pattern
        self.gunicorn_error_logger = logging.getLogger('gunicorn.error')
        self._logger_doc_rec_core = logging.getLogger(__name__)
        for item in self.gunicorn_error_logger.handlers:
            self._logger_doc_rec_core.addHandler(item)
        self._logger_doc_rec_core.setLevel(logging.DEBUG)

    def search_match(self, block_text: str, block_area: int, block_cords: list,
                     pattern_search: str, pattern_search_fullmatch: list):
        results = []
        for item in pattern_search_fullmatch:
            if re.search(item, block_text):
                results.append([block_area, block_cords])
        if len(results) == 0:
            splited_text = self.split_text(block_text)
            string_to_match = pattern_search
            for line_splited_text in splited_text:
                for item in line_splited_text:
                    result = fuzz.ratio(string_to_match, item)
                    if result >= 70:  # процент совпадения, который должен быть
                        results.append([block_area, block_cords])
        return results

    def find_block_cords(self, img):
        results = []
        for i in range(2, 7):  # количество фильтраций текста
            image, line_items_coordinates, areas = self.mark_region(img, i)
            for j, k in zip(range(len(line_items_coordinates)), range(len(areas))):
                if 45000 < areas[k] <= 250000:  # area a block
                    img_crop = image[line_items_coordinates[j][0][1]:line_items_coordinates[j][1][1],
                               line_items_coordinates[j][0][0]:line_items_coordinates[j][1][0]]
                    ret, thresh1 = cv2.threshold(img_crop, 120, 255, cv2.THRESH_BINARY)
                    text = str(pytesseract.image_to_string(thresh1, lang='eng', config='--psm 6', ))
                    match_in_text = self.search_match(text, areas[k], line_items_coordinates[j],
                                                      "e-mail:", ["e-mail:", "email:", "mail", "email"])
                    if match_in_text:
                        results.append(match_in_text)
        self._logger_doc_rec_core.info("All blocks found")
        return results

    @staticmethod
    def mark_region(image, iterations):

        # define threshold of regions to ignore
        THRESHOLD_REGION_IGNORE = 40

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 30)

        # Dilate to combine adjacent text contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilate = cv2.dilate(thresh, kernel, iterations=iterations)

        # Find contours, highlight text areas, and extract ROIs
        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        line_items_coordinates = []
        areas = []
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h

            if w < THRESHOLD_REGION_IGNORE or h < THRESHOLD_REGION_IGNORE:
                continue
            image = cv2.rectangle(image, (x, y), (x + w, y + h), color=(255, 0, 255), thickness=3)
            line_items_coordinates.append([(x, y), (x + w, y + h)])
            areas.append(area)

        return image, line_items_coordinates, areas

    @staticmethod
    def split_text(text: str):
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            new_lines.append(line.split(" "))
        return new_lines

    @staticmethod
    def find_min_area(blocks: list):
        res, cords = [], []
        for item in blocks:
            for elem in item:
                res.append(elem[0])
                cords.append(elem[1])
        try:
            index = res.index(min(res))
            return cords, index
        except ValueError:
            raise ValueError("Failed to calculate coordinates")


class DocumentRecognizer(DocumentRecognizerCore):
    def __init__(self):
        super().__init__()
        self.gunicorn_error_logger = logging.getLogger('gunicorn.error')
        self._logger_doc_rec = logging.getLogger(__name__)
        for item in self.gunicorn_error_logger.handlers:
            self._logger_doc_rec.addHandler(item)
        self._logger_doc_rec.setLevel(logging.DEBUG)

    def find_stamp_coordinates(self, base64_data: str):
        try:
            binary_pdf = self.base64_to_pdf(base64_data=base64_data.encode('utf-8'))
        except AttributeError:
            self._logger_doc_rec.warning(f"key 'data' does not contain base64 date.")
            raise ValueError("key 'data' does not contain base64 date.")
        img = self.make_img(binary_pdf)

        blocks = self.find_block_cords(img)
        cords, index = self.find_min_area(blocks)
        result = self.post_processing_cords(cords, index)

        msg = {
            'data':
                {
                    'x': result[0],
                    'y': result[1] - 250
                }
        }
        self._logger_doc_rec.info(f'Data sent!')
        return msg

    def post_processing_cords(self, cords: list, index: int):
        x_cord = int(1654 / 2)
        y_cord = cords[index][0][1]

        self._logger_doc_rec.info(f'Data is ready to be sent!')
        return x_cord, y_cord

    def base64_to_pdf(self, base64_data: bytes):
        try:
            binary_pdf = codecs.decode(base64_data, 'base64')
        except binascii.Error:
            self._logger_doc_rec.warning(f"key 'data' does not contain base64 date.")
            raise ValueError("key 'data' does not contain base64 date.")

        self._logger_doc_rec.info(f'File decoded successfully!')
        return binary_pdf

    def make_img(self, binary_pdf: bytes):
        try:
            pages = convert_from_bytes(binary_pdf)
        except PDFPageCountError:
            self._logger_doc_rec.warning(f'The PDF file could not be read. This error usually occurs if b64_data is corrupted.')
            raise ValueError("Failed to calculate coordinates")
        image = pages[len(pages) - 1]
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        self._logger_doc_rec.info(f'The last page of the file has been successfully converted to an image!')
        return cv2.imdecode(np.frombuffer(buffer.getvalue(), dtype='uint8'),
                            cv2.COLOR_BGR2RGB)


class DocumentService:
    def __init__(self):
        self.gunicorn_error_logger = logging.getLogger('gunicorn.error')
        self._logger_doc_service = logging.getLogger(__name__)
        for item in self.gunicorn_error_logger.handlers:
            self._logger_doc_service.addHandler(item)
        self._logger_doc_service.setLevel(logging.DEBUG)

    def publish_msg(self, data):
        try:
            content = data['data']
        except KeyError:
            self._logger_doc_service.warning(f'No key required!')
            raise ValueError("No key required!")
        except ValueError:
            self._logger_doc_service.warning(f'Incorrect value!')
            raise ValueError("Incorrect value!")
        except TypeError:
            self._logger_doc_service.warning(f'The object being sent is not JSON')
            raise ValueError("The object being sent is not JSON")
        recognizer = DocumentRecognizer()
        return recognizer.find_stamp_coordinates(content)

