FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential gcc

COPY pyproject.toml requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=innit_project.settings

CMD ["gunicorn", "innit_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
