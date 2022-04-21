FROM python:3.9

RUN apt-get update \
            && apt-get upgrade -y \
            && apt-get autoremove \
            && apt-get autoclean \
            && mkdir app \
            && apt-get install poppler-utils -y \
            && apt install tesseract-ocr -y \
            && apt-get install -y python3-opencv

RUN apt-get install tesseract-ocr-eng -y
RUN apt-get install tesseract-ocr-rus -y

COPY requirements.txt /app/
WORKDIR /app
RUN pip install --upgrade pip \
            && pip install --no-cache-dir -r requirements.txt \
            && pip install python-Levenshtein

COPY . /app/

ENV SECRET_KEY="123"
ENV FLASK_APP=app.py

CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:80", "main:app"]
