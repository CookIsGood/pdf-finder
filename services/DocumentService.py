import pdf_recognizer.DocumentRecognizer as rec

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
        recognizer = rec.DocumentRecognizer(**content)
        return recognizer.find_stamp_coordinates(b64_data)
