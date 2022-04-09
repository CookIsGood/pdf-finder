import cv2, pytesseract, re, io, os
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError
import codecs
from fuzzywuzzy import fuzz
import binascii
import numpy as np
import logging
from PIL import Image
import base64


class DocumentRecognizerCore:
    def __init__(self, min_area, max_area, pattern: str):
        self._pattern = pattern
        self._min_area = min_area
        self._max_area = max_area
        self._logger_doc_rec_core = logging.getLogger(__name__)
        self._logger_doc_rec_core.setLevel(logging.DEBUG)

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
        for i in range(1, 7):  # количество фильтраций текста
            image, line_items_coordinates, areas = self.mark_region(image, i)
            for j, k in zip(range(len(line_items_coordinates)), range(len(areas))):
                try:
                    if self._min_area < areas[k] <= self._max_area:  # area a block
                        img_crop = image[line_items_coordinates[j][0][1]:line_items_coordinates[j][1][1],
                                   line_items_coordinates[j][0][0]:line_items_coordinates[j][1][0]]
                        ret, thresh1 = cv2.threshold(img_crop, 120, 255, cv2.THRESH_BINARY)
                        text = str(pytesseract.image_to_string(thresh1, lang='eng', config='--psm 6', ))
                        match_in_text = self.search_match(text, areas[k], line_items_coordinates[j],
                                                          pattern)
                        if match_in_text:
                            results.append(match_in_text)
                except TypeError:
                    self._logger_doc_rec_core.warning("Incorrect values ​​passed")
                    raise ValueError("Incorrect values ​​passed")
        self._logger_doc_rec_core.debug("All blocks found")
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
    def find_min_area(blocks: list) -> tuple:
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
    def __init__(self, **kwargs):
        self._logger_doc_rec = logging.getLogger(__name__)
        self._logger_doc_rec.setLevel(logging.DEBUG)
        self._min_area = kwargs.get('min_area', 5000)
        self._max_area = kwargs.get('max_area', 35000)
        self._start_page = kwargs.get('start_page', None)
        self._stop_page = kwargs.get('stop_page', None)
        self._pattern = str(kwargs.get('pattern', "PlaceForStamp"))

        super().__init__(self._min_area, self._max_area, self._pattern,)

    def find_stamp_coordinates(self, base64_data: str):
        binary_pdf = self.base64_to_pdf(base64_data=base64_data.encode('utf-8'))
        pages, num_pages, count_pages = self.bpdf_to_pages(binary_pdf, self._start_page, self._stop_page)
        images = self.pages_to_images(pages)
        crop_img = Image.new(mode="RGBA", size=(300, 150), color='white')
        result_matches = []
        for i in range(len(images)):
            blocks = self.find_block_cords(images[i], pattern=self._pattern)
            if len(blocks) != 0:
                cords, index = self.find_min_area(blocks)
                x, y = self.find_center(cords[index])
                pages[num_pages[i]].paste(crop_img, (x-200, y-100),  crop_img)
                result_matches.append(
                    {
                        "page": num_pages[i]+1,
                        "coords": {
                            "x": x,
                            "y": y
                        }
                    })
            procent = self.calc_progress_recognize(i, len(images))
            self._logger_doc_rec.info(f'Done on {procent}%/100%')
        if len(result_matches) == 0:
            self._logger_doc_rec.warning("Could not find keyword")
            raise ValueError("Could not find keyword")

        msg = self.post_processing_cords(result_matches, count_pages, pages)
        self._logger_doc_rec.debug('Message generation completed')

        return msg

    @staticmethod
    def calc_progress_recognize(iter, count_iterations) -> int:
        count_iterations_one_procent = count_iterations / 100
        progress = iter / count_iterations_one_procent
        return int(progress)

    def post_processing_cords(self, result_matches, count, pages: list):
        buffer = io.BytesIO()
        os.makedirs("/app/out_pdf", exist_ok=True)
        pages[0].save("/app/out_pdf/mypdf.pdf", "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
        with open("/app/out_pdf/mypdf.pdf", "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        #b64_doc = base64.b64encode(codecs.decode((buffer.getvalue())., 'UTF-8'))
        msg = {
            "data":
                {
                    "count_pages": count
                }
        }
        msg["data"]["matches"] = result_matches
        msg["data"]["output_doc"] = str(encoded_string.decode('utf-8'))
        self._logger_doc_rec.debug('Splitting binary pdf into images is complete')

        return msg

    def base64_to_pdf(self, base64_data: bytes):
        try:
            binary_pdf = codecs.decode(base64_data, 'base64')
        except binascii.Error:
            logging.warning("key 'b64_data' does not contain base64 date.")
            raise ValueError("key 'b64_data' does not contain base64 date.")
        self._logger_doc_rec.debug('Base64_pdf to binary_pdf conversion completed')
        return binary_pdf

    def bpdf_to_pages(self, binary_pdf: bytes, start_page, stop_page) -> tuple:

        try:
            pages = convert_from_bytes(binary_pdf)
        except PDFPageCountError:
            logging.warning("Splitting binary pdf into images cannot be complete")
            raise ValueError("Page count error!")
        count_pages = len(pages)
        num_pages = [i for i in range(len(pages))]
        try:
            pages = pages[start_page:stop_page:None]
            num_pages = num_pages[start_page:stop_page:None]
        except TypeError:
            self._logger_doc_rec.warning("Incorrect values ​​passed")
            raise ValueError("Incorrect values ​​passed")

        self._logger_doc_rec.debug('Splitting binary pdf into images is complete')
        return pages, num_pages, count_pages

    @staticmethod
    def pages_to_images(pages: list) -> list:
        result = []
        for item in pages:
            buffer = io.BytesIO()
            item.save(buffer, format='JPEG')
            result.append(cv2.imdecode(np.frombuffer(buffer.getvalue(), dtype='uint8'),
                                       cv2.COLOR_BGR2RGB))
        return result
