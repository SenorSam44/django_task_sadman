FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock* /app/

RUN pdm install --no-editable --no-self

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["pdm", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
