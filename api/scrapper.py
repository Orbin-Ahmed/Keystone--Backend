from py3pin.Pinterest import Pinterest
from .proxy import get_random_proxy

def search_pinterest(query, page_size):
    file_path = "E:/Django/Keystone--Backend/Free_Proxy_List.json"
    p = get_random_proxy(file_path)
    pinterest = Pinterest(
        email='acantoahmed@hotmail.com',
        password='Pranto@123',
        username='acantoahmed3898',
        proxies=p,
    )
    search_batch = pinterest.search(scope='pins', query=query, page_size=page_size)
    results = []
    print(p)

    for result in search_batch:
        minimized_result = {
            'id': result.get('id'),
            'images': {
                '474x': result.get('images', {}).get('474x', {}).get('url'),
                'orig': result.get('images', {}).get('orig', {}).get('url')
            }
        }
        results.append(minimized_result)
    
    return results
