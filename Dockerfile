FROM python:3.10-slim
WORKDIR /build
COPY ./requirements.txt .
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y curl && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt
WORKDIR /app
CMD uvicorn main:app --host=0.0.0.0 --port=8080 --reload