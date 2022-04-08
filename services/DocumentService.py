import cv2, pytesseract, re, io
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError
import codecs
from fuzzywuzzy import fuzz
import binascii
import numpy as np


class DocumentRecognizerCore:
    def __init__(self, pattern: str = "PlaceForStamp",
                 min_area=3000,
                 max_area=100000):
        self._pattern = pattern
        self._min_area = min_area
        self._max_area = max_area

    def search_match(self, block_text: str, block_area: int, block_cords: list,
                     pattern_search: str):
        results = []
        if re.search(pattern_search, block_text):
            results.append([block_area, block_cords])
            return results
        splited_text = self.split_text(block_text)
        string_to_match = pattern_search
        for line_splited_text in splited_text:
            for item in line_splited_text:
                result = fuzz.ratio(string_to_match, item)
                if result >= 70:  # процент совпадения, который должен быть
                    results.append([block_area, block_cords])
        return results

    def find_block_cords(self, image, pattern: str):
        results = []
        for i in range(1, 4):  # количество фильтраций текста
            image, line_items_coordinates, areas = self.mark_region(image, i)
            for j, k in zip(range(len(line_items_coordinates)), range(len(areas))):
                if self._min_area < areas[k] <= self._max_area:  # area a block
                    img_crop = image[line_items_coordinates[j][0][1]:line_items_coordinates[j][1][1],
                               line_items_coordinates[j][0][0]:line_items_coordinates[j][1][0]]
                    ret, thresh1 = cv2.threshold(img_crop, 120, 255, cv2.THRESH_BINARY)
                    text = str(pytesseract.image_to_string(thresh1, lang='eng', config='--psm 6', ))
                    match_in_text = self.search_match(text, areas[k], line_items_coordinates[j],
                                                      pattern)
                    if match_in_text:
                        results.append(match_in_text)
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
    def pages_to_images(pages: list) -> list:
        result = []
        for item in pages:
            buffer = io.BytesIO()
            item.save(buffer, format='JPEG')
            result.append(cv2.imdecode(np.frombuffer(buffer.getvalue(), dtype='uint8'),
                                       cv2.COLOR_BGR2RGB))
        return result

    @staticmethod
    def find_min_area(blocks: list):
        res, cords = [], []
        for item in blocks:
            for elem in item:
                res.append(elem[0])
                cords.append(elem[1])
            index = res.index(min(res))
            return cords, index

    @staticmethod
    def find_center(points: list) -> tuple:
        result_x = (points[1][0] + points[0][0]) / 2
        result_y = (points[1][1] + points[0][1]) / 2
        return int(result_x), int(result_y)



class DocumentRecognizer(DocumentRecognizerCore):
    def __init__(self, pattern: str, min_area: int, max_area: int):
        super().__init__(pattern, min_area, max_area)

    def find_stamp_coordinates(self, base64_data: str):
        binary_pdf = self.base64_to_pdf(base64_data=base64_data.encode('utf-8'))
        pages = self.bpdf_to_pages(binary_pdf)
        images = self.pages_to_images(pages)
        result_matches = []
        for i in range(len(images)):
            blocks = self.find_block_cords(images[i], pattern=self._pattern)
            if len(blocks) != 0:
                cords, index = self.find_min_area(blocks)
                x, y = self.find_center(cords[index])
                result_matches.append(
                    {
                        "page": i + 1,
                        "coords": {
                            "x": x,
                            "y": y
                        }
                    })
        if len(result_matches) == 0:
            raise ValueError("Failed to calculate coordinates!")

        msg = self.post_processing_cords(result_matches, len(images))

        return msg

    @staticmethod
    def post_processing_cords(result_matches, count_pages):

        msg = {
            "data":
                {
                    "count_pages": count_pages,
                }
        }
        msg["data"]["matches"] = result_matches

        return msg

    @staticmethod
    def base64_to_pdf(base64_data: bytes):
        try:
            binary_pdf = codecs.decode(base64_data, 'base64')
        except binascii.Error:
            raise ValueError("key 'b64_data' does not contain base64 date.")
        return binary_pdf

    @staticmethod
    def bpdf_to_pages(binary_pdf: bytes):
        try:
            pages = convert_from_bytes(binary_pdf)
        except PDFPageCountError:
            raise ValueError("Page count error!")
        return pages


class DocumentService:

    @staticmethod
    def publish_msg(data):
        try:
            content = data['data']
            pattern = content["pattern"]
            b64_data = content["b64_data"]
        except KeyError:
            raise ValueError("No key required!")
        except ValueError:
            raise ValueError("Value must be JSON!")
        recognizer = DocumentRecognizer(str(pattern), min_area=5000, max_area=35000)
        return recognizer.find_stamp_coordinates(b64_data)
