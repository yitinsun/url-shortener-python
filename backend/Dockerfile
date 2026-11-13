FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install --no-cache-dir .

ENV APP_ENV=prod
EXPOSE 8080

CMD ["uvicorn", "urlshortener.main:app", "--host", "0.0.0.0", "--port", "8080"]
