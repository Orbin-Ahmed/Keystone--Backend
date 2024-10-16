import os
import requests

CHECKPOINTS = {
    'best_1600_box_100.pt': 'https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_1600_box_100.pt',
    'best_wall_7k_100.pt': 'https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_wall_7k_100.pt',
}

CHECKPOINT_DIR = os.path.join('api', 'checkpoints')
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

for filename, url in CHECKPOINTS.items():
    file_path = os.path.join(CHECKPOINT_DIR, filename)
    if not os.path.exists(file_path):
        print(f'Downloading {filename} from {url}')
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        print(f'{filename} already exists. Skipping download.')
