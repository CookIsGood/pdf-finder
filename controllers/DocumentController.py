from flask import Blueprint, request, jsonify
from services.DocumentService import DocumentService
import binascii

documents = Blueprint('documents', __name__)

service = DocumentService()


@documents.route('/protocols/find-coordinates', methods=['POST'])
def search():
    content = request.get_json()
    try:
        input_data = content['data']
    except KeyError:
        msg = {
            'data':
                {
                    'msg': "key 'data' not found"
                }
        }
        return jsonify(msg), 400
    except TypeError:
        msg = {
            'data':
                {
                    'msg': "The object being sent is not JSON"
                }
        }
        return jsonify(msg), 400
    try:
        msg = service.find_block_coordinates(input_data)
    except binascii.Error:
        msg = {
            'data':
                {
                    'msg': "key 'data' does not contain base64 date."
                }
        }
        return jsonify(msg), 422
    except ValueError:
        msg = {
            'data':
                {
                    'msg': "Failed to calculate coordinates"
                }
        }
        return jsonify(msg), 422
    return jsonify(msg)
