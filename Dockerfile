FROM python:3.9

RUN apt-get update \
            && apt-get upgrade -y \
            && apt-get autoremove \
            && apt-get autoclean \
            && mkdir app
RUN apt-get install poppler-utils -y
RUN apt install tesseract-ocr -y
RUN apt-get install -y python3-opencv

COPY requirements.txt /app/
WORKDIR /app
RUN pip install --upgrade pip \
            && pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV SECRET_KEY="123"
ENV FLASK_APP=app.py

CMD ["python", "app.py"]