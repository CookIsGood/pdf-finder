import cv2, pytesseract, re, io
from fuzzywuzzy import fuzz
import logging
import base64
from buisness_logic.DocumentTools import DocumentConverter, DocumentCropInsertion


class DocumentRecognizerCore:
    def __init__(self, min_area, max_area, pattern: str):
        self._logger_doc_rec_core = logging.getLogger(__name__)
        self._logger_doc_rec_core.setLevel(logging.DEBUG)

        self._pattern = pattern
        self._min_area = min_area
        self._max_area = max_area

    def _search_match(self, block_text: str, block_area: int, block_cords: list,
                     pattern_search: str):
        results = []
        if re.search(pattern_search, block_text):
            results.append([block_area, block_cords])
            return results
        splited_text = self._split_text(block_text)
        string_to_match = pattern_search
        for line_splited_text in splited_text:
            for item in line_splited_text:
                result = fuzz.ratio(string_to_match, item)
                if result >= 70:  # процент совпадения, который должен быть
                    results.append([block_area, block_cords])
        return results

    def find_block_cords(self, image, pattern: str):
        if self._min_area <= 0 or self._max_area <= 0:
            raise ValueError("Area cannot be negative!")
        if self._min_area >= self._max_area:
            self._max_area = self._min_area
        results = []
        for i in range(1, 7):  # количество фильтраций текста
            image, line_items_coordinates, areas = self._mark_region(image, i)
            for j, k in zip(range(len(line_items_coordinates)), range(len(areas))):
                try:
                    if self._min_area < areas[k] <= self._max_area:  # area a block
                        img_crop = image[line_items_coordinates[j][0][1]:line_items_coordinates[j][1][1],
                                   line_items_coordinates[j][0][0]:line_items_coordinates[j][1][0]]
                        ret, thresh1 = cv2.threshold(img_crop, 120, 255, cv2.THRESH_BINARY)
                        text = str(pytesseract.image_to_string(thresh1, lang='eng', config='--psm 6', ))
                        match_in_text = self._search_match(text, areas[k], line_items_coordinates[j],
                                                          pattern)
                        if match_in_text:
                            results.append(match_in_text)
                except TypeError:
                    self._logger_doc_rec_core.warning("Incorrect values ​​passed")
                    raise ValueError("Incorrect values ​​passed")
        self._logger_doc_rec_core.debug("All blocks found")
        return results

    @staticmethod
    def _mark_region(image, iterations):

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
    def _split_text(text: str):
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            new_lines.append(line.split(" "))
        return new_lines

    @staticmethod
    def _find_min_area(blocks: list) -> tuple:
        res, cords = [], []
        for item in blocks:
            for elem in item:
                res.append(elem[0])
                cords.append(elem[1])
        index = res.index(min(res))
        return cords, index

    @staticmethod
    def _find_center(points: list) -> tuple:
        result_x = (points[1][0] + points[0][0]) / 2
        result_y = (points[1][1] + points[0][1]) / 2
        return int(result_x), int(result_y)


class DocumentRecognizer(DocumentRecognizerCore, DocumentCropInsertion):
    def __init__(self, **kwargs):
        self._logger_doc_rec = logging.getLogger(__name__)
        self._logger_doc_rec.setLevel(logging.DEBUG)

        self._doc_converter = DocumentConverter(kwargs.get('b64_data'),
                                                kwargs.get('start_page', None),
                                                kwargs.get('stop_page', None))
        self._crop_width = kwargs.get('crop_width', 300)
        self._crop_height = kwargs.get('crop_height', 150)
        self._crop_color = kwargs.get('crop_color', "#ffffff")
        super().__init__(kwargs.get('min_area', 5000),
                         kwargs.get('max_area', 35000),
                         str(kwargs.get('pattern', "PlaceForStamp")))

    def run(self):
        new_pages, pages, num_pages, count_pages = self._doc_converter.get_pages_info()
        result_matches = self._find_stamp_coordinates()
        msg = self._post_processing_cords(result_matches, count_pages, pages)
        self._logger_doc_rec.debug('Message generation completed')

        return msg

    def _find_stamp_coordinates(self):
        images = self._doc_converter.get_images()
        new_pages, pages, num_pages, count_pages = self._doc_converter.get_pages_info()

        crop = self.get_crop(self._crop_width, self._crop_height, self._crop_color)
        result_matches = []
        for i in range(len(images)):
            blocks = self.find_block_cords(images[i], pattern=self._pattern)
            if len(blocks) != 0:
                cords, index = self._find_min_area(blocks)
                x, y = self._find_center(cords[index])
                pages[num_pages[i]].paste(crop, self.get_crop_position(x, y,
                                                                       self._crop_width,
                                                                       self._crop_height), crop)
                result_matches.append(
                    {
                        "page": num_pages[i] + 1,
                        "coords": {
                            "x": x,
                            "y": y
                        }
                    })
            procent = self._calc_progress_recognize(i, len(images))
            self._logger_doc_rec.info(f'Done on {procent}%/100%')
        if len(result_matches) == 0:
            self._logger_doc_rec.warning("Could not find keyword")
            raise ValueError("Could not find keyword")

        self._logger_doc_rec.debug('Message generation completed')

        return result_matches

    def _post_processing_cords(self, result_matches, count, pages: list):
        buffer = io.BytesIO()
        pages[0].save(buffer, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
        encoded_string = base64.b64encode(buffer.getvalue())
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

    @staticmethod
    def _calc_progress_recognize(iter, count_iterations) -> int:
        count_iterations_one_procent = count_iterations / 100
        progress = iter / count_iterations_one_procent
        return int(progress)
