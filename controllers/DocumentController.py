from flask import Blueprint, request, jsonify
from services.DocumentService import DocumentService

documents = Blueprint('documents', __name__)

service = DocumentService()


@documents.route('/test-protocols/find-coordinates', methods=['POST'])
def search():
    content = request.get_json()
    result = service.find_block_coordinates(content['data'])
    return jsonify(
        {'data':
            {
                'x': result[0],
                'y': result[1]
            }
        })
