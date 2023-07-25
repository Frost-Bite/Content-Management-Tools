from requests_html import HTMLSession
from time import sleep

def get_proxies():
    endpoint = 'https://api.best-proxies.ru/proxylist.txt'
    key = 'developer'
    api_url = f'{endpoint}?key={key}&limit=50&type=socks5&level=1'
    session = HTMLSession()
    
    try:
        response = session.get(api_url)
        response.raise_for_status()
    except Exception as e:        
        print(f"Error: {e}")
        session.close()
        sleep(10)
        return []
    
    proxies = response.text.split()
    
    if not proxies:
        session.close()
        return []
    
    session.close()
    return proxies
