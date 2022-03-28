from flask import Flask
from conn_db import db
import os
from controllers.UserController import users
from controllers.DocumentController import documents


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/my_db.db'
    DEBUG_TB_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()

app.register_blueprint(users)
app.register_blueprint(documents)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')