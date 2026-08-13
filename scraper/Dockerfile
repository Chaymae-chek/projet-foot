# scraper/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copier d'abord uniquement requirements.txt : Docker met cette étape en
# cache tant que ce fichier ne change pas, donc les reconstructions
# suivantes (après une modification de api_client.py) sont bien plus rapides.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "api_client.py"]