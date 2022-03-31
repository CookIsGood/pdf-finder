import cv2, pytesseract, os, re
from PIL import Image
from pdf2image import convert_from_path
import codecs, fnmatch
from fuzzywuzzy import fuzz
import binascii
import hashlib
import random


class DocumentService:

    def find_block_coordinates(self, base64_data: str):
        os.makedirs(f"protocols", exist_ok=True)
        os.makedirs(f"images", exist_ok=True)
        hash = hashlib.md5(base64_data.encode("utf-8"))
        filename = str(f'{hash.hexdigest()}_{str(random.randint(1, 100))}')
        try:
            self.base64_to_pdf(folder_name='protocols', name_pdf=filename,
                               base64_data=base64_data.encode('utf-8'))
        except binascii.Error:
            raise
        pdf_file = fnmatch.filter(os.listdir(f'protocols'), f'{filename}.pdf')[0]
        self._make_images('images', filename)
        jpg_file = fnmatch.filter(os.listdir(f'images'), f'{filename}.jpg')[0]

        blocks = self._find_block_cords(f'images/{jpg_file}')
        res, cords = [], []
        for item in blocks:
            for elem in item:
                res.append(elem[0])
                cords.append(elem[1])
        try:
            index = res.index(min(res))
        except ValueError:
            raise
        img = Image.open(f'images/{jpg_file}')
        x, y = img.size
        os.remove(f'images/{jpg_file}')
        os.remove(f'protocols/{filename}.pdf')
        msg = {
            'data':
                {
                    'x': int(x / 2),
                    'y': cords[index][0][1] - 250
                }
        }
        return msg

    def _make_images(self, folder_name: str, filename: str):
        pdfs = f"protocols/{filename}.pdf"
        pages = convert_from_path(pdfs)
        image_name = f"{filename}.jpg"
        pages[len(pages) - 1].save(f"{folder_name}/{image_name}", "JPEG")

    def _mark_region(self, image_path, iterations):
        image = cv2.imread(image_path)

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

    def _find_match_in_text(self, text: str, area: int, cords: list):
        match = re.search("e-mail:", text)
        match1 = re.search("email:", text)
        match2 = re.search("mail", text)
        results = []
        if match or match1 or match2:
            results.append([area, cords])
            return results

    def _split_text(self, text: str):
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            new_lines.append(line.split(" "))
        return new_lines

    def _new_search_match(self, text: str, area: int, cords: list):
        splited_text = self._split_text(text)
        string_to_match = 'e-mail:'
        results = []
        for line_splited_text in splited_text:
            for item in line_splited_text:
                result = fuzz.ratio(string_to_match, item)
                if result >= 70:
                    results.append([area, cords])
        return results

    def _find_block_cords(self, path_to_file: str):
        results = []
        for i in range(2, 7):
            image, line_items_coordinates, areas = self._mark_region(f"{path_to_file}", i)
            for j, k in zip(range(len(line_items_coordinates)), range(len(areas))):
                if 45000 < areas[k] <= 250000:  # area a block
                    img = image[line_items_coordinates[j][0][1]:line_items_coordinates[j][1][1],
                          line_items_coordinates[j][0][0]:line_items_coordinates[j][1][0]]
                    ret, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
                    text = str(pytesseract.image_to_string(thresh1, lang='eng', config='--psm 6', ))
                    if self._find_match_in_text(text, areas[k], line_items_coordinates[j]):
                        results.append(self._find_match_in_text(text, areas[k], line_items_coordinates[j]))
                        j += 1
                        k += 1
                    elif self._new_search_match(text, areas[k], line_items_coordinates[j]):
                        results.append(self._new_search_match(text, areas[k], line_items_coordinates[j]))
        return results

    @staticmethod
    def base64_to_pdf(base64_data: bytes, name_pdf: str, folder_name: str):
        bPDFout = codecs.decode(base64_data, 'base64')

        with open(f"{folder_name}/{name_pdf}.pdf", 'wb') as f:
            f.write(bPDFout)
