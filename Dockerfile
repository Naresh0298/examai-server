FROM python:3.13-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /code/app

EXPOSE 8000

CMD [ "uvicorn","app.server:app","--host","0.0.0.0","--port","8000"]
