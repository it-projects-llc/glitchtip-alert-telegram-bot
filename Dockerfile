FROM python:3.9-slim

WORKDIR /app

COPY /build/requirements.txt .
RUN pip install -r requirements.txt

COPY /build .

EXPOSE 8844

CMD ["gunicorn", "--bind", "0.0.0.0:8844", "bot:app"]