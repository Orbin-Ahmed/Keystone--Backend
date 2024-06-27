import requests
from bs4 import BeautifulSoup

def scrape_houzz_images(keyword: str, page: int):
    base_url = "https://www.houzz.com/photos/query/"
    search_url = f"{base_url}{keyword}/nQRvCq/p/{page}/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img', class_='hz-photo-card__img')

    image_urls = [img['src'] for img in images if 'src' in img.attrs]

    return image_urls
