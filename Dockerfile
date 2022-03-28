FROM python:3.9

RUN apt-get update \
            && apt-get upgrade -y \
            && apt-get autoremove \
            && apt-get autoclean \
            && mkdir app \
            && apt-get install poppler-utils \
            && apt install tesseract-ocr

COPY requirements.txt /app/
WORKDIR /app
RUN pip install --upgrade pip \
            && pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV SECRET_KEY="123"
ENV FLASK_APP=app.py

CMD ["python", "test.py"]