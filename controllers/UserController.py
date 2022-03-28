from flask import Blueprint

users = Blueprint('users', __name__)


@users.route('/<username>', methods=['GET'])
def get_by_username(username):
    pass


@users.route('/register', methods=['POST'])
def register(username, password):
    pass


@users.route('/<username>', methods=['PUT'])
def update_info(username):
    pass


@users.route('/<username>', methods=['DELETE'])
def delete_user(username):
    pass
