import time
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from bs4 import BeautifulSoup
from config import Config
from .utils import get_driver

def scrape_site(site, market, max_pages=1):
    query_market = market.lower().replace(' ', '-')
    base_url = {
        'redfin.com': f'https://www.redfin.com/city/123/OH/Akron/filter/sort=lo-price,page=1',
        'homes.com': f'https://www.homes.com/{query_market}/homes-for-sale/',
        'movoto.com': f'https://www.movoto.com/{query_market}/for-sale/'
    }.get(site, '')
    
    if not base_url: return []
    
    driver = get_driver()
    listings = []
    
    try:
        driver.get(base_url)
        time.sleep(random.uniform(2, 5))
        
        for page in range(1, max_pages + 1):
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            if 'redfin' in site:
                items = soup.find_all('div', class_='HomeCard')
                for item in items:
                    addr_tag = item.find('span', class_='address')
                    price_tag = item.find('span', class_='homecardV2Price')
                    stats_tag = item.find('div', class_='stats')
                    addr = addr_tag.text.strip() if addr_tag else ''
                    price = price_tag.text.strip() if price_tag else ''
                    beds = baths = sqft = ''
                    if stats_tag:
                        stats = stats_tag.text.strip().split('•')
                        if len(stats) > 0: beds = stats[0].strip()
                        if len(stats) > 1: baths = stats[1].strip()
                        if len(stats) > 2: sqft = stats[2].strip()
                    if addr and price:
                        listings.append({'addr': addr, 'price': price, 'beds': beds, 'baths': baths, 'sqft': sqft})
            
            elif 'homes' in site:
                items = soup.find_all('div', class_='for-sale-content-container')  # Updated; close to rent variant
                for item in items:
                    addr_tag = item.find('p', class_='address')
                    info_container = item.find('ul', class_='detailed-info-container')
                    extra_info = info_container.find_all('li') if info_container else []
                    addr = addr_tag.text.strip() if addr_tag else ''
                    price = extra_info[0].text.strip() if len(extra_info) > 0 else ''
                    beds = extra_info[1].text.strip() if len(extra_info) > 1 else ''
                    baths = extra_info[2].text.strip() if len(extra_info) > 2 else ''
                    sqft = extra_info[3].text.strip() if len(extra_info) > 3 else ''
                    if addr and price:
                        listings.append({'addr': addr, 'price': price, 'beds': beds, 'baths': baths, 'sqft': sqft})
            
            elif 'movoto' in site:
                items = soup.find_all('div', class_='tileContent')
                for item in items:
                    addr_tag = item.find('p', class_='cardAddr')
                    price_tag = item.find('p', class_='cardPrice')
                    stats_tag = item.find('p', class_='cardItem')
                    addr = addr_tag.text.strip() if addr_tag else ''
                    price = price_tag.text.strip() if price_tag else ''
                    beds = baths = sqft = ''
                    if stats_tag:
                        stats = stats_tag.text.strip().split('|')
                        if len(stats) > 0: beds = stats[0].strip()
                        if len(stats) > 1: baths = stats[1].strip()
                        if len(stats) > 2: sqft = stats[2].strip()
                    if addr and price:
                        listings.append({'addr': addr, 'price': price, 'beds': beds, 'baths': baths, 'sqft': sqft})
            
            # Pagination stub (expand for multi-page later)
            time.sleep(random.uniform(3, 7))
        
    except Exception as e:
        print(f"Error scraping {site}: {e}")
    finally:
        driver.quit()
    
    return listings

if __name__ == '__main__':
    for site in Config.SCRAPE_SITES:
        results = scrape_site(site, Config.MARKETS[0])
        print(f"{site} results: {len(results)} listings")
        print(results[:2])
