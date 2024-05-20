import random
import json

def get_proxies_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            proxies = json.load(file)
            return proxies
    except Exception as e:
        print("An error occurred while reading the file:", e)
        return []

def get_random_proxy(file_path):
    proxies = get_proxies_from_file(file_path)
    if not proxies:
        print("No proxies found in the file.")
        return None
    random_proxy = random.choice(proxies)
    ip = random_proxy["ip"]
    port = random_proxy["port"]
    protocol = random_proxy["protocols"][0]
    return {protocol: f"{protocol}://{ip}:{port}"}
