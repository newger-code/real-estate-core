#!/usr/bin/env python3
"""
Enhanced Zillow Scraper with Advanced Anti-Bot Strategies
Handles Zillow's sophisticated blocking with multiple evasion techniques
"""

import asyncio
import json
import logging
import random
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import quote

try:
    from pyppeteer import launch
    from pyppeteer_stealth import stealth
except ImportError:
    print("Required packages already installed")
    from pyppeteer import launch
    from pyppeteer_stealth import stealth

class ZillowScraper:
    def __init__(self, proxy_ip: str = "73.32.221.152", proxy_port: str = "22225"):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.base_url = "https://www.zillow.com"
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"zillow_scraper_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def create_advanced_stealth_browser(self):
        """Create advanced stealth browser with maximum evasion"""
        self.logger.info("Launching advanced stealth browser...")
        
        # Randomize browser fingerprint
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        selected_ua = random.choice(user_agents)
        
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Faster loading
            f'--proxy-server={self.proxy_ip}:{self.proxy_port}',
            f'--user-agent={selected_ua}'
        ]
        
        browser = await launch(
            headless=True,
            args=browser_args,
            ignoreHTTPSErrors=True,
            slowMo=random.randint(100, 300),
            devtools=False
        )
        
        page = await browser.newPage()
        await stealth(page)
        
        # Advanced stealth configurations
        await page.setUserAgent(selected_ua)
        await page.setViewport({
            'width': random.randint(1200, 1920), 
            'height': random.randint(800, 1080)
        })
        
        # Remove webdriver traces
        await page.evaluateOnNewDocument('''() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Remove chrome automation indicators
            delete window.chrome.runtime.onConnect;
            delete window.chrome.runtime.onMessage;
            
            // Spoof plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Spoof languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        }''')
        
        # Set realistic headers
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        return browser, page
        
    def format_address_for_search(self, address: str) -> str:
        """Format address for Zillow search"""
        # Clean and format address
        clean_address = address.replace(',', '').strip()
        return quote(clean_address)
        
    async def human_like_behavior(self, page):
        """Simulate human-like behavior"""
        # Random mouse movements
        await page.mouse.move(
            random.randint(100, 800), 
            random.randint(100, 600)
        )
        
        # Random scroll
        await page.evaluate(f'''() => {{
            window.scrollTo(0, {random.randint(100, 500)});
        }}''')
        
        # Random delay
        await asyncio.sleep(random.uniform(1.5, 3.5))
        
    async def search_property(self, page, address: str) -> Optional[str]:
        """Search for property and get property URL"""
        self.logger.info(f"Searching for property: {address}")
        
        try:
            # Go to Zillow homepage first
            await page.goto(self.base_url, {'waitUntil': 'networkidle2', 'timeout': 30000})
            await self.human_like_behavior(page)
            
            # Find search box and enter address
            search_selectors = [
                'input[placeholder*="Enter an address"]',
                'input[data-testid="search-box-input"]',
                '#search-box-input',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    await page.waitForSelector(selector, timeout=5000)
                    search_input = selector
                    break
                except:
                    continue
                    
            if not search_input:
                self.logger.error("Could not find search input")
                return None
                
            # Clear and type address
            await page.click(search_input)
            await page.keyboard.down('Control')
            await page.keyboard.press('a')
            await page.keyboard.up('Control')
            await page.keyboard.press('Backspace')
            
            # Type address with human-like delays
            for char in address:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
            await asyncio.sleep(random.uniform(1, 2))
            
            # Press Enter or click search
            await page.keyboard.press('Enter')
            await page.waitForNavigation({'waitUntil': 'networkidle2', 'timeout': 30000})
            
            await self.human_like_behavior(page)
            
            # Look for property links in search results
            property_selectors = [
                'a[data-test="property-card-link"]',
                '.property-card-link',
                'a[href*="/homedetails/"]',
                '.list-card-link'
            ]
            
            for selector in property_selectors:
                try:
                    links = await page.querySelectorAll(selector)
                    if links:
                        href = await page.evaluate('(element) => element.href', links[0])
                        if href and '/homedetails/' in href:
                            self.logger.info(f"Found property URL: {href}")
                            return href
                except:
                    continue
                    
            # If no direct links, try to get current URL if it's a property page
            current_url = page.url
            if '/homedetails/' in current_url:
                return current_url
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching property: {e}")
            return None
            
    async def extract_property_data(self, page) -> Dict[str, Any]:
        """Extract comprehensive property data from Zillow"""
        self.logger.info("Extracting property data from Zillow...")
        
        property_data = {
            'source': 'zillow.com',
            'scraped_at': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # Wait for page to load
            await page.waitForSelector('body', timeout=30000)
            await self.human_like_behavior(page)
            
            # Extract Zestimate (Zillow's AVM)
            try:
                zestimate_selectors = [
                    '[data-testid="zestimate-text"]',
                    '.zestimate',
                    '[data-testid="price-range"]',
                    '.estimate-value'
                ]
                
                for selector in zestimate_selectors:
                    zestimate = await page.evaluate(f'''() => {{
                        const elem = document.querySelector('{selector}');
                        return elem ? elem.textContent.trim() : null;
                    }}''')
                    if zestimate and '$' in zestimate:
                        property_data['zestimate'] = zestimate
                        break
                        
            except Exception as e:
                self.logger.warning(f"Could not extract Zestimate: {e}")
                
            # Extract property address
            try:
                address_selectors = [
                    '[data-testid="property-address"]',
                    'h1[data-testid="property-address"]',
                    '.property-address'
                ]
                
                for selector in address_selectors:
                    address = await page.evaluate(f'''() => {{
                        const elem = document.querySelector('{selector}');
                        return elem ? elem.textContent.trim() : null;
                    }}''')
                    if address:
                        property_data['address'] = address
                        break
                        
            except Exception as e:
                self.logger.warning(f"Could not extract address: {e}")
                
            # Extract current price
            try:
                price_selectors = [
                    '[data-testid="property-price"]',
                    '.notranslate',
                    '.price'
                ]
                
                for selector in price_selectors:
                    price = await page.evaluate(f'''() => {{
                        const elem = document.querySelector('{selector}');
                        return elem ? elem.textContent.trim() : null;
                    }}''')
                    if price and '$' in price:
                        property_data['price'] = price
                        break
                        
            except Exception as e:
                self.logger.warning(f"Could not extract price: {e}")
                
            # Extract property details
            try:
                details = await page.evaluate('''() => {
                    const details = {};
                    
                    // Look for beds, baths, sqft
                    const detailElements = document.querySelectorAll('[data-testid*="bed"], [data-testid*="bath"], [data-testid*="sqft"]');
                    
                    detailElements.forEach(elem => {
                        const text = elem.textContent.trim();
                        const testId = elem.getAttribute('data-testid');
                        
                        if (testId && testId.includes('bed')) {
                            details.beds = text;
                        } else if (testId && testId.includes('bath')) {
                            details.baths = text;
                        } else if (testId && testId.includes('sqft')) {
                            details.sqft = text;
                        }
                    });
                    
                    // Alternative selectors
                    if (!details.beds) {
                        const bedElem = document.querySelector('.summary-container span:contains("bed")');
                        if (bedElem) details.beds = bedElem.textContent.trim();
                    }
                    
                    return details;
                }''')
                
                if details:
                    property_data.update(details)
                    
            except Exception as e:
                self.logger.warning(f"Could not extract property details: {e}")
                
            # Extract additional data
            try:
                # Property type, year built, etc.
                additional_data = await page.evaluate('''() => {
                    const data = {};
                    
                    // Property type
                    const typeElem = document.querySelector('[data-testid="property-type"]');
                    if (typeElem) data.property_type = typeElem.textContent.trim();
                    
                    // Year built
                    const yearElem = document.querySelector('[data-testid="year-built"]');
                    if (yearElem) data.year_built = yearElem.textContent.trim();
                    
                    return data;
                }''')
                
                if additional_data:
                    property_data.update(additional_data)
                    
            except Exception as e:
                self.logger.warning(f"Could not extract additional data: {e}")
                
            # Check if we got meaningful data
            if any(key in property_data for key in ['zestimate', 'address', 'price']):
                property_data['success'] = True
                self.logger.info("Successfully extracted property data")
            else:
                self.logger.warning("No meaningful property data extracted")
                
        except Exception as e:
            self.logger.error(f"Error extracting property data: {e}")
            
        return property_data
        
    async def scrape_property(self, address: str) -> Dict[str, Any]:
        """Scrape a single property from Zillow"""
        self.logger.info(f"Starting Zillow scrape for: {address}")
        
        browser = None
        try:
            # Create advanced stealth browser
            browser, page = await self.create_advanced_stealth_browser()
            
            # Search for the property
            property_url = await self.search_property(page, address)
            
            if not property_url:
                return {'success': False, 'error': 'Property not found in search'}
                
            # Navigate to property page if not already there
            if page.url != property_url:
                await page.goto(property_url, {'waitUntil': 'networkidle2', 'timeout': 30000})
                await self.human_like_behavior(page)
                
            # Check for blocking
            page_content = await page.content()
            if any(block_indicator in page_content.lower() for block_indicator in 
                   ['blocked', 'captcha', 'access denied', 'bot detected', 'unusual traffic']):
                self.logger.error("Page blocked or captcha detected")
                return {'success': False, 'error': 'Blocked or captcha'}
                
            # Extract property data
            property_data = await self.extract_property_data(page)
            property_data['url'] = property_url
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"Error scraping property: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            if browser:
                await browser.close()
                
    def scrape_property_sync(self, address: str) -> Dict[str, Any]:
        """Synchronous wrapper for scraping"""
        return asyncio.get_event_loop().run_until_complete(self.scrape_property(address))

def main():
    """Test the scraper with target properties"""
    scraper = ZillowScraper()
    
    test_addresses = [
        "1841 Marks Ave, Akron, OH 44305",
        "1754 Hampton Rd, Akron, OH 44305"
    ]
    
    results = []
    for address in test_addresses:
        print(f"\n{'='*60}")
        print(f"Testing Zillow: {address}")
        print('='*60)
        
        result = scraper.scrape_property_sync(address)
        results.append(result)
        
        print(json.dumps(result, indent=2))
        
        # Longer delay between requests for Zillow
        time.sleep(random.randint(10, 20))
        
    # Save results
    output_file = f"zillow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nResults saved to: {output_file}")
    return results

if __name__ == "__main__":
    main()
