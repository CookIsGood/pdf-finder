from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError
import codecs
import binascii
import numpy as np
import cv2, io
import logging
from PIL import Image
from PIL import ImageColor


class DocumentConverter:
    def __init__(self, base64_data, start_page, stop_page):
        self._logger_doc_converter = logging.getLogger(__name__)
        self._logger_doc_converter.setLevel(logging.DEBUG)

        self._base64_data = base64_data.encode('utf-8')
        self._start_page = start_page
        self._stop_page = stop_page

    def get_images(self):
        binary_pdf = self._base64_to_pdf(self._base64_data)
        new_pages, pages, num_pages, count_pages = self._bpdf_to_pages(binary_pdf,
                                                                       self._start_page,
                                                                       self._stop_page)
        images = self._pages_to_images(new_pages)
        return images

    def get_pages_info(self):
        binary_pdf = self._base64_to_pdf(self._base64_data)
        new_pages, pages, num_pages, count_pages = self._bpdf_to_pages(binary_pdf,
                                                                       self._start_page,
                                                                       self._stop_page)
        return new_pages, pages, num_pages, count_pages

    def _base64_to_pdf(self, base64_data: bytes):
        try:
            binary_pdf = codecs.decode(base64_data, 'base64')
        except binascii.Error:
            logging.warning("key 'b64_data' does not contain base64 date.")
            raise ValueError("key 'b64_data' does not contain base64 date.")
        self._logger_doc_converter.debug('Base64_pdf to binary_pdf conversion completed')
        return binary_pdf

    def _bpdf_to_pages(self, binary_pdf: bytes, start_page, stop_page) -> tuple:

        try:
            pages = convert_from_bytes(binary_pdf)
        except PDFPageCountError:
            logging.warning("Splitting binary pdf into images cannot be complete")
            raise ValueError("Page count error!")
        count_pages = len(pages)
        num_pages = [i for i in range(len(pages))]
        try:
            new_pages = pages.copy()
            new_pages = new_pages[start_page:stop_page:None]
            num_pages = num_pages[start_page:stop_page:None]
        except TypeError:
            self._logger_doc_converter.warning("Incorrect values ​​passed")
            raise ValueError("Incorrect values ​​passed")

        self._logger_doc_converter.debug('Splitting binary pdf into images is complete')
        return new_pages, pages, num_pages, count_pages

    @staticmethod
    def _pages_to_images(pages: list) -> list:
        result = []
        for item in pages:
            buffer = io.BytesIO()
            item.save(buffer, format='JPEG')
            result.append(cv2.imdecode(np.frombuffer(buffer.getvalue(), dtype='uint8'),
                                       cv2.COLOR_BGR2RGB))
        return result


class DocumentCropInsertion:

    def get_crop(self, width, height, color):
        try:
            if width <= 0 or height <= 0:
                raise ValueError("Width and height cannot be negative or zero!")
            color = self._hex_to_rgb(color)
            crop_img = Image.new(mode="RGBA", size=(width, height), color=color)
        except TypeError:
            raise ValueError("Invalid crop image parameters passed")
        return crop_img


    @staticmethod
    def get_crop_position(x, y, width, height):
        x_new = x - width
        y_new = y - height
        result_x = (x_new + x) / 2
        result_y = (y_new + y) / 2
        return int(result_x), int(result_y)

    @staticmethod
    def _hex_to_rgb(hex_str: str):
        try:
            rgb_color = ImageColor.getcolor(hex_str, "RGB")
        except TypeError:
            raise ValueError("Incorrect color value passed")
        return rgb_color
