import cv2, pytesseract, os, re
from PIL import Image
from pdf2image import convert_from_path
import codecs, fnmatch


class DocumentService:

    def find_coordinates(self, folder_name: str, binary_data: str):
        os.makedirs(f"{folder_name}", exist_ok=True)
        files = fnmatch.filter(os.listdir(f'{folder_name}'), '*.pdf')
        for file in files:
            self._make_images(binary_data, file)


    def _make_images(self, folder_name: str, filename: str):
        pdfs = f"/{folder_name}/{filename}"
        pages = convert_from_path(pdfs)
        image_name = "last_page_" + str(len(pages)) + ".jpg"
        pages[len(pages) - 1].save(f"{folder_name}/{image_name}", "JPEG")

    def _mark_region(self, image_path: str, iterations: int):
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
        for c in cnts:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)

            if w < THRESHOLD_REGION_IGNORE or h < THRESHOLD_REGION_IGNORE:
                continue

            image = cv2.rectangle(image, (x, y), (x + w, y + h), color=(255, 0, 255), thickness=3)
            line_items_coordinates.append([(x, y), (x + w, y + h)])

        return image, line_items_coordinates

    def _find_center(self, points: list):
        result_x = (points[1][0] + points[0][0]) / 2
        result_y = (points[1][1] + points[0][1]) / 2
        return int(result_x), int(result_y)

    def _find_match_in_text(self, text: str):
        match = re.search("e-mail:", text)
        match1 = re.search("email:", text)
        if match or match1:
            return True

    def _find_text_in_block(self, line_items_coordinates: list, image):
        for i in range(10):
            for item in line_items_coordinates:
                img = image[item[0][1]:item[1][1], item[0][0]:item[1][0]]
                ret, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
                text = str(pytesseract.image_to_string(thresh1, config='--psm 6', ))
                print(text)
                if self._find_match_in_text(text):
                    print("Find it")
                    return item
        return None


    @staticmethod
    def pdf_to_binary(path: str):
        with open(path, 'rb') as f:
            pdfdatab = f.read()
        b64PDF = codecs.encode(pdfdatab, 'base64')
        return b64PDF

    @staticmethod
    def binary_to_pdf(binary_data: bytes, name_pdf: str):
        bPDFout = codecs.decode(binary_data, 'base64')
        with open(f"images/{name_pdf}.pdf", 'wb') as f:
            f.write(bPDFout)
