FROM python:3.13-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Use gunicorn with gthread worker for production instead of eventlet
CMD ["gunicorn", "-w", "1", "-k", "gthread", "-b", "0.0.0.0:80", "app:app"]