from services.DocumentService import DocumentService

service = DocumentService()

name_doc = "Вопросы по Hive"
#service._create_binary_pdf(name_doc)
hello = service.pdf_to_binary(f"images/{name_doc}.pdf")
service.binary_to_pdf(bytes(hello), "new_pdf")
service.find_coordinates("images", hello)

