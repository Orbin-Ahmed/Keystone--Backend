from py3pin.Pinterest import Pinterest
from .proxy import get_random_proxy
import os

def search_pinterest(query, page_size=30, page_number=1, desired_count=20):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(BASE_DIR, "Free_Proxy_List.json")
    p = get_random_proxy(file_path)
    pinterest = Pinterest(
        email='acantoahmed@hotmail.com',
        password='Pranto@123',
        username='acantoahmed3898',
        cred_root='cred_root',
        proxies=p,
    )
    # pinterest.login()
    all_results = []
    current_page = 1

    while len(all_results) < desired_count:
        search_batch = pinterest.search(scope='pins', query=query, page_size=page_size)

        if not search_batch:
            break

        if current_page >= page_number:
            for result in search_batch:
                minimized_result = {
                    'id': result.get('id'),
                    'images': {
                        'thumb': result.get('images', {}).get('474x', {}).get('url'),
                        'full': result.get('images', {}).get('orig', {}).get('url')
                    }
                }
                all_results.append(minimized_result)
                if len(all_results) >= desired_count:
                    break

        current_page += 1
        
    return all_results[:desired_count]