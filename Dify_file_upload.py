import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuratie
API_KEY = os.getenv("DIFY_API_KEY")
DATASET_ID = os.getenv("DIFY_DATASET_ID")
PDF_FOLDER = os.getenv("PDF_FOLDER")

# Error handling for missing environment variables
if API_KEY is None or DATASET_ID is None or PDF_FOLDER is None:
    print("❌ Error: DIFY_API_KEY, DIFY_DATASET_ID, or PDF_FOLDER not found in .env file.")
    print("Please create a .env file with these variables.")
    exit()

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
