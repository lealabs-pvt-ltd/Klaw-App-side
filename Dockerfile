# app/Dockerfile
FROM python:3.9.20-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# Combine commands into a single CMD
CMD ["python3 manage.py makemigrations && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8001"]
