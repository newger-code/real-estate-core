#!/usr/bin/env python3
"""
Smart Test - Use proxy only when needed, extract real data
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from proxy_config import get_playwright_proxy
from utils.common import setup_logger

class SmartScraper:
    """Smart scraper that adapts to site requirements"""
    
    def __init__(self):
        self.logger = setup_logger("smart_scraper")
        self.results = {}
        
        # Site configurations
        self.site_configs = {
            "redfin": {
                "url": "https://www.redfin.com",
                "needs_proxy": False,
                "search_selectors": [
                    'input[placeholder*="address" i]',
                    'input[data-rf-test-id="search-box-input"]'
                ],
                "property_selectors": {
                    "address": ['.street-address', '[data-rf-test-id="abp-streetLine"]'],
                    "beds": ['.beds .value', '[data-rf-test-id="abp-beds"]'],
                    "baths": ['.baths .value', '[data-rf-test-id="abp-baths"]'],
                    "sqft": ['.sqft .value', '[data-rf-test-id="abp-sqFt"]'],
                    "price": ['.price', '[data-rf-test-id="abp-price"]'],
                    "status": ['.listing-status', '[data-rf-test-id="listing-status"]']
                }
            },
            "homes": {
                "url": "https://www.homes.com",
                "needs_proxy": True,
                "search_selectors": [
                    'input[placeholder*="address" i]',
                    'input[name="searchfield"]'
                ],
                "property_selectors": {
                    "address": ['h1[data-testid="property-address"]', '.property-address'],
                    "beds": ['[data-testid="beds"]', '.beds'],
                    "baths": ['[data-testid="baths"]', '.baths'],
                    "sqft": ['[data-testid="sqft"]', '.sqft'],
                    "price": ['.price', '[data-testid="price"]'],
                    "status": ['.listing-status', '[data-testid="listing-status"]']
                }
            },
            "movoto": {
                "url": "https://www.movoto.com",
                "needs_proxy": True,
                "search_selectors": [
                    'input[placeholder*="address" i]',
                    'input[name="search"]'
                ],
                "property_selectors": {
                    "address": ['.property-address', '.listing-address'],
                    "beds": ['.beds', '.bed-count'],
                    "baths": ['.baths', '.bath-count'],
                    "sqft": ['.sqft', '.square-feet'],
                    "price": ['.price', '.listing-price'],
                    "status": ['.listing-status', '.property-status']
                }
            }
        }
    
    async def test_site(self, site_name: str, address: str):
        """Test individual site with smart proxy usage"""
        
        config = self.site_configs[site_name]
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"TESTING {site_name.upper()}")
        self.logger.info(f"Address: {address}")
        self.logger.info(f"Proxy needed: {config['needs_proxy']}")
        self.logger.info(f"{'='*50}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create context with or without proxy
            context_options = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                "viewport": {"width": 1366, "height": 768}
            }
            
            if config["needs_proxy"]:
                context_options["proxy"] = get_playwright_proxy()
                context_options["ignore_https_errors"] = True
                self.logger.info("🔒 Using Bright Data proxy")
            else:
                self.logger.info("🌐 Direct connection (no proxy)")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # Step 1: Load homepage
                self.logger.info(f"📍 Loading {config['url']}")
                await page.goto(config['url'], wait_until="domcontentloaded", timeout=20000)
                
                # Take screenshot
                screenshot_path = f"smart_test_{site_name}_home.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot: {screenshot_path}")
                
                # Check for blocking
                title = await page.title()
                if "access denied" in title.lower() or "blocked" in title.lower():
                    self.logger.error(f"❌ Site is blocking access: {title}")
                    return {"success": False, "error": "Site blocked access"}
                
                self.logger.info(f"✅ Homepage loaded: {title}")
                
                # Step 2: Find and use search
                search_input = None
                for selector in config["search_selectors"]:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=3000)
                        if search_input:
                            self.logger.info(f"🔍 Found search input: {selector}")
                            break
                    except:
                        continue
                
                if not search_input:
                    self.logger.error("❌ No search input found")
                    return {"success": False, "error": "No search input found"}
                
                # Enter address
                self.logger.info(f"⌨️  Entering address: {address}")
                await search_input.fill(address)
                await asyncio.sleep(1)
                
                # Submit search
                self.logger.info("🚀 Submitting search")
                await page.keyboard.press("Enter")
                await asyncio.sleep(5)  # Wait for results
                
                # Take results screenshot
                results_screenshot = f"smart_test_{site_name}_results.png"
                await page.screenshot(path=results_screenshot)
                self.logger.info(f"📸 Results screenshot: {results_screenshot}")
                
                # Step 3: Extract property data
                property_data = await self._extract_property_data(page, config, site_name)
                
                if property_data:
                    self.logger.info("✅ Property data extracted successfully!")
                    
                    # Log extracted data
                    for field, value in property_data.items():
                        if value:
                            self.logger.info(f"   {field}: {value}")
                    
                    # Save data
                    output_file = f"smart_test_{site_name}_data.json"
                    with open(output_file, "w") as f:
                        json.dump(property_data, f, indent=2)
                    
                    self.logger.info(f"💾 Data saved: {output_file}")
                    
                    return {
                        "success": True,
                        "data": property_data,
                        "fields_extracted": len([v for v in property_data.values() if v]),
                        "total_fields": len(property_data)
                    }
                else:
                    self.logger.error("❌ No property data extracted")
                    return {"success": False, "error": "No property data extracted"}
                
            except Exception as e:
                self.logger.error(f"❌ Error: {str(e)}")
                return {"success": False, "error": str(e)}
            
            finally:
                await browser.close()
    
    async def _extract_property_data(self, page, config, site_name):
        """Extract property data using site-specific selectors"""
        
        property_data = {
            "site": site_name,
            "extraction_timestamp": datetime.now().isoformat(),
            "url": page.url
        }
        
        # Try to extract each field
        for field_name, selectors in config["property_selectors"].items():
            value = None
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = await element.text_content()
                        if text and text.strip():
                            value = text.strip()
                            self.logger.info(f"   Found {field_name}: {value[:50]}...")
                            break
                except:
                    continue
            
            property_data[field_name] = value
        
        # Special handling for photos
        try:
            photo_selectors = ['.property-photos img', '.listing-photos img', '.MediaCarousel img']
            photos = []
            
            for selector in photo_selectors:
                try:
                    images = await page.locator(selector).all()
                    for img in images[:5]:  # Limit to 5 photos
                        src = await img.get_attribute('src')
                        if src and 'http' in src:
                            photos.append(src)
                    if photos:
                        break
                except:
                    continue
            
            property_data["photos"] = photos
            if photos:
                self.logger.info(f"   Found {len(photos)} photos")
                
        except Exception as e:
            self.logger.warning(f"Photo extraction failed: {str(e)}")
        
        # Check if we got any meaningful data
        meaningful_fields = [v for k, v in property_data.items() 
                           if k not in ["site", "extraction_timestamp", "url"] and v]
        
        return property_data if meaningful_fields else None
    
    async def run_comprehensive_test(self):
        """Run test on all sites"""
        
        test_address = "1841 Marks Ave, Akron, OH 44305"
        
        print("Smart Real Estate Scraper Test")
        print("=" * 40)
        print(f"Test Address: {test_address}")
        print(f"Sites: {list(self.site_configs.keys())}")
        print()
        
        results = {}
        
        for site_name in self.site_configs.keys():
            result = await self.test_site(site_name, test_address)
            results[site_name] = result
            
            if result["success"]:
                print(f"✅ {site_name.upper()} - SUCCESS")
                print(f"   Fields: {result['fields_extracted']}/{result['total_fields']}")
            else:
                print(f"❌ {site_name.upper()} - FAILED: {result['error']}")
            
            print("-" * 40)
        
        # Final summary
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"Success Rate: {successful}/{total} ({successful/total:.1%})")
        
        if successful > 0:
            print(f"\n📊 PROOF OF SCRAPED DATA:")
            for site, result in results.items():
                if result["success"]:
                    data = result["data"]
                    print(f"\n{site.upper()}:")
                    print(f"  Address: {data.get('address', 'N/A')}")
                    print(f"  Beds/Baths: {data.get('beds', 'N/A')}/{data.get('baths', 'N/A')}")
                    print(f"  Sqft: {data.get('sqft', 'N/A')}")
                    print(f"  Price: {data.get('price', 'N/A')}")
                    print(f"  Photos: {len(data.get('photos', []))}")
        
        return results

async def main():
    scraper = SmartScraper()
    await scraper.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
