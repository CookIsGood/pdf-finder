from flask import Blueprint, request, jsonify
from services.DocumentService import DocumentService
import binascii

documents = Blueprint('documents', __name__)

service = DocumentService()


@documents.route('/protocols/find-coordinates', methods=['POST'])
def search():
    content = request.get_json()
    try:
        msg = service.publish_msg(content)
    except ValueError as err:
        msg = {
            'data':
                {
                    'msg': err.args[0]
                }
        }
        return jsonify(msg), 422
    return jsonify(msg)
