FROM python:3.11-slim

WORKDIR /app

# Install git or other basics if needed, but for now just python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["python", "src/server.py"]