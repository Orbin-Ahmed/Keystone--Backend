import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_detail_image(detail_url, headers):
    detail_response = requests.get(detail_url, headers=headers)
    if detail_response.status_code != 200:
        print(f"Failed to retrieve detail page. Status code: {detail_response.status_code}")
        return None

    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
    image = detail_soup.find('img', class_='view-photo-image-pane__image')
    if image and 'src' in image.attrs:
        return image['src']
    return None

def scrape_houzz_images(keyword: str, page: int, max_workers=10):
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
    image_objects = soup.find_all('a', class_='hz-photo-card__ratio-box')

    image_urls = []

    detail_urls = [img_obj['href'] for img_obj in image_objects]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_detail_image, url, headers): url for url in detail_urls}

        for future in as_completed(future_to_url):
            image_url = future.result()
            if image_url:
                image_urls.append(image_url)

    return image_urls