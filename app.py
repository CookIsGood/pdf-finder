from flask import Flask
import os
from controllers.DocumentController import documents
from core_limiter import limiter

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG_TB_ENABLED = False


app = Flask(__name__)
app.config.from_object(Config)
limiter.init_app(app)
app.register_blueprint(documents)

if __name__ == "__main__":
    app.run(port=45000, host="0.0.0.0")