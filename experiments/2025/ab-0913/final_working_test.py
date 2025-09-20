#!/usr/bin/env python3
"""
Final Working Test - Demonstrate actual data extraction with proof
Focus on Redfin (works without proxy) and show complete system functionality
"""

import asyncio
import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from proxy_config import proxy_manager
from utils.common import setup_logger

class FinalWorkingScraper:
    """Final working scraper with proven data extraction"""
    
    def __init__(self):
        self.logger = setup_logger("final_working_scraper")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        self.output_dir = Path("final_test_results") / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Output directory: {self.output_dir}")
    
    async def test_redfin_complete(self, address: str):
        """Complete Redfin test with actual data extraction"""
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"FINAL WORKING TEST - REDFIN")
        self.logger.info(f"Address: {address}")
        self.logger.info(f"{'='*60}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                viewport={"width": 1366, "height": 768}
            )
            
            page = await context.new_page()
            
            try:
                # Step 1: Load Redfin homepage
                self.logger.info("📍 Step 1: Loading Redfin homepage")
                await page.goto("https://www.redfin.com", wait_until="domcontentloaded", timeout=15000)
                
                screenshot_path = self.output_dir / "step1_homepage.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Homepage screenshot: {screenshot_path}")
                
                # Step 2: Find and use search
                self.logger.info("🔍 Step 2: Finding search input")
                search_input = await page.wait_for_selector('input[placeholder*="address" i]', timeout=10000)
                
                if not search_input:
                    raise Exception("Search input not found")
                
                self.logger.info("✅ Search input found")
                
                # Step 3: Enter address
                self.logger.info(f"⌨️  Step 3: Entering address: {address}")
                await search_input.fill(address)
                await asyncio.sleep(2)
                
                # Step 4: Submit search
                self.logger.info("🚀 Step 4: Submitting search")
                await page.keyboard.press("Enter")
                await asyncio.sleep(8)  # Wait longer for results
                
                screenshot_path = self.output_dir / "step4_search_results.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Search results screenshot: {screenshot_path}")
                
                # Step 5: Check if we need to click on a result
                current_url = page.url
                self.logger.info(f"Current URL: {current_url}")
                
                # Look for property results to click
                if "/home/" not in current_url:
                    self.logger.info("🎯 Step 5: Looking for property results to click")
                    
                    # Try different result selectors
                    result_selectors = [
                        '.SearchResultsList .result',
                        '.search-result-item',
                        '[data-rf-test-id="search-result"]',
                        '.HomeCard',
                        '.SearchResult'
                    ]
                    
                    clicked = False
                    for selector in result_selectors:
                        try:
                            results = await page.locator(selector).count()
                            if results > 0:
                                self.logger.info(f"Found {results} results with selector: {selector}")
                                await page.locator(selector).first.click()
                                await asyncio.sleep(5)
                                clicked = True
                                break
                        except Exception as e:
                            self.logger.warning(f"Selector {selector} failed: {str(e)}")
                            continue
                    
                    if not clicked:
                        self.logger.warning("No clickable results found, trying to extract from current page")
                
                # Step 6: Extract property data
                self.logger.info("📊 Step 6: Extracting property data")
                
                screenshot_path = self.output_dir / "step6_property_page.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Property page screenshot: {screenshot_path}")
                
                property_data = await self._extract_redfin_data(page)
                
                if property_data:
                    self.logger.info("✅ SUCCESS! Property data extracted:")
                    
                    # Log extracted data
                    for field, value in property_data.items():
                        if value and field not in ["extraction_timestamp", "photos"]:
                            self.logger.info(f"   {field}: {value}")
                    
                    if property_data.get("photos"):
                        self.logger.info(f"   photos: {len(property_data['photos'])} images found")
                    
                    # Step 7: Save data in multiple formats
                    await self._save_extracted_data(property_data, address)
                    
                    return {
                        "success": True,
                        "data": property_data,
                        "fields_extracted": len([v for v in property_data.values() if v]),
                        "total_fields": len(property_data)
                    }
                else:
                    self.logger.error("❌ No property data could be extracted")
                    return {"success": False, "error": "No data extracted"}
                
            except Exception as e:
                self.logger.error(f"❌ Error: {str(e)}")
                return {"success": False, "error": str(e)}
            
            finally:
                await browser.close()
    
    async def _extract_redfin_data(self, page):
        """Extract data from Redfin property page"""
        
        property_data = {
            "source_site": "redfin",
            "extraction_timestamp": datetime.now().isoformat(),
            "property_url": page.url
        }
        
        # Define extraction rules
        extraction_rules = {
            "address": [
                '.street-address',
                '[data-rf-test-id="abp-streetLine"]',
                'h1.street-address',
                '.address'
            ],
            "beds": [
                '.beds .value',
                '[data-rf-test-id="abp-beds"]',
                '.bed-bath .beds',
                '.stats-bed'
            ],
            "baths": [
                '.baths .value', 
                '[data-rf-test-id="abp-baths"]',
                '.bed-bath .baths',
                '.stats-bath'
            ],
            "sqft": [
                '.sqft .value',
                '[data-rf-test-id="abp-sqFt"]',
                '.stats-sqft',
                '.square-feet'
            ],
            "year_built": [
                '[data-rf-test-id="abp-yearBuilt"]',
                '.year-built .value',
                '.built-year'
            ],
            "price": [
                '.price',
                '.listing-price',
                '[data-rf-test-id="abp-price"]',
                '.home-main-stats-variant-value'
            ],
            "status": [
                '.listing-status',
                '.property-status',
                '[data-rf-test-id="listing-status"]'
            ],
            "lot_size": [
                '[data-rf-test-id="abp-lotSize"]',
                '.lot-size .value',
                '.lot-sqft'
            ]
        }
        
        # Extract each field
        for field_name, selectors in extraction_rules.items():
            value = None
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = await element.text_content()
                        if text and text.strip():
                            value = text.strip()
                            self.logger.info(f"   ✓ {field_name}: {value}")
                            break
                except:
                    continue
            
            if not value:
                self.logger.warning(f"   ✗ {field_name}: Not found")
            
            property_data[field_name] = value
        
        # Extract photos
        try:
            photo_selectors = [
                '.MediaCarousel img',
                '.photo-carousel img',
                '.property-photos img',
                '.listing-photos img'
            ]
            
            photos = []
            for selector in photo_selectors:
                try:
                    images = await page.locator(selector).all()
                    for img in images[:10]:  # Limit to 10 photos
                        src = await img.get_attribute('src')
                        if src and ('http' in src or src.startswith('//')):
                            if src.startswith('//'):
                                src = 'https:' + src
                            photos.append(src)
                    if photos:
                        break
                except:
                    continue
            
            property_data["photos"] = photos
            if photos:
                self.logger.info(f"   ✓ photos: {len(photos)} images")
            else:
                self.logger.warning("   ✗ photos: Not found")
                
        except Exception as e:
            self.logger.warning(f"Photo extraction failed: {str(e)}")
            property_data["photos"] = []
        
        # Try to detect status from page content if not found
        if not property_data.get("status"):
            try:
                page_content = await page.text_content("body")
                page_content_lower = page_content.lower()
                
                status_indicators = [
                    ("for sale", "FOR SALE"),
                    ("active", "ACTIVE"),
                    ("pending", "PENDING"),
                    ("sold", "SOLD"),
                    ("off market", "OFF MARKET")
                ]
                
                for indicator, status in status_indicators:
                    if indicator in page_content_lower:
                        property_data["status"] = status
                        self.logger.info(f"   ✓ status (detected): {status}")
                        break
                        
            except Exception as e:
                self.logger.warning(f"Status detection failed: {str(e)}")
        
        # Check if we got meaningful data
        meaningful_fields = [v for k, v in property_data.items() 
                           if k not in ["source_site", "extraction_timestamp", "property_url", "photos"] and v]
        
        return property_data if meaningful_fields else None
    
    async def _save_extracted_data(self, property_data, address):
        """Save extracted data in multiple formats"""
        
        # Clean address for filename
        clean_address = address.replace(",", "_").replace(" ", "_").replace("/", "_")
        base_filename = f"redfin_{clean_address}_{self.timestamp}"
        
        # Save JSON
        json_path = self.output_dir / f"{base_filename}.json"
        with open(json_path, "w") as f:
            json.dump(property_data, f, indent=2)
        self.logger.info(f"💾 JSON saved: {json_path}")
        
        # Save CSV
        csv_path = self.output_dir / f"{base_filename}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write headers
            headers = list(property_data.keys())
            writer.writerow(headers)
            
            # Write data (convert lists to strings)
            values = []
            for header in headers:
                value = property_data.get(header, "")
                if isinstance(value, list):
                    value = "; ".join(str(v) for v in value)
                values.append(str(value))
            writer.writerow(values)
        
        self.logger.info(f"💾 CSV saved: {csv_path}")
        
        # Create proof summary
        proof_path = self.output_dir / "PROOF_OF_SCRAPED_DATA.txt"
        with open(proof_path, "w") as f:
            f.write("REAL ESTATE SCRAPER - PROOF OF ACTUAL DATA EXTRACTION\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Site: Redfin.com\n")
            f.write(f"Test Address: {address}\n")
            f.write(f"Proxy Used: No (Direct connection)\n\n")
            
            f.write("EXTRACTED DATA:\n")
            f.write("-" * 20 + "\n")
            
            for field, value in property_data.items():
                if field not in ["photos"] and value:
                    f.write(f"{field}: {value}\n")
            
            if property_data.get("photos"):
                f.write(f"photos: {len(property_data['photos'])} images\n")
            
            f.write(f"\nFields Extracted: {len([v for v in property_data.values() if v])}\n")
            f.write(f"Total Fields: {len(property_data)}\n")
            f.write(f"Completeness: {len([v for v in property_data.values() if v])/len(property_data):.1%}\n")
        
        self.logger.info(f"🎯 Proof file saved: {proof_path}")
    
    async def test_proxy_connectivity(self):
        """Test proxy connectivity for completeness"""
        
        self.logger.info("\n" + "="*40)
        self.logger.info("PROXY CONNECTIVITY TEST")
        self.logger.info("="*40)
        
        try:
            success, message, ip = await proxy_manager.test_proxy_connectivity()
            
            proxy_result = {
                "success": success,
                "message": message,
                "external_ip": ip,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                self.logger.info(f"✅ Bright Data proxy working")
                self.logger.info(f"   External IP: {ip}")
            else:
                self.logger.error(f"❌ Proxy test failed: {message}")
            
            # Save proxy test result
            proxy_path = self.output_dir / "proxy_test_result.json"
            with open(proxy_path, "w") as f:
                json.dump(proxy_result, f, indent=2)
            
            return proxy_result
            
        except Exception as e:
            self.logger.error(f"❌ Proxy test error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_complete_test(self):
        """Run complete test with both addresses"""
        
        test_addresses = [
            "1841 Marks Ave, Akron, OH 44305",
            "1754 Hampton Rd, Akron, OH 44305"
        ]
        
        print("Final Working Real Estate Scraper Test")
        print("=" * 50)
        print(f"Output Directory: {self.output_dir}")
        print(f"Test Addresses: {test_addresses}")
        print()
        
        # Test proxy connectivity
        await self.test_proxy_connectivity()
        
        results = {}
        
        # Test each address
        for i, address in enumerate(test_addresses, 1):
            print(f"\n{'='*50}")
            print(f"TESTING ADDRESS {i}: {address}")
            print(f"{'='*50}")
            
            result = await self.test_redfin_complete(address)
            results[address] = result
            
            if result["success"]:
                print(f"✅ SUCCESS - Data extracted!")
                print(f"   Fields: {result['fields_extracted']}/{result['total_fields']}")
                print(f"   Completeness: {result['fields_extracted']/result['total_fields']:.1%}")
                
                # Show key data
                data = result["data"]
                if data.get("address"):
                    print(f"   Address: {data['address']}")
                if data.get("beds") and data.get("baths"):
                    print(f"   Beds/Baths: {data['beds']}/{data['baths']}")
                if data.get("sqft"):
                    print(f"   Square Feet: {data['sqft']}")
                if data.get("price"):
                    print(f"   Price: {data['price']}")
            else:
                print(f"❌ FAILED: {result['error']}")
        
        # Final summary
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        print(f"\n{'='*50}")
        print("FINAL SUMMARY")
        print(f"{'='*50}")
        print(f"Addresses Tested: {total}")
        print(f"Successful Extractions: {successful}")
        print(f"Success Rate: {successful/total:.1%}")
        print(f"Output Directory: {self.output_dir}")
        
        if successful > 0:
            print(f"\n🎯 PROOF OF ACTUAL SCRAPED DATA:")
            print(f"   Check files in: {self.output_dir}")
            print(f"   - JSON files with complete data")
            print(f"   - CSV files for analysis")
            print(f"   - Screenshots showing process")
            print(f"   - PROOF_OF_SCRAPED_DATA.txt summary")
        
        return results

async def main():
    scraper = FinalWorkingScraper()
    await scraper.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())
