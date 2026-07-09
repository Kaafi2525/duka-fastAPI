FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

ENV MODULE_NAME=main
ENV VARIABLE_NAME=app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY . /app
