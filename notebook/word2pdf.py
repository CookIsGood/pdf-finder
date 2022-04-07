from docx2pdf import convert
import os, fnmatch

files = fnmatch.filter(os.listdir(f'C:\hi'), '*.docx')

for file in files:
    print(file)
    convert(f"C:\hi\{file}",
            f"C:\docs_pdf\{file.strip('.docx')}.pdf")
