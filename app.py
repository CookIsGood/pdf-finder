from flask import Flask
import os
from controllers.DocumentController import documents

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG_TB_ENABLED = False


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(documents)