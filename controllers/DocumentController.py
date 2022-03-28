from flask import Blueprint
from services.DocumentService import DocumentService

documents = Blueprint('documents', __name__)

service = DocumentService()


@documents.route('/test-protocols/find-coordinates', methods=['POST'])
def search():
    pass
