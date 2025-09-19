import streamlit as st
from playwright.async_api import async_playwright
import asyncio
import re
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import logging
import numpy as np
import random
import time
import os
import requests
import json
import numpy_financial as npf  # For IRR calculation

# Load environment variables from .env file
from pathlib import Path
env_path = Path('.') / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
fh = logging.FileHandler('app_log.txt')
logger.addHandler(fh)

# Bright Data Configuration
proxy_server = os.getenv("BRIGHT_DATA_HOST", "brd.superproxy.io:33335")
BRIGHT_DATA_API_TOKEN = os.getenv("BRIGHT_DATA_API_TOKEN", "")

# Bright Data Scraper API Endpoints - USA Properties Only
BRIGHT_DATA_ZILLOW_DATASET = "gd_lfqkr8wm13ixtbd8f5"  # Zillow USA dataset ID
BRIGHT_DATA_REALTOR_DATASET = "gd_m517agnc1jppzwgtmw"  # Realtor dataset ID (has USA properties)
BRIGHT_DATA_ZILLOW_PRICE_HISTORY = "gd_lxu1cz9r88uiqsosl"  # Zillow price history dataset
BRIGHT_DATA_API_BASE = "https://api.brightdata.com/datasets/v3"
proxy_username = os.getenv("BRIGHT_DATA_USERNAME", "brd-customer-hl_dd2a0351-zone-residential_proxy_us1")
proxy_password = os.getenv("BRIGHT_DATA_PASSWORD", "")

# Bright Data proxy customization options
def get_proxy_username(country=None, state=None, asn=None, ip=None):
    """Generate customized Bright Data proxy username based on requirements"""
    base_username = proxy_username
    
    if country:
        base_username += f"-country-{country}"
    if state:
        base_username += f"-state-{state}"
    if asn:
        base_username += f"-asn-{asn}"
    if ip:
        base_username += f"-ip-{ip}"
    
    return base_username

# Random User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
]

class NormalizerAgent:
    def normalize(self, address):
        # Enhanced regex pattern for better address parsing
        # Handles formats like "1841 Marks Ave, Akron, OH 44305"
        pattern = r'(\d+\s+[\w\s.]+?),\s*([\w\s]+?),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?'
        match = re.match(pattern, address.strip(), re.I)
        if match:
            street, city, state, zipcode = match.groups()
            return {
                'street': street.strip(),
                'city': city.strip(),
                'state': state.upper(),
                'zip': zipcode.strip() if zipcode else None
            }
        
        # Fallback pattern for addresses without ZIP
        pattern2 = r'(\d+\s+[\w\s.]+?),\s*([\w\s]+?),\s*([A-Z]{2})'
        match2 = re.match(pattern2, address.strip(), re.I)
        if match2:
            street, city, state = match2.groups()
            return {
                'street': street.strip(),
                'city': city.strip(),
                'state': state.upper(),
                'zip': None
            }
        return None

class SiteFetcherAgent:
    def __init__(self, proxy, cert_path=None, ignore_https_errors=False):
        self.proxy = proxy
        self.cert_path = cert_path
        self.ignore_https_errors = ignore_https_errors

    async def _retry_operation(self, func, *args, **kwargs):
        """Retry operation with exponential backoff"""
        retries = 3
        backoff = 2.0
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(backoff ** attempt)
        return None

    async def fetch_zillow(self, page, address_dict):
        street = address_dict['street'].replace(' ', '-')
        city = address_dict['city'].replace(' ', '-')
        state = address_dict['state']
        zipcode = address_dict['zip']
        # Use HTTPS and proven URL format for Zillow
        url = f"https://www.zillow.com/homes/{street}-{city}-{state}-{zipcode}_rb/"
        try:
            await self._retry_operation(page.goto, url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(5, 10))  # Even longer delays for human-like behavior
            
            # Simulate human scrolling
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/4);')
            await asyncio.sleep(random.uniform(1, 2))
            # Use current 2025 Zillow selectors with fallbacks
            value = await page.evaluate('() => document.querySelector(\'[data-testid="primary-zestimate"], [data-testid="price"], .notranslate\')?.innerText || null')
            rent = await page.evaluate('() => document.querySelector(\'[data-testid="rent-zestimate-value"], [data-testid="rent-estimate"]\')?.innerText || null')
            beds = await page.evaluate('() => document.querySelector(\'[data-testid="bedroom-amount"], [data-testid="bed-value"]\')?.innerText || null')
            baths = await page.evaluate('() => document.querySelector(\'[data-testid="bathroom-amount"], [data-testid="bath-value"]\')?.innerText || null')
            sqft = await page.evaluate('() => document.querySelector(\'[data-testid="floor-space-amount"], [data-testid="sqft-value"]\')?.innerText || null')
            year = await page.evaluate('() => document.querySelector(\'span[data-testid="year-built"]\')?.innerText || null')
            taxes = await page.evaluate('() => document.querySelector(\'[data-testid="property-tax"]\')?.innerText || null')
            last_sold = await page.evaluate('() => document.querySelector(\'.last-sold\')?.innerText || null')
            images = await page.locator('img[alt="Gallery Image"]').all()
            image_urls = []
            for img in images:
                src = await img.get_attribute('src')
                if src:
                    image_urls.append(src)
            return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls}
        except Exception as e:
            logger.error(f"Zillow fetch error: {e}")
            st.warning("Partial or no data from Zillow")
            return {'value': 'Failed', 'rent': 'Failed'}

    async def fetch_redfin(self, page, address_dict):
        try:
            # Use search approach - more reliable than guessing property IDs
            city = address_dict['city'].replace(' ', '-').lower()
            state = address_dict['state'].upper()
            street = address_dict['street'].replace(' ', '+')
            
            search_url = f"https://www.redfin.com/city/262/{state}/{city}/filter/address={street}"
            await self._retry_operation(page.goto, search_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(5, 10))  # Even longer delays for human-like behavior
            
            # Simulate human scrolling
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/4);')
            await asyncio.sleep(random.uniform(1, 2))
            
            # Get first property link using evaluate for reliability
            detail_url = await page.evaluate('''
                () => {
                    const link = document.querySelector('[data-rf-test-id="listing-link"] a, a[href*="/home/"], .listing-result a');
                    return link ? link.href : null;
                }
            ''')
            if detail_url and not detail_url.startswith('http'):
                detail_url = f"https://www.redfin.com{detail_url}"
            elif not detail_url:
                return {'value': 'No property found', 'rent': 'Failed'}
                
            await self._retry_operation(page.goto, detail_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(4, 8))  # Longer delay for property pages
            
            # Simulate human scrolling on property page
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/3);')
            await asyncio.sleep(random.uniform(1, 3))
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/2);')
            await asyncio.sleep(random.uniform(1, 2))
            
            # Get property data using page.evaluate for reliability
            value = await page.evaluate('() => document.querySelector("[data-rf-test-name=avm-price]")?.innerText || document.querySelector(".avm-value")?.innerText || null')
            rent = await page.evaluate('() => document.querySelector("[data-rf-test-name=rent-estimate]")?.innerText || null')
            beds = await page.evaluate('() => document.querySelector("[data-rf-test-name=bedroom-count]")?.innerText || null')
            baths = await page.evaluate('() => document.querySelector("[data-rf-test-name=bathroom-count]")?.innerText || null')
            sqft = await page.evaluate('() => document.querySelector("[data-rf-test-name=square-footage]")?.innerText || null')
            year = await page.evaluate('''() => {
                const yearRow = Array.from(document.querySelectorAll('.facts-table td')).find(td => td.innerText.includes('Year Built'));
                return yearRow ? yearRow.nextElementSibling?.innerText || null : null;
            }''')
            taxes = await page.evaluate('''() => {
                const taxRow = Array.from(document.querySelectorAll('.facts-table td')).find(td => td.innerText.includes('Tax'));
                return taxRow ? taxRow.nextElementSibling?.innerText || null : null;
            }''')
            last_sold = await page.evaluate('''() => {
                const soldRow = Array.from(document.querySelectorAll('.facts-table td')).find(td => td.innerText.includes('Sold'));
                return soldRow ? soldRow.nextElementSibling?.innerText || null : null;
            }''')
            
            # Get images safely
            image_urls = await page.evaluate('''
                () => {
                    const imgs = Array.from(document.querySelectorAll('img[src*="ssl.cdn-redfin.com"]'));
                    return imgs.map(img => img.src).slice(0, 5);
                }
            ''')
            
            return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls or []}
            
        except Exception as e:
            logger.error(f"Redfin fetch error: {e}")
            st.warning("Partial or no data from Redfin")
            return {'value': 'Failed', 'rent': 'Failed'}

    async def fetch_homes(self, page, address_dict):
        try:
            # Use search approach for Homes.com
            street = address_dict['street'].replace(' ', '%20')
            city = address_dict['city'].replace(' ', '%20')
            state = address_dict['state']
            zipcode = address_dict['zip']
            
            search_url = f"https://www.homes.com/search/?q={street}%2C%20{city}%2C%20{state}%20{zipcode}"
            await self._retry_operation(page.goto, search_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(5, 10))  # Even longer delays for human-like behavior
            
            # Simulate human scrolling
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/4);')
            await asyncio.sleep(random.uniform(1, 2))
            
            # Get first property link using evaluate for reliability
            detail_url = await page.evaluate('''
                () => {
                    const link = document.querySelector('a[href*="/property/"], .property-card a, .listing-card a');
                    return link ? link.href : null;
                }
            ''')
            
            if detail_url and not detail_url.startswith('http'):
                detail_url = f"https://www.homes.com{detail_url}"
            elif not detail_url:
                return {'value': 'No property found', 'rent': 'Failed'}
                
            await self._retry_operation(page.goto, detail_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(4, 8))  # Longer delay for property pages
            
            # Simulate human scrolling on property page
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/3);')
            await asyncio.sleep(random.uniform(1, 3))
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/2);')
            await asyncio.sleep(random.uniform(1, 2))
            
            # Get property data using page.evaluate for reliability
            value = await page.evaluate('() => document.querySelector(".estimated-value, .price, .current-price")?.innerText || null')
            rent = await page.evaluate('() => document.querySelector(".estimated-rent, .rent-estimate")?.innerText || null')
            beds = await page.evaluate('() => document.querySelector(".beds, .bedroom-count, [data-label=\'beds\'], .fact-beds")?.innerText || null')
            baths = await page.evaluate('() => document.querySelector(".baths, .bathroom-count, [data-label=\'baths\'], .fact-baths")?.innerText || null')
            sqft = await page.evaluate('() => document.querySelector(".sqft, .square-feet, [data-label=\'sqft\'], .fact-sqft")?.innerText || null')
            year = await page.evaluate('() => document.querySelector(".year-built, [data-label=\'year\'], .fact-year")?.innerText || null')
            taxes = await page.evaluate('() => document.querySelector(".taxes, .property-tax, .tax-amount")?.innerText || null')
            last_sold = await page.evaluate('() => document.querySelector(".last-sold, .sold-date, .sale-history")?.innerText || null')
            
            # Get images safely
            image_urls = await page.evaluate('''
                () => {
                    const imgs = Array.from(document.querySelectorAll('img[src*="homes.com"], .property-image img, .gallery img'));
                    return imgs.map(img => img.src).filter(src => src && !src.includes('icon')).slice(0, 5);
                }
            ''')
            
            return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls or []}
            
        except Exception as e:
            logger.error(f"Homes fetch error: {e}")
            st.warning("Partial or no data from Homes.com")
            return {'value': 'Failed', 'rent': 'Failed'}

    async def fetch_realtor(self, page, address_dict):
        """Fetch data from Realtor using direct URL pattern (similar to Zillow _rb approach)"""
        try:
            street = address_dict['street'].replace(' ', '-')
            city = address_dict['city'].replace(' ', '-')
            state = address_dict['state']
            zipcode = address_dict['zip']
            
            # Try direct property URL first (like Zillow _rb pattern)  
            # Format: /realestateandhomes-detail/[ADDRESS]_[CITY]_[STATE]_[ZIP]
            direct_url = f"https://www.realtor.com/realestateandhomes-detail/{street}_{city}_{state}_{zipcode}"
            
            try:
                logger.info(f"Trying Realtor direct URL: {direct_url}")
                await self._retry_operation(page.goto, direct_url, wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(random.uniform(3, 6))
                
                # Check if we got a valid property page
                value = await page.evaluate('() => document.querySelector("[data-testid=current-estimate], [data-testid=card-price], .price, .ldp-price")?.innerText || null')
                if value and value not in ['N/A', '']:
                    # Success with direct URL - get all data
                    rent = await page.evaluate('() => document.querySelector("[data-testid=rent-estimate], .rent-estimate, .rental-estimate")?.innerText || null')
                    beds = await page.evaluate('() => document.querySelector("[data-testid=property-meta-beds] span, [data-testid=bed-count], .beds")?.innerText || null')
                    baths = await page.evaluate('() => document.querySelector("[data-testid=property-meta-baths] span, [data-testid=bath-count], .baths")?.innerText || null')
                    sqft = await page.evaluate('() => document.querySelector("[data-testid=property-meta-sqft] span, [data-testid=sqft], .sqft")?.innerText || null')
                    year = await page.evaluate('() => document.querySelector("[data-testid=property-meta-year-built] span, [data-testid=year-built], .year-built")?.innerText || null')
                    taxes = await page.evaluate('() => document.querySelector(".property-tax, .taxes, .tax-amount")?.innerText || null')
                    last_sold = await page.evaluate('() => document.querySelector(".last-sold, .sold-date, .sale-date")?.innerText || null')
                    
                    # Get images
                    image_urls = await page.evaluate('''
                        () => {
                            const imgs = Array.from(document.querySelectorAll('img[src*="realtor.com"], .gallery img, .photo-gallery img'));
                            return imgs.map(img => img.src).filter(src => src && !src.includes('icon') && src.includes('realtor')).slice(0, 5);
                        }
                    ''')
                    
                    logger.info(f"Realtor direct URL success!")
                    return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls}
            except Exception as direct_error:
                logger.warning(f"Realtor direct URL failed, trying search fallback: {direct_error}")
            
            # Fallback: Use search approach if direct URL doesn't work
            search_url = f"https://www.realtor.com/realestateandhomes-search/{city}_{state}/type-single-family-home?address={street.replace('-', '+')}+{zipcode}"
            logger.info(f"Trying Realtor search: {search_url}")
            await self._retry_operation(page.goto, search_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(5, 8))
            
            # Look for first property link
            detail_url = await page.evaluate('''
                () => {
                    const link = document.querySelector('a[href*="/realestateandhomes-detail/"]');
                    return link ? link.href : null;
                }
            ''')
            
            if not detail_url:
                return {'value': 'No property found', 'rent': 'N/A'}
            
            await self._retry_operation(page.goto, detail_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(4, 7))
            
            # Get all property data with multiple selector fallbacks
            value = await page.evaluate('() => document.querySelector("[data-testid=current-estimate], [data-testid=card-price], .price, .ldp-price")?.innerText || null')
            rent = await page.evaluate('() => document.querySelector("[data-testid=rent-estimate], .rent-estimate, .rental-estimate")?.innerText || null')
            beds = await page.evaluate('() => document.querySelector("[data-testid=property-meta-beds] span, [data-testid=bed-count], .beds")?.innerText || null')
            baths = await page.evaluate('() => document.querySelector("[data-testid=property-meta-baths] span, [data-testid=bath-count], .baths")?.innerText || null')
            sqft = await page.evaluate('() => document.querySelector("[data-testid=property-meta-sqft] span, [data-testid=sqft], .sqft")?.innerText || null')
            year = await page.evaluate('() => document.querySelector("[data-testid=property-meta-year-built] span, [data-testid=year-built], .year-built")?.innerText || null')
            taxes = await page.evaluate('() => document.querySelector(".property-tax, .taxes")?.innerText || null')
            last_sold = await page.evaluate('() => document.querySelector(".last-sold, .sold-date")?.innerText || null')
            
            image_urls = await page.evaluate('''
                () => {
                    const imgs = Array.from(document.querySelectorAll('img[src*="realtor.com"], .gallery img, .photo-gallery img'));
                    return imgs.map(img => img.src).filter(src => src && !src.includes('icon')).slice(0, 5);
                }
            ''')
            
            logger.info(f"Realtor search fallback success!")
            return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls}
        except Exception as e:
            logger.error(f"Realtor fetch error: {e}")
            return {'value': 'Failed', 'rent': 'Failed'}

    async def fetch_movoto(self, page, address_dict):
        """Fetch data from Movoto"""
        try:
            street = address_dict['street'].replace(' ', '-').lower()
            city = address_dict['city'].replace(' ', '-').lower()
            state = address_dict['state'].lower()
            zipcode = address_dict['zip']
            
            # Movoto URL pattern: https://www.movoto.com/state/city/street-zipcode/
            movoto_url = f"https://www.movoto.com/{state}/{city}/{street}-{zipcode}/"
            await self._retry_operation(page.goto, movoto_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(3, 7))
            
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/4);')
            await asyncio.sleep(random.uniform(1, 2))
            
            # Get property data using common selectors
            value = await page.evaluate('() => document.querySelector(".price, .estimated-value, .listing-price, .home-price")?.innerText || null')
            rent = await page.evaluate('() => document.querySelector(".rent-estimate, .rental-estimate")?.innerText || null')
            beds = await page.evaluate('() => document.querySelector(".beds, .bedrooms, .bed-count")?.innerText || null')
            baths = await page.evaluate('() => document.querySelector(".baths, .bathrooms, .bath-count")?.innerText || null')
            sqft = await page.evaluate('() => document.querySelector(".sqft, .square-feet, .area")?.innerText || null')
            year = await page.evaluate('() => document.querySelector(".year-built, .build-year")?.innerText || null')
            taxes = await page.evaluate('() => document.querySelector(".taxes, .property-tax, .tax-info")?.innerText || null')
            last_sold = await page.evaluate('() => document.querySelector(".last-sold, .sold-date, .sale-date")?.innerText || null')
            
            # Get images
            image_urls = await page.evaluate('''
                () => {
                    const imgs = Array.from(document.querySelectorAll('img[src*="movoto"], .property-image img, .photo img'));
                    return imgs.map(img => img.src).filter(src => src && !src.includes('icon')).slice(0, 5);
                }
            ''')
            
            return {'value': value, 'rent': rent, 'beds': beds, 'baths': baths, 'sqft': sqft, 'year': year, 'taxes': taxes, 'last_sold': last_sold, 'images': image_urls or []}
        except Exception as e:
            logger.error(f"Movoto fetch error: {e}")
            st.warning("Partial or no data from Movoto")
            return {'value': 'Failed', 'rent': 'Failed'}

    async def fetch_all(self, address_dict):
        # Validate proxy credentials
        if not self.proxy.get('username') or not self.proxy.get('password'):
            logger.error("Proxy credentials not found. Please set BRIGHT_DATA_USERNAME and BRIGHT_DATA_PASSWORD environment variables.")
            st.error("Proxy credentials missing. Please check your .env file.")
            return {'zillow': {'value': 'Failed', 'rent': 'Failed'},
                    'redfin': {'value': 'Failed', 'rent': 'Failed'},
                    'homes': {'value': 'Failed', 'rent': 'Failed'},
                    'realtor': {'value': 'Failed', 'rent': 'Failed'}}
        
        # Configure SSL certificate handling
        ssl_configured = False
        if self.cert_path and os.path.exists(self.cert_path):
            # Try NODE_EXTRA_CA_CERTS for Node.js/Playwright
            os.environ['NODE_EXTRA_CA_CERTS'] = self.cert_path
            logger.info(f"SSL certificate path set: {self.cert_path}")
            ssl_configured = True
        
        try:
            async with async_playwright() as p:
                # Configure browser arguments based on SSL setup
                # Enhanced anti-bot detection arguments
                browser_args = [
                    '--disable-http2',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI,VizDisplayCompositor',
                    '--disable-ipc-flooding-protection',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-automation',
                    '--disable-web-security',
                    '--allow-running-insecure-content'
                ]
                
                if ssl_configured and not self.ignore_https_errors:
                    # With SSL certificate configured, rely on system trust
                    logger.info("Using SSL certificate - relying on macOS Keychain trust")
                elif self.ignore_https_errors:
                    # Fallback to ignore SSL errors
                    browser_args.extend([
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--allow-running-insecure-content'
                    ])
                    logger.info("Using ignore SSL errors mode")
                
                # Use Chromium for now (simplify to avoid timeout issues)
                browser = await p.chromium.launch(proxy=self.proxy, args=browser_args)
                    
                # Enhanced context options to mimic real browser
                context_options = {
                    'user_agent': random.choice(user_agents),
                    'ignore_https_errors': self.ignore_https_errors and not ssl_configured,
                    'viewport': {'width': 1920, 'height': 1080},
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                    'permissions': ['geolocation'],
                    'geolocation': {'latitude': 41.0814, 'longitude': -81.5190},  # Akron, OH coordinates
                    'extra_http_headers': {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                }
                context = await browser.new_context(**context_options)
                
                # Enhanced stealth scripts to avoid detection
                await context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Override the plugins property to use a custom getter
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Override the languages property to use a custom getter
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Mock chrome runtime
                    if (!window.chrome) {
                        window.chrome = { runtime: {} };
                    }
                    
                    // Override permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                    );
                    
                    // Hide automation indicators
                    delete window.navigator.__proto__.webdriver;
                """)
                page1 = await context.new_page()
                page2 = await context.new_page()
                page3 = await context.new_page()
                page4 = await context.new_page()
                page5 = await context.new_page()
                tasks = [
                    self.fetch_zillow(page1, address_dict),
                    self.fetch_redfin(page2, address_dict),
                    self.fetch_homes(page3, address_dict),
                    self.fetch_realtor(page4, address_dict),
                    self.fetch_movoto(page5, address_dict)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                await browser.close()
        except Exception as e:
            logger.error(f"Browser initialization error: {e}")
            st.error(f"Failed to initialize browser: {str(e)}")
            return {'zillow': {'value': 'Failed', 'rent': 'Failed'},
                    'redfin': {'value': 'Failed', 'rent': 'Failed'},
                    'homes': {'value': 'Failed', 'rent': 'Failed'},
                    'realtor': {'value': 'Failed', 'rent': 'Failed'},
                    'movoto': {'value': 'Failed', 'rent': 'Failed'}}
        
        data = {'zillow': results[0] if not isinstance(results[0], Exception) else {'value': 'Failed', 'rent': 'Failed'},
                'redfin': results[1] if not isinstance(results[1], Exception) else {'value': 'Failed', 'rent': 'Failed'},
                'homes': results[2] if not isinstance(results[2], Exception) else {'value': 'Failed', 'rent': 'Failed'},
                'realtor': results[3] if not isinstance(results[3], Exception) else {'value': 'Failed', 'rent': 'Failed'},
                'movoto': results[4] if not isinstance(results[4], Exception) else {'value': 'Failed', 'rent': 'Failed'}}
        return data

class AggregatorAgent:
    def aggregate(self, data):
        values = []
        rents = []
        beds = []
        baths = []
        sqfts = []
        years = []
        taxes = []
        last_solds = []
        images = []
        
        def safe_float_extract(val):
            """Safely extract float from value - handles both strings and numbers"""
            if val is None or val in ['Failed', 'N/A', 'No data found', 'API Error', 'Trigger failed', 'Timeout', 'Processing...', 'Dataset N/A']:
                return None
            try:
                # If it's already a number, return it
                if isinstance(val, (int, float)):
                    return float(val)
                # If it's a string, clean it up
                if isinstance(val, str):
                    cleaned = val.replace('$', '').replace(',', '').split('/')[0].split()[0]
                    return float(cleaned)
                return None
            except:
                return None
                
        def safe_int_extract(val):
            """Safely extract int from value - handles both strings and numbers"""
            if val is None or val in ['Failed', 'N/A', 'No data found', 'API Error', 'Trigger failed', 'Timeout', 'Processing...', 'Dataset N/A']:
                return None
            try:
                # If it's already a number, return it
                if isinstance(val, (int, float)):
                    return int(val)
                # If it's a string, clean it up
                if isinstance(val, str):
                    cleaned = val.replace('$', '').replace(',', '').split()[0]
                    return int(cleaned)
                return None
            except:
                return None
        
        for site, site_data in data.items():
            if isinstance(site_data, dict):
                # Extract value (property price)
                val = safe_float_extract(site_data.get('value'))
                if val is not None:
                    values.append(val)
                
                # Extract rent
                ren = safe_float_extract(site_data.get('rent'))
                if ren is not None:
                    rents.append(ren)
                    
                # Extract beds
                bed = safe_float_extract(site_data.get('beds'))
                if bed is not None:
                    beds.append(bed)
                    
                # Extract baths
                bath = safe_float_extract(site_data.get('baths'))
                if bath is not None:
                    baths.append(bath)
                    
                # Extract sqft
                sqft = safe_float_extract(site_data.get('sqft'))
                if sqft is not None:
                    sqfts.append(sqft)
                    
                # Extract year
                year = safe_int_extract(site_data.get('year'))
                if year is not None:
                    years.append(year)
                    
                # Extract taxes (keep as-is)
                if 'taxes' in site_data and site_data['taxes'] not in [None, 'Failed', 'N/A']:
                    taxes.append(site_data['taxes'])
                    
                # Extract last_sold (keep as-is) 
                if 'last_sold' in site_data and site_data['last_sold'] not in [None, 'Failed', 'N/A']:
                    last_solds.append(site_data['last_sold'])
                    
                # Extract images
                if 'images' in site_data and site_data['images']:
                    images.extend(site_data['images'])
                    
        # Track successful sites for better user feedback
        successful_sites = []
        failed_sites = []
        
        for site, site_data in data.items():
            if isinstance(site_data, dict) and site_data.get('value') not in ['Failed', 'N/A', None, 'API N/A', 'Dataset N/A', 'No property found', 'Trigger failed', 'Processing...']:
                successful_sites.append(site.title())
            else:
                failed_sites.append(site.title())
        
        aggregated = {
            'value': np.mean(values) if values else None,
            'rent': np.mean(rents) if rents else None,
            'beds': np.mean(beds) if beds else None,
            'baths': np.mean(baths) if baths else None,
            'sqft': np.mean(sqfts) if sqfts else None,
            'year': np.mean(years) if years else None,
            'taxes': taxes[0] if taxes else None,
            'last_sold': last_solds[0] if last_solds else None,
            'images': images[:10] if images else [],  # Take first 10 images, avoid set() on dicts
            'successful_sites': successful_sites,
            'failed_sites': failed_sites,
            'data_quality': f"{len(successful_sites)}/{len(data)} sites successful"
        }
        
        # Display cascade information to user
        if successful_sites:
            st.success(f"✅ Data from {len(successful_sites)}/5 sites: {', '.join(successful_sites)}")
        if failed_sites:
            st.warning(f"⚠️ Failed sites: {', '.join(failed_sites)}")
        if len(successful_sites) < 2:
            st.error("❌ Less than 2 sites successful - data reliability may be low")
            
        return aggregated, data

class AnalyzerAgent:
    def __init__(self, settings):
        self.settings = settings

    def analyze(self, aggregated, user_inputs):
        purchase = user_inputs.get('purchase', 0)
        reno = user_inputs.get('reno', 0)
        arv = aggregated['value'] or 0
        rent = aggregated['rent'] or 0
        hold_days = self.settings['hold_days_base'] + (reno // 10000) * 7
        hold_months = hold_days / 30
        monthly_carrying = max(0.007 * purchase, 500)
        carrying = monthly_carrying * hold_months
        sale_costs = arv * (self.settings['brokerage'] + self.settings['sales_closing']) / 100
        net_profit = arv - purchase - reno - carrying - sale_costs - (purchase * self.settings['acquisition'] / 100)
        total_invest = purchase * (1 - self.settings['ltv'] / 100) + reno
        roi = (net_profit / total_invest * 100) if total_invest else 0
        noi = rent * 12 * (1 - self.settings['vacancy']/100 - self.settings['maintenance']/100 - self.settings['management']/100)
        cap_rate = (noi / purchase * 100) if purchase else 0
        down = purchase * (1 - self.settings['ltv']/100)
        mortgage_monthly = (purchase * self.settings['ltv']/100 * self.settings['interest']/100 / 12) / (1 - (1 + self.settings['interest']/100 / 12)**(-self.settings['amortization']*12)) if self.settings['amortization'] else 0
        cash_flow = rent - mortgage_monthly - (rent * (self.settings['vacancy'] + self.settings['maintenance'] + self.settings['management'])/100)
        cash_on_cash = (cash_flow * 12 / down * 100) if down else 0
        cashflows = [-down - reno] + [cash_flow] * int(user_inputs.get('hold_months', 12)) + [arv - purchase * (1 - self.settings['ltv']/100) - carrying - sale_costs]
        try:
            irr = npf.irr(cashflows) * 100 if len(cashflows) > 1 else 0
        except:
            irr = 0
        return {
            'net_profit': net_profit,
            'roi': roi,
            'cap_rate': cap_rate,
            'cash_flow': cash_flow,
            'cash_on_cash': cash_on_cash,
            'irr': irr,
            'basis': purchase + reno + carrying + (purchase * self.settings['acquisition']/100)
        }

class OutputRendererAgent:
    def render_summary(self, aggregated, metrics):
        # Professional Property Summary with horizontal layout
        st.subheader("🏠 Property Overview")
        
        # Property basics in horizontal layout
        prop_col1, prop_col2, prop_col3, prop_col4 = st.columns(4)
        
        with prop_col1:
            st.metric("💰 Property Value", f"${aggregated.get('value', 'N/A'):,}" if isinstance(aggregated.get('value'), (int, float)) else aggregated.get('value', 'N/A'))
            
        with prop_col2:
            st.metric("🏠 Monthly Rent", f"${aggregated.get('rent', 'N/A'):,}" if isinstance(aggregated.get('rent'), (int, float)) else aggregated.get('rent', 'N/A'))
            
        with prop_col3:
            beds_baths = f"{aggregated.get('beds', 'N/A')} bed / {aggregated.get('baths', 'N/A')} bath"
            st.metric("🛌 Bed/Bath", beds_baths)
            
        with prop_col4:
            st.metric("📅 Year Built", f"{int(aggregated.get('year', 0))}" if isinstance(aggregated.get('year'), (int, float)) and aggregated.get('year', 0) > 0 else 'N/A')
        
        # Investment Analysis
        st.subheader("📊 Investment Analysis")
        col1, col2, col3 = st.columns(3)
        col1.metric("💹 Cap Rate", f"{metrics['cap_rate']:.2f}%" if metrics['cap_rate'] else "N/A")
        col2.metric("💵 Monthly Cash Flow", f"${metrics['cash_flow']:.2f}" if metrics['cash_flow'] else "N/A")
        col3.metric("📈 Cash on Cash", f"{metrics['cash_on_cash']:.2f}%" if metrics['cash_on_cash'] else "N/A")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("🚀 IRR", f"{metrics['irr']:.2f}%" if metrics['irr'] else "N/A")
        col5.metric("🎯 Net Profit", f"${metrics['net_profit']:.0f}" if metrics['net_profit'] else "N/A")
        col6.metric("📈 ROI", f"{metrics['roi']:.1f}%" if metrics['roi'] else "N/A")

    def render_details(self, aggregated, site_data, images, metrics):
        # Professional Property Data Display
        st.subheader("📊 Property Valuation Summary")
        
        # Create a clean horizontal layout for key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Estimated Value", f"${aggregated.get('value', 'N/A'):,}" if isinstance(aggregated.get('value'), (int, float)) else aggregated.get('value', 'N/A'))
            
        with col2:
            st.metric("🏠 Monthly Rent", f"${aggregated.get('rent', 'N/A'):,}" if isinstance(aggregated.get('rent'), (int, float)) else aggregated.get('rent', 'N/A'))
            
        with col3:
            st.metric("🏛️ Annual Taxes", f"${aggregated.get('taxes', 'N/A'):,}" if isinstance(aggregated.get('taxes'), (int, float)) else aggregated.get('taxes', 'N/A'))
            
        with col4:
            st.metric("📅 Last Sold", aggregated.get('last_sold', 'N/A'))
        
        # Property Details in a clean format
        st.subheader("🏡 Property Details")
        detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
        
        with detail_col1:
            st.write("**🛏️ Bedrooms**")
            st.write(f"{aggregated.get('beds', 'N/A')}")
            
        with detail_col2:
            st.write("**🛁 Bathrooms**") 
            st.write(f"{aggregated.get('baths', 'N/A')}")
            
        with detail_col3:
            st.write("**📐 Square Feet**")
            st.write(f"{aggregated.get('sqft', 'N/A'):,}" if isinstance(aggregated.get('sqft'), (int, float)) else aggregated.get('sqft', 'N/A'))
            
        with detail_col4:
            st.write("**🏗️ Year Built**")
            st.write(f"{int(aggregated.get('year', 0))}" if isinstance(aggregated.get('year'), (int, float)) and aggregated.get('year', 0) > 0 else 'N/A')

        # Data Sources in a clean horizontal table
        st.subheader("🌐 Data Sources Comparison")
        
        if site_data:
            # Create a comprehensive comparison table showing ALL 5 sources
            comparison_data = []
            for site_name, site_info in site_data.items():
                # Show ALL sites, regardless of success/failure
                value = site_info.get('value', 'N/A')
                rent = site_info.get('rent', 'N/A')
                
                # Determine status
                if value not in ['N/A', 'Failed', 'API Error', 'Trigger failed', 'Timeout', 'Processing...', 'No property found', 'Dataset N/A', 'API N/A']:
                    status = '✅ Success'
                    formatted_value = f"${value:,}" if isinstance(value, (int, float)) else str(value)
                    formatted_rent = f"${rent:,}" if isinstance(rent, (int, float)) else str(rent)
                else:
                    status = f'❌ {value}' if value in ['Failed', 'API Error', 'Trigger failed', 'Timeout', 'Processing...', 'No property found'] else '❌ Not Available'
                    formatted_value = value
                    formatted_rent = rent
                
                comparison_data.append({
                    'Source': site_name.title(),
                    'Property Value': formatted_value,
                    'Rent Estimate': formatted_rent,
                    'Status': status
                })
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            else:
                st.info("No data sources available")

        # Property Images with clean presentation
        st.subheader("📸 Property Images")
        
        # Filter and prioritize images by source (Zillow first, then others)
        zillow_images = aggregated.get('images', [])
        
        if zillow_images:
            # Process only first 4-6 images to avoid wrong property images
            valid_images = []
            for img in zillow_images[:4]:  # Limit to first 4 to ensure correct property
                try:
                    image_url = None
                    if isinstance(img, dict):
                        if 'mixedSources' in img and 'jpeg' in img['mixedSources']:
                            jpeg_sources = img['mixedSources']['jpeg']
                            if jpeg_sources and isinstance(jpeg_sources, list) and len(jpeg_sources) > 0:
                                image_url = jpeg_sources[-1].get('url')
                        elif 'url' in img:
                            image_url = img['url']
                    elif isinstance(img, str) and img.startswith('http'):
                        image_url = img
                    
                    if image_url and 'zillow' in image_url.lower():  # Prioritize Zillow images
                        valid_images.append(image_url)
                except Exception as e:
                    continue
            
            if valid_images:
                # Display images in a grid layout
                cols = st.columns(2)  # Use 2 columns for better visibility
                for i, url in enumerate(valid_images[:4]):  # Max 4 images
                    with cols[i % 2]:
                        try:
                            st.image(url, caption=f"Property Image {i+1}", use_container_width=True)
                        except Exception as e:
                            st.markdown(f"🔗 [Image {i+1}]({url})")
            else:
                st.info("Images found but may not be from correct property source")
        else:
            st.info("No images available for this property")

        # Investment Analysis Chart
        st.subheader("📈 12-Month Cash Flow Projection")
        fig, ax = plt.subplots(figsize=(12, 6))
        months = range(1, 13)
        monthly_cash_flow = metrics.get('cash_flow', 0)
        cumulative = [monthly_cash_flow * m for m in months]
        
        # Create a professional-looking chart
        ax.plot(months, cumulative, marker='o', linewidth=3, markersize=8, color='#2E86AB', markerfacecolor='#F24236')
        ax.fill_between(months, cumulative, alpha=0.3, color='#2E86AB')
        
        ax.set_title('Projected Cumulative Cash Flow', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Cumulative Cash Flow ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
        
        # Add value annotations
        for i, v in enumerate(cumulative):
            if i % 2 == 0:  # Show every other month to avoid crowding
                ax.annotate(f'${v:,.0f}', (i+1, v), textcoords="offset points", 
                           xytext=(0,15), ha='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Key Investment Metrics
        st.subheader("💼 Investment Analysis")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("💰 Monthly Cash Flow", f"${metrics.get('cash_flow', 0):,.0f}")
            st.metric("📊 Cap Rate", f"{metrics.get('cap_rate', 0):.2f}%")
            
        with metric_col2:
            st.metric("🏦 Cash-on-Cash ROI", f"{metrics.get('coc_return', 0):.2f}%")
            st.metric("💡 Total ROI", f"{metrics.get('total_return', 0):.2f}%")
            
        with metric_col3:
            st.metric("⚡ Break-Even Point", f"{metrics.get('break_even', 0):.0f} months" if metrics.get('break_even', 0) > 0 else "N/A")
            st.metric("🎯 Recommendation", "✅ Analyze" if metrics.get('cash_flow', 0) > 0 else "❌ Pass")
        
        # Cash Flow Projection Chart
        st.subheader("📈 12-Month Cash Flow Projection")
        if metrics.get('cash_flow', 0) != 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            months = list(range(1, 13))
            monthly_cash_flow = metrics.get('cash_flow', 0)
            cumulative = [monthly_cash_flow * m for m in months]
            
            # Create professional chart
            ax.plot(months, cumulative, marker='o', linewidth=3, markersize=8, 
                   color='#2E86AB', markerfacecolor='#F24236')
            ax.fill_between(months, cumulative, alpha=0.3, color='#2E86AB')
            
            ax.set_title('Projected Cumulative Cash Flow', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Month', fontsize=12)
            ax.set_ylabel('Cumulative Cash Flow ($)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
            
            # Add value annotations
            for i, v in enumerate(cumulative):
                if i % 2 == 0:  # Show every other month to avoid crowding
                    ax.annotate(f'${v:,.0f}', (i+1, v), textcoords="offset points", 
                               xytext=(0,15), ha='center', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No cash flow data available for chart")
        
        # Comparable Properties section 
        st.subheader("🏘️ Comparable Properties")
        # Skip comps API call - using direct Bright Data integration
        comps = {}
        if comps:
            st.table(pd.DataFrame(comps))
        else:
            st.info("Comparable properties analysis not available")

class CRMNotifierAgent:
    def notify(self, metrics, threshold):
        if metrics['roi'] > threshold:
            st.write("Alert: Property meets requirements! Review now.")
            # Placeholder for email/SMS (add smtplib/Twilio with keys)

# Bright Data Scraper API Agent - Uses Bright Data's proven scrapers
class BrightDataScraperAgent:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = BRIGHT_DATA_API_BASE
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        # Cache for known working snapshots
        self.known_snapshots = {
            "1841-marks-ave-akron-oh-44305": "s_mf5nalqb1xmho43n2",  # From earlier successful test
        }
    
    def trigger_scrape(self, dataset_id, url):
        """Trigger a new scrape request and return snapshot ID"""
        try:
            endpoint = f"{self.base_url}/trigger?dataset_id={dataset_id}&format=json"
            payload = [{"url": url}]
            
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('snapshot_id')
            else:
                logger.error(f"Bright Data trigger error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Bright Data trigger error: {e}")
            return None
    
    def get_snapshot_data(self, snapshot_id):
        """Retrieve data from snapshot"""
        try:
            endpoint = f"{self.base_url}/snapshot/{snapshot_id}?format=json"
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Bright Data snapshot error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Bright Data snapshot error: {e}")
            return None
    
    def wait_for_completion(self, snapshot_id, max_wait_minutes=5):
        """Wait for snapshot to complete"""
        import time
        max_wait_seconds = max_wait_minutes * 60
        wait_interval = 5  # Check every 5 seconds (faster)
        total_waited = 0
        
        logger.info(f"Waiting up to {max_wait_minutes} minutes for snapshot {snapshot_id}")
        
        while total_waited < max_wait_seconds:
            try:
                # Check progress
                progress_endpoint = f"{self.base_url}/progress/{snapshot_id}"
                response = requests.get(progress_endpoint, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    progress = response.json()
                    status = progress.get('status', 'running')
                    records = progress.get('records', 0)
                    
                    logger.info(f"Progress check: status={status}, records={records}, waited={total_waited}s")
                    
                    if status == 'ready' or status == 'completed':
                        logger.info(f"Snapshot {snapshot_id} completed with {records} records")
                        return True
                    elif status == 'failed':
                        logger.error(f"Snapshot {snapshot_id} failed")
                        return False
                    
                    # Still running, wait more
                    time.sleep(wait_interval)
                    total_waited += wait_interval
                else:
                    logger.error(f"Progress check failed: {response.status_code} - {response.text}")
                    time.sleep(wait_interval)
                    total_waited += wait_interval
                    
            except Exception as e:
                logger.error(f"Progress check error: {e}")
                time.sleep(wait_interval)
                total_waited += wait_interval
        
        logger.warning(f"Snapshot {snapshot_id} timed out after {max_wait_minutes} minutes")
        return False
    
    def _extract_value(self, data, field_names):
        """Extract value from data using multiple possible field names"""
        for field in field_names:
            if field in data and data[field] is not None:
                return data[field]
        return 'N/A'
    
    def scrape_zillow(self, address_dict):
        """Use Bright Data's Zillow scraper API with smart caching"""
        # Generate property key and URL
        street = address_dict['street'].replace(' ', '-')
        city = address_dict['city'].replace(' ', '-')
        state = address_dict['state']
        zipcode = address_dict['zip']
        
        property_key = f"{street}-{city}-{state}-{zipcode}".lower()
        zillow_url = f"https://www.zillow.com/homes/{street}-{city}-{state}-{zipcode}_rb/"
        logger.info(f"Zillow API: Starting scrape for {zillow_url}")
        
        # Check if we have a cached snapshot first
        if property_key in self.known_snapshots:
            cached_snapshot = self.known_snapshots[property_key]
            logger.info(f"Zillow API: Using cached snapshot {cached_snapshot}")
            
            # Try to get data from cached snapshot
            data = self.get_snapshot_data(cached_snapshot)
            if data and len(data) > 0:
                logger.info(f"Zillow API: Successfully got cached data")
                property_data = data[0] if isinstance(data, list) else data
                return {
                    'value': property_data.get('price', property_data.get('zestimate', 'N/A')),
                    'rent': property_data.get('rentZestimate', 'N/A'),
                    'beds': property_data.get('bedrooms', 'N/A'),
                    'baths': property_data.get('bathrooms', 'N/A'),
                    'sqft': property_data.get('livingArea', 'N/A'),
                    'year': property_data.get('yearBuilt', 'N/A'),
                    'taxes': property_data.get('taxHistory', [{}])[0].get('taxPaid', 'N/A') if property_data.get('taxHistory') else 'N/A',
                    'last_sold': property_data.get('priceHistory', [{}])[0].get('date', 'N/A') if property_data.get('priceHistory') else 'N/A',
                    'images': property_data.get('photos', [])[:5]
                }
            else:
                logger.warning(f"Zillow API: Cached snapshot {cached_snapshot} has no data")
        
        try:
            # Step 1: Trigger new scrape
            logger.info(f"Zillow API: Triggering new scrape...")
            snapshot_id = self.trigger_scrape(BRIGHT_DATA_ZILLOW_DATASET, zillow_url)
            if not snapshot_id:
                logger.error(f"Zillow API: Trigger failed")
                return {'value': 'Trigger failed', 'rent': 'Trigger failed'}
            
            logger.info(f"Zillow API: Got snapshot ID: {snapshot_id}")
            
            # Step 2: Wait for completion (30 seconds max for faster response)
            logger.info(f"Zillow API: Waiting for completion...")
            if not self.wait_for_completion(snapshot_id, max_wait_minutes=0.5):  # 30 seconds
                logger.warning(f"Zillow API: Timeout after 30 seconds - returning partial result")
                return {'value': 'Processing...', 'rent': 'Processing...'}
            
            # Step 3: Get the data
            logger.info(f"Zillow API: Getting snapshot data...")
            data = self.get_snapshot_data(snapshot_id)
            if not data or len(data) == 0:
                logger.warning(f"Zillow API: No data found")
                return {'value': 'No data found', 'rent': 'N/A'}
            
            # Cache successful snapshot for future use
            self.known_snapshots[property_key] = snapshot_id
            logger.info(f"Zillow API: Cached snapshot {snapshot_id} for {property_key}")
            
            # Parse the first property result
            property_data = data[0] if isinstance(data, list) else data
            logger.info(f"Zillow API: Successfully got property data")
            return {
                'value': property_data.get('price', property_data.get('zestimate', 'N/A')),
                'rent': property_data.get('rentZestimate', 'N/A'),
                'beds': property_data.get('bedrooms', 'N/A'),
                'baths': property_data.get('bathrooms', 'N/A'),
                'sqft': property_data.get('livingArea', 'N/A'),
                'year': property_data.get('yearBuilt', 'N/A'),
                'taxes': property_data.get('taxHistory', [{}])[0].get('taxPaid', 'N/A') if property_data.get('taxHistory') else 'N/A',
                'last_sold': property_data.get('priceHistory', [{}])[0].get('date', 'N/A') if property_data.get('priceHistory') else 'N/A',
                'images': property_data.get('photos', [])[:5]  # First 5 images
            }
                
        except Exception as e:
            logger.error(f"Bright Data Zillow scraper error: {e}")
            return {'value': 'Failed', 'rent': 'Failed'}
    
    def scrape_realtor(self, address_dict):
        """Use Bright Data's Realtor.com scraper API with trigger/wait pattern"""
        try:
            # Generate Realtor.com property URL (more direct than search)
            street = address_dict['street'].replace(' ', '-').lower()
            city = address_dict['city'].replace(' ', '-').lower()
            state = address_dict['state'].lower()
            zipcode = address_dict['zip']
            
            # Use direct property URL format for better results
            realtor_url = f"https://www.realtor.com/realestateandhomes-detail/{street}_{city}_{state}_{zipcode}"
            logger.info(f"Realtor API: Starting scrape for {realtor_url}")
            
            # Step 1: Trigger scrape
            snapshot_id = self.trigger_scrape(BRIGHT_DATA_REALTOR_DATASET, realtor_url)
            if not snapshot_id:
                logger.error(f"Realtor API: Trigger failed")
                return {'value': 'Trigger failed', 'rent': 'Trigger failed'}
            
            logger.info(f"Realtor API: Got snapshot ID: {snapshot_id}")
            
            # Step 2: Wait for completion (30 seconds max)
            if not self.wait_for_completion(snapshot_id, max_wait_minutes=0.5):
                logger.warning(f"Realtor API: Timeout after 30 seconds")
                return {'value': 'Processing...', 'rent': 'Processing...'}
            
            # Step 3: Get the data
            data = self.get_snapshot_data(snapshot_id)
            if not data or len(data) == 0:
                logger.warning(f"Realtor API: No data found")
                return {'value': 'No data found', 'rent': 'N/A'}
            
            # Parse the response
            property_data = data[0] if isinstance(data, list) else data
            logger.info(f"Realtor API: Successfully got property data")
            return {
                'value': property_data.get('price', property_data.get('list_price', property_data.get('estimate', 'N/A'))),
                'rent': property_data.get('rent_estimate', property_data.get('rentEstimate', 'N/A')),
                'beds': property_data.get('beds', property_data.get('bedrooms', 'N/A')),
                'baths': property_data.get('baths', property_data.get('bathrooms', 'N/A')),
                'sqft': property_data.get('sqft', property_data.get('square_feet', 'N/A')),
                'year': property_data.get('year_built', property_data.get('yearBuilt', 'N/A')),
                'taxes': property_data.get('tax_amount', property_data.get('taxes', 'N/A')),
                'last_sold': property_data.get('last_sold_date', property_data.get('sold_date', 'N/A')),
                'images': property_data.get('photos', property_data.get('images', []))[:5]
            }
                
        except Exception as e:
            logger.error(f"Bright Data Realtor scraper error: {e}")
            return {'value': 'Failed', 'rent': 'Failed'}

class CompsGrabberAgent:
    def __init__(self, proxy, cert_path=None, ignore_https_errors=False):
        self.proxy = proxy
        self.cert_path = cert_path
        self.ignore_https_errors = ignore_https_errors

    async def fetch_redfin_comps(self, page, address_dict):
        """Fetch comparable properties from Redfin"""
        try:
            city = address_dict['city'].replace(' ', '-').lower()
            state = address_dict['state'].upper()
            street = address_dict['street'].replace(' ', '+')
            
            # Use Redfin's sold properties search
            search_url = f"https://www.redfin.com/city/262/{state}/{city}/filter/address={street},sold-2y"
            await self._retry_operation(page.goto, search_url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(random.uniform(3, 7))
            
            # Get sold comps from the page
            comps = await page.evaluate('''
                () => {
                    const listings = document.querySelectorAll('.result-card, .listing-result, .soldResult');
                    return Array.from(listings).slice(0, 5).map(listing => {
                        const address = listing.querySelector('.address, .listing-address')?.innerText || 'N/A';
                        const price = listing.querySelector('.price, .sold-price')?.innerText || 'N/A';
                        const details = listing.querySelector('.bed-bath-sqft-data, .property-details')?.innerText || 'N/A';
                        const soldDate = listing.querySelector('.sold-date, .status-date')?.innerText || 'N/A';
                        return {
                            address: address,
                            sold_price: price,
                            details: details,
                            sold_date: soldDate
                        };
                    }).filter(comp => comp.address !== 'N/A');
                }
            ''')
            
            return comps
        except Exception as e:
            logger.error(f"Redfin comps fetch error: {e}")
            return []

    async def get_comps(self, address_dict):
        """Get comparable properties using browser automation"""
        if self.cert_path and os.path.exists(self.cert_path):
            os.environ['NODE_EXTRA_CA_CERTS'] = self.cert_path
        
        try:
            async with async_playwright() as p:
                browser_args = [
                    '--disable-http2',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled'
                ]
                
                if self.ignore_https_errors:
                    browser_args.extend([
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors'
                    ])
                
                browser = await p.chromium.launch(proxy=self.proxy, args=browser_args)
                context = await browser.new_context(
                    user_agent=random.choice(user_agents),
                    ignore_https_errors=self.ignore_https_errors,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                comps = await self.fetch_redfin_comps(page, address_dict)
                await browser.close()
                
                return comps
        except Exception as e:
            logger.error(f"CompsGrabber error: {e}")
            return []

def get_comps(address):
    # Placeholder for legacy compatibility
    logger.info(f"Comps API call placeholder for {address}")
    return {}

# CSS for better readability and font sizes
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Increase font sizes */
    .stMetric label {
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    
    .stMetric [data-testid="metric-container"] > div {
        font-size: 24px !important;
        font-weight: 700 !important;
    }
    
    /* Better table styling */
    .stDataFrame {
        font-size: 14px !important;
    }
    
    /* Subheader improvements */
    .stMarkdown h3 {
        font-size: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Success/Warning/Error message improvements */
    .stAlert {
        font-size: 16px !important;
        margin: 0.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main App
st.title("Property Analyzer")

with st.sidebar:
    st.header("Settings & Thresholds")
    st.subheader("🔒 Bright Data SSL Configuration")
    st.info("Required: Choose one of the SSL options below")
    
    ssl_option = st.radio(
        "SSL Configuration Method:",
        ["Load Bright Data Certificate", "Ignore HTTPS Errors"],
        index=0,  # Default to "Load Bright Data Certificate" now that it's working
        help="Bright Data SSL certificate is now properly configured with macOS Keychain trust."
    )
    
    if ssl_option == "Load Bright Data Certificate":
        default_cert_path = os.getenv("BRIGHT_DATA_CERT_PATH", "")
        cert_path = st.text_input(
            "Certificate Path", 
            value=default_cert_path, 
            help="Path to Bright Data SSL certificate file (loaded from .env)"
        )
        ignore_https = False
        st.success("✅ Using SSL Certificate with macOS Keychain trust - **Recommended for long-term stability**")
    else:
        cert_path = ""
        ignore_https = True
        st.warning("⚠️ Using ignore SSL errors mode - less secure fallback option")
    
    st.subheader("📊 Analysis Settings")
    roi_threshold = st.number_input("ROI Alert Threshold (%)", value=20.0)
    show_details = st.checkbox("Show More Details on Page", value=False)
    
    st.subheader("🌍 Proxy Targeting")
    st.info("Currently configured for US-based proxies")
    
    st.subheader("🔧 Scraping Method")
    scraping_method = st.radio(
        "Choose Data Collection Method:",
        ["Bright Data API Scrapers (Recommended)", "Browser Automation (Backup)"],
        index=0,
        help="API scrapers are faster, more reliable, and cost-effective for concept validation"
    )
    
    if scraping_method == "Bright Data API Scrapers (Recommended)":
        api_token = os.getenv("BRIGHT_DATA_API_TOKEN", "")
        if not api_token or api_token == "your_bright_data_api_token_here":
            st.warning("⚠️ Please add your Bright Data API token to the .env file")
            st.info("Add: BRIGHT_DATA_API_TOKEN=your_actual_token_here")
            st.info("Cost: ~$0.001 per property lookup")
        else:
            st.success("✅ Bright Data API configured - Fast & Reliable!")
            st.info("💰 Cost: ~$0.001 per property ($1 for 1000 properties)")
    else:
        st.info("Using browser automation - slower but uses existing proxy setup")

address = st.text_input("Enter Property Address (e.g., 1841 Marks Ave, Akron, OH 44305)")
st.session_state['address'] = address  # For comps call

if st.button("Analyze"):
    if not address or len(address.strip()) < 10:
        st.error("Please enter a valid address with street, city, state, and ZIP code.")
    else:
        normalizer = NormalizerAgent()
        address_dict = normalizer.normalize(address)
        if not address_dict:
            st.error("Invalid address format. Please use format: Street Address, City, State ZIP")
        else:
            # Choose data collection method
            if scraping_method == "Bright Data API Scrapers (Recommended)":
                # Use Bright Data API scrapers
                api_token = os.getenv("BRIGHT_DATA_API_TOKEN", "")
                if not api_token or api_token == "your_bright_data_api_token_here":
                    st.error("❌ Bright Data API token not configured. Please add it to your .env file.")
                    st.stop()
                
                st.info("🚀 Using Bright Data API Scrapers - Fast & Reliable!")
                scraper = BrightDataScraperAgent(api_token)
                
                # Get data from both Zillow and Realtor APIs
                with st.spinner("Fetching property data from Zillow API..."):
                    zillow_data = scraper.scrape_zillow(address_dict)
                
                # Note: Switched to browser automation for Realtor (API was international only)
                realtor_data = {'value': 'Using Browser', 'rent': 'N/A', 'beds': 'N/A', 'baths': 'N/A', 'sqft': 'N/A', 'year': 'N/A', 'taxes': 'N/A', 'last_sold': 'N/A'}
                
                # Get additional data sources with error handling
                with st.spinner("Fetching data from additional sources..."):
                    # Add fallback browser automation for Redfin and Homes if APIs not available
                    try:
                        proxy = {
                            "server": f"http://{proxy_server}",
                            "username": proxy_username,
                            "password": proxy_password
                        }
                        fetcher = SiteFetcherAgent(proxy, cert_path if cert_path else None, ignore_https)
                        browser_data = asyncio.run(fetcher.fetch_all(address_dict))
                        realtor_data = browser_data.get('realtor', {'value': 'Browser Failed', 'rent': 'N/A'})  # Override placeholder
                        redfin_data = browser_data.get('redfin', {'value': 'N/A', 'rent': 'N/A'})
                        homes_data = browser_data.get('homes', {'value': 'N/A', 'rent': 'N/A'})
                        movoto_data = browser_data.get('movoto', {'value': 'N/A', 'rent': 'N/A'})
                    except Exception as e:
                        st.warning(f"⚠️ Browser automation error: {str(e)} - using API data only")
                        realtor_data = {'value': 'Browser Failed', 'rent': 'N/A'}
                        redfin_data = {'value': 'N/A', 'rent': 'N/A'}
                        homes_data = {'value': 'N/A', 'rent': 'N/A'}
                        movoto_data = {'value': 'N/A', 'rent': 'N/A'}
                
                # Format data for existing aggregator - all 5 sources
                data = {
                    'zillow': zillow_data,
                    'realtor': realtor_data,
                    'redfin': redfin_data,
                    'homes': homes_data,
                    'movoto': movoto_data
                }
                
            else:
                # Use traditional browser automation
                st.info("🔄 Using Browser Automation - This may take longer...")
                proxy = {
                    "server": f"http://{proxy_server}",
                    "username": proxy_username,
                    "password": proxy_password
                }
                fetcher = SiteFetcherAgent(proxy, cert_path if cert_path else None, ignore_https)
                data = asyncio.run(fetcher.fetch_all(address_dict))
            
            aggregator = AggregatorAgent()
            aggregated, site_data = aggregator.aggregate(data)

            # Settings defaults
            settings = {
                'desired_profit': 20000,
                'desired_roi': 20,
                'acquisition': 1.5,
                'brokerage': 3,
                'sales_closing': 1.5,
                'taxes': 1.2,
                'insurance': 0.5,
                'vacancy': 5,
                'maintenance': 10,
                'management': 8,
                'bad_debt': 2,
                'leasing_fee': 500,
                'turnover': 1000,
                'utilities': 100,
                'cdd': 0,
                'other_fee': 0,
                'ltv': 80,
                'interest': 5.5,
                'amortization': 30,
                'arm_length': 5,
                'adjustable_rate': 1,
                'hold_days_base': 60
            }

            # User inputs
            with st.expander("Analysis Inputs"):
                purchase = st.number_input("Purchase Price", value=100000.0)
                reno = st.number_input("Reno Cost", value=20000.0)
                hold_months = st.number_input("Months Held", value=12)

            user_inputs = {'purchase': purchase, 'reno': reno, 'hold_months': hold_months}

            analyzer = AnalyzerAgent(settings)
            metrics = analyzer.analyze(aggregated, user_inputs)

            tab1, tab2 = st.tabs(["Summary", "Details"])
            with tab1:
                renderer = OutputRendererAgent()
                renderer.render_summary(aggregated, metrics)
            with tab2:
                renderer.render_details(aggregated, site_data, aggregated.get('images', []), metrics)

            notifier = CRMNotifierAgent()
            notifier.notify(metrics, roi_threshold)