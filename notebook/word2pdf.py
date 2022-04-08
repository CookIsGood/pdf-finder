from docx2pdf import convert
import os, fnmatch


def docx2pdf(path_to_docx: str, path_to_pdf: str):
    files = fnmatch.filter(os.listdir(f'{path_to_docx}'), '*.docx')
    for file in files:
        print(file)
        convert(f"{path_to_docx}\{file}",
                f"{path_to_pdf}\{file.strip('.docx')}.pdf")
