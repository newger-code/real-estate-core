#!/usr/bin/env python3
"""
Enhanced Realtor.com Scraper with Advanced Anti-Bot Strategies
Handles heavy blocking with stealth browser techniques
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import re

try:
    from pyppeteer import launch
    from pyppeteer_stealth import stealth
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "pyppeteer", "pyppeteer-stealth"], check=True)
    from pyppeteer import launch
    from pyppeteer_stealth import stealth

class RealtorScraper:
    def __init__(self, proxy_ip: str = "73.32.221.152", proxy_port: str = "22225"):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.base_url = "https://www.realtor.com"
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"realtor_scraper_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def create_stealth_browser(self):
        """Create a stealth browser instance with proxy"""
        self.logger.info("Launching stealth browser with proxy...")
        
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
            f'--proxy-server={self.proxy_ip}:{self.proxy_port}',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        browser = await launch(
            headless=True,
            args=browser_args,
            ignoreHTTPSErrors=True,
            slowMo=random.randint(50, 150)
        )
        
        page = await browser.newPage()
        await stealth(page)
        
        # Set additional headers and viewport
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        await page.setViewport({'width': 1366, 'height': 768})
        
        # Set extra headers
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return browser, page
        
    def format_address_for_url(self, address: str) -> str:
        """Format address for Realtor.com URL structure"""
        # Parse address components
        parts = address.replace(',', '').split()
        
        # Extract components
        street_num = parts[0] if parts else ""
        street_name = " ".join(parts[1:-3]) if len(parts) > 3 else ""
        city = parts[-3] if len(parts) > 2 else ""
        state = parts[-2] if len(parts) > 1 else ""
        zip_code = parts[-1] if parts else ""
        
        # Format for URL: street-name_city_state_zipcode
        street_formatted = street_name.replace(" ", "-")
        url_path = f"{street_num}-{street_formatted}_{city}_{state}_{zip_code}"
        
        return f"{self.base_url}/realestateandhomes-detail/{url_path}"
        
    async def human_like_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """Add human-like delays"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
        
    async def extract_property_data(self, page) -> Dict[str, Any]:
        """Extract property data from the page"""
        self.logger.info("Extracting property data...")
        
        property_data = {
            'source': 'realtor.com',
            'scraped_at': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # Wait for page to load completely
            await page.waitForSelector('body', timeout=30000)
            await self.human_like_delay(2000, 4000)
            
            # Extract basic property info
            try:
                # Property address
                address_selector = 'h1[data-testid="property-address"], .address-container h1, [data-testid="property-street-address"]'
                address = await page.evaluate(f'''() => {{
                    const elem = document.querySelector('{address_selector}');
                    return elem ? elem.textContent.trim() : null;
                }}''')
                if address:
                    property_data['address'] = address
                    
            except Exception as e:
                self.logger.warning(f"Could not extract address: {e}")
                
            # Extract price
            try:
                price_selector = '[data-testid="property-price"], .price, .listing-price'
                price = await page.evaluate(f'''() => {{
                    const elem = document.querySelector('{price_selector}');
                    return elem ? elem.textContent.trim() : null;
                }}''')
                if price:
                    property_data['price'] = price
                    
            except Exception as e:
                self.logger.warning(f"Could not extract price: {e}")
                
            # Extract AVM/Estimate (Realtor.com's RentSpree estimate)
            try:
                avm_selectors = [
                    '[data-testid="avm-value"]',
                    '.avm-value',
                    '.property-estimate',
                    '.estimate-value',
                    '[data-testid="property-estimate"]'
                ]
                
                for selector in avm_selectors:
                    avm = await page.evaluate(f'''() => {{
                        const elem = document.querySelector('{selector}');
                        return elem ? elem.textContent.trim() : null;
                    }}''')
                    if avm:
                        property_data['avm_estimate'] = avm
                        break
                        
            except Exception as e:
                self.logger.warning(f"Could not extract AVM: {e}")
                
            # Extract property details
            try:
                details = await page.evaluate('''() => {
                    const details = {};
                    
                    // Beds, baths, sqft
                    const bedSelector = '[data-testid="property-beds"], .beds';
                    const bathSelector = '[data-testid="property-baths"], .baths';
                    const sqftSelector = '[data-testid="property-sqft"], .sqft';
                    
                    const bedElem = document.querySelector(bedSelector);
                    if (bedElem) details.beds = bedElem.textContent.trim();
                    
                    const bathElem = document.querySelector(bathSelector);
                    if (bathElem) details.baths = bathElem.textContent.trim();
                    
                    const sqftElem = document.querySelector(sqftSelector);
                    if (sqftElem) details.sqft = sqftElem.textContent.trim();
                    
                    return details;
                }''')
                
                if details:
                    property_data.update(details)
                    
            except Exception as e:
                self.logger.warning(f"Could not extract property details: {e}")
                
            # Check if we got meaningful data
            if any(key in property_data for key in ['address', 'price', 'avm_estimate']):
                property_data['success'] = True
                self.logger.info("Successfully extracted property data")
            else:
                self.logger.warning("No meaningful property data extracted")
                
        except Exception as e:
            self.logger.error(f"Error extracting property data: {e}")
            
        return property_data
        
    async def scrape_property(self, address: str) -> Dict[str, Any]:
        """Scrape a single property from Realtor.com"""
        self.logger.info(f"Starting scrape for address: {address}")
        
        browser = None
        try:
            # Create stealth browser
            browser, page = await self.create_stealth_browser()
            
            # Format URL
            property_url = self.format_address_for_url(address)
            self.logger.info(f"Navigating to: {property_url}")
            
            # Navigate to property page
            response = await page.goto(property_url, {
                'waitUntil': 'networkidle2',
                'timeout': 60000
            })
            
            if response.status != 200:
                self.logger.error(f"HTTP {response.status} received")
                return {'success': False, 'error': f'HTTP {response.status}'}
                
            await self.human_like_delay(3000, 5000)
            
            # Check for blocking/captcha
            page_content = await page.content()
            if any(block_indicator in page_content.lower() for block_indicator in 
                   ['blocked', 'captcha', 'access denied', 'bot detected']):
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
    scraper = RealtorScraper()
    
    test_addresses = [
        "1841 Marks Ave, Akron, OH 44305",
        "1754 Hampton Rd, Akron, OH 44305"
    ]
    
    results = []
    for address in test_addresses:
        print(f"\n{'='*60}")
        print(f"Testing: {address}")
        print('='*60)
        
        result = scraper.scrape_property_sync(address)
        results.append(result)
        
        print(json.dumps(result, indent=2))
        
        # Delay between requests
        time.sleep(random.randint(5, 10))
        
    # Save results
    output_file = f"realtor_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nResults saved to: {output_file}")
    return results

if __name__ == "__main__":
    main()
