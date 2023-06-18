from time import sleep
from datetime import datetime
from requests_html import HTMLSession
from pprint import pprint
from proxiesnew import get_proxies 
import random 
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, wait
from queue import Queue

import logging


def extract_and_write_game_data(response, domain, locker):
    
    gamename = ''.join(response.html.xpath('//a/h1[1]/text()'))
    platform = response.html.xpath("//li[@class='summary_detail product_platforms']/span[@class='data' and 1]/a/text()") # Comma separated, PC, Switch, PS4, Xbox One)
    genre = response.html.xpath("//li[@class='summary_detail product_genre']/span[@class='data' and 2]/text()")
    userscore = response.html.xpath("//div[@class='userscore_wrap feature_userscore']/div[@class='summary' and 2]/p[1]/span[@class='count' and 2]/a[1]/text()") # number of user ratings
    mp = ''.join(response.html.xpath("//li[@class='summary_detail product_players']/span[@class='data' and 2]/text()"))
    publisher = response.html.xpath("//li[@class='summary_detail publisher']/span[@class='data' and 2]/a/text()") 	
    developer = ','.join(response.html.xpath("//li[@class='summary_detail developer']/span[@class='data' and 2]/a/text()")) 
    metascoreuser = response.html.xpath("//a/div[contains(@class, 'metascore_w user')]/text()") # User rating
    metascore = ''.join(response.html.xpath("//div[contains(@class, 'metascore_w')]/span[1]/text()")) 
    agerating = ''.join(response.html.xpath("//li[@class='summary_detail product_rating']/span[@class='data' and 2]/text()"))
    releasedate = ''.join(response.html.xpath("//li[@class='summary_detail release_data']/span[@class='data' and 2]/text()")) # Releasedate (20190219,yyyymmdd)   
    
    #Reformatting data

    platform_replacements = {
        'iPhone/iPad': '',
        'Stadia': '',
        'PlayStation ': 'PS',
        'playstation-': 'PS'
    }

    platform = [platform_replacements.get(tp, tp) for tp in platform if tp not in platform_replacements]

    targetplatform = domain.split('/')
    platform.append(targetplatform[0])

    platform = ','.join(platform)
    
    if mp != 'No Online Multiplayer' and mp != '':
        genre.append('multiplayer') 
    genre = ','.join(genre)
    genre = genre.replace('Role-Playing', 'RPG')
    
    i = 0
    for p in publisher:
        publisher[i] = p.replace('\n', '').replace('  ', '')
        i=i+1
        
    publisher = ','.join(publisher)
    
    userscore = ''.join(userscore).replace(' Ratings', '')
    
    developer = developer.replace('\n', '').replace('  ', '') 
    
    metascoreuser = ''.join(metascoreuser).replace('.', '')
    
    releasedate = date_to_excel(releasedate)


    # Write data to file line by line, you can use your method or pandas
    with locker:
        with open(filename, 'a', encoding='utf-16') as file:
            file.write(f'{gamename}\t{platform}\t{genre}\t{publisher}\t{developer}\t{metascoreuser}\t{metascore}\t{domain}\t{releasedate}\t{agerating}\t{mp}\t{userscore}\n')
                

def date_to_excel(date_string):
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    month, day, year = date_string.split()
    month = month_map[month]
    day = day.rstrip(',')
    if len(day) == 1:
        day = f"0{day}"
    
    return f"{year}{month}{day}"

# Wait new proxies   
def is_empty(q):
    if q.empty():
        sleep(10)
        if q.empty():
            return True
    return False

# log data for threads
logger = logging.getLogger(__name__)  

def worker(thread_num, domains_queue, proxy_queue, scaned_domains, locker):
    with HTMLSession() as session:
        print('Start thread session', thread_num)      

        while True:
            if is_empty(domains_queue):                
                print('Interrupt the thread, the queue is empty')
                break

            try:                
                print('Requests in the queue', len(list(domains_queue.queue)))
                domain = domains_queue.get()
                print(domain)
                scaned_domains.add(domain)                
                url = f'https://www.metacritic.com/game/{domain}'                               
                quit = False
                while True:
                    try:
                        if is_empty(proxy_queue):
                            print(f'last proxy used on {domain}, request a new proxy list')
                            for prx in get_proxies():
                                proxy_queue.put(prx) 
                            
                        print('Proxy left', len(list(proxy_queue.queue)))
                        random_proxy_raw = proxy_queue.get()
                        random_proxy = 'socks5://'+random_proxy_raw
                        print(random_proxy)
                        random_proxy = {'http': random_proxy, 'https': random_proxy}
                        print(random_proxy)
                        
                        user_agent = random.choice(user_agent_list)
                        headers = {'User-Agent': user_agent}                        
                        
                        response = session.get(url, proxies=random_proxy, timeout=8, headers=headers)        
                        pprint(response)  # Server response
                        pprint(response.html)  # URL

                        html = response.text.strip()
                        assert response.status_code == 200
                        extract_and_write_game_data(response, domain, locker)
                        break
                        
                    except Exception as e:
                        print(type(e), e)
                print(f'Ready = {domain}')
                sleep(1)
            except Exception as e:
                print(e, type(e))
  
def main():
    locker = Lock()
    domains_queue = Queue()
    with open('metagames.txt', 'r') as domains_file:
        for line in domains_file:
            domain = line.rstrip('\n')
            domains_queue.put(domain)

    scaned_domains = set()

    now = datetime.now()
    date_for_filename = now.strftime("%Y%m%d-%H%M")
    global filename
    filename = 'results-meta'+date_for_filename+'.csv'
    
    with open(filename, 'a', encoding='utf-16') as file:
        file.write(f'Gamename\tplatform\tgenre\tpublisher\tdeveloper\treviewscore\tmetascore\tdomain\treleasedate\tagerating\tmp\tuserreviews\n')

    proxy_queue = Queue()

    while proxy_queue.empty():
        for prx in get_proxies():
            proxy_queue.put(prx)
            if proxy_queue.empty():
                print('proxy server addresses not received, next try in 10 seconds')
                sleep(10)                 

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(domains_queue.qsize()):
            futures.append(executor.submit(worker, i, domains_queue, proxy_queue, scaned_domains, locker))
            logger.info(f'Thread {i} started work')

        # Wait for all tasks to complete
        completed, not_completed = wait(futures)
        
        # Check for any exceptions in the completed tasks
        for future in completed:
            try:
                future.result()
            except Exception as e:
                logger.exception(e)
                

            
user_agent_list = [ # User-Agent list, need to be cleaned, you can use your
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0',
'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:77.0) Gecko/20100101 Firefox/77.0',
'Mozilla/5.0 (X11; Linux ppc64le; rv:75.0) Gecko/20100101 Firefox/75.0',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/75.0',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:75.0) Gecko/20100101 Firefox/75.0',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2866.71 Safari/537.36',
'Mozilla/5.0 (X11; Ubuntu; Linux i686 on x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2820.59 Safari/537.36',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2762.73 Safari/537.36',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2656.18 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44',
    ]

if __name__ == '__main__':
    main()
