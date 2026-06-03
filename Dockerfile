FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Crear un usuario no root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["python", "-m", "app.main"]
