from services.DocumentService import DocumentService
import base64

service = DocumentService()

name_doc = "Вопросы по Hive"
#service._create_binary_pdf(name_doc)
hello = service.pdf_to_base64(f"images/{name_doc}.pdf")
print(hello)
service.base64_to_pdf(bytes(hello), "new_pdf")
service._word_to_pdf('protocols')


