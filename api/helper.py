import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

def download_model_from_drive(file_id, destination):
    def get_session():
        session = requests.Session()
        retry = Retry(total=1, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        return session

    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32768
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    session = get_session()

    url = f"https://drive.google.com/uc?id={file_id}&export=download"
    response = session.get(url, stream=True)

    token = get_confirm_token(response)
    if token:
        url = f"{url}&confirm={token}"
        response = session.get(url, stream=True)

    if 'text/html' in response.headers.get('Content-Type', ''):
        confirm_match = re.search(r"confirm=([0-9A-Za-z_]+)", response.text)
        if confirm_match:
            confirm_token = confirm_match.group(1)
            url = f"https://drive.google.com/uc?id={file_id}&export=download&confirm={confirm_token}"
            response = session.get(url, stream=True)

    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition:
        save_response_content(response, destination)
        print(f"Model downloaded and saved to {destination}")
        return True
    else:
        print("Failed to download the file. Google Drive might be blocking automated downloads.")
        print("Please try to download the file manually and place it in the correct directory.")
        return False

def ensure_model_exists(model_path, file_id):
    if not os.path.exists(model_path):
        print(f"{model_path} not found. Downloading from Google Drive...")
        success = download_model_from_drive(file_id, model_path)
        if not success:
            print("Failed to download the file. Please check the file ID and your permissions.")
    else:
        print(f"{model_path} already exists. Skipping download.")