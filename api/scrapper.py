from py3pin.Pinterest import Pinterest
from .proxy import get_random_proxy

def search_pinterest(query, page_size=30, page_number=1):
    file_path = "E:/Django/Keystone--Backend/Free_Proxy_List.json"
    p = get_random_proxy(file_path)
    pinterest = Pinterest(
        email='acantoahmed@hotmail.com',
        password='Pranto@123',
        username='acantoahmed3898',
        proxies=p,
    )

    all_results = []
    current_page = 1

    while True:
        search_batch = pinterest.search(scope='pins', query=query, page_size=page_size)

        if not search_batch:
            break

        if current_page == page_number:
            for result in search_batch:
                minimized_result = {
                    'id': result.get('id'),
                    'images': {
                        'thumb': result.get('images', {}).get('474x', {}).get('url'),
                        'full': result.get('images', {}).get('orig', {}).get('url')
                    }
                }
                all_results.append(minimized_result)

        current_page += 1
        
        if current_page > page_number:
            break

    return all_results
