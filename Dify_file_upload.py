import os
import requests
import json
import time

# Configuratie
API_KEY = "dataset-7FKlce0q2QrAIrf0GmcQ24Gh"
DATASET_ID = "cdf400c7-e896-4c8c-bf67-d83fde99d15e"
PDF_FOLDER = r"C:\Users\titia\Downloads\chapters-20250401T220920Z-001\chapters"

# API setup
url = f"https://api.dify.ai/v1/datasets/{DATASET_ID}/document/create_by_file"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Upload alle PDF bestanden
for filename in os.listdir(PDF_FOLDER):
    if filename.endswith(".pdf"):
        file_path = os.path.join(PDF_FOLDER, filename)

        with open(file_path, 'rb') as file:
            config = json.dumps({
                "indexing_technique": "high_quality",
                "process_rule": {"mode": "automatic"}
            })

            files = {
                'file': (filename, file, 'application/pdf'),
                'data': (None, config, 'text/plain')
            }

            response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                print(f"✅ {filename}")
            else:
                print(f"❌ {filename} - Error {response.status_code}")

        time.sleep(1)  # Pauze tussen uploads