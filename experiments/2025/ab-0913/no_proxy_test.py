#!/usr/bin/env python3
"""
No Proxy Test - Test scraper logic without proxy first
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.common import setup_logger

async def test_site_without_proxy(site_url: str, site_name: str):
    """Test site access without proxy"""
    
    logger = setup_logger(f"no_proxy_test_{site_name}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            viewport={"width": 1366, "height": 768}
        )
        
        page = await context.new_page()
        
        try:
            logger.info(f"Loading {site_name}: {site_url}")
            
            # Navigate to site
            await page.goto(site_url, wait_until="domcontentloaded", timeout=15000)
            
            # Take screenshot
            screenshot_path = f"no_proxy_{site_name}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Get page info
            title = await page.title()
            current_url = page.url
            
            logger.info(f"✅ Successfully loaded {site_name}")
            logger.info(f"   Title: {title}")
            logger.info(f"   URL: {current_url}")
            
            # Look for search inputs
            search_selectors = [
                'input[placeholder*="address" i]',
                'input[placeholder*="Address"]',
                'input[type="search"]',
                'input[type="text"]',
                '#search',
                '.search-input',
                '[data-rf-test-id="search-box-input"]',  # Redfin specific
                'input[name="searchfield"]'  # Homes.com specific
            ]
            
            found_inputs = []
            for selector in search_selectors:
                try:
                    elements = await page.locator(selector).count()
                    if elements > 0:
                        # Get the actual placeholder text
                        first_element = page.locator(selector).first
                        placeholder = await first_element.get_attribute("placeholder")
                        found_inputs.append(f"{selector} - '{placeholder}' ({elements} elements)")
                except:
                    pass
            
            if found_inputs:
                logger.info("✅ Search inputs found:")
                for inp in found_inputs:
                    logger.info(f"   {inp}")
            else:
                logger.warning("❌ No search inputs found")
                
                # Try to find any input elements
                all_inputs = await page.locator("input").count()
                logger.info(f"Total input elements found: {all_inputs}")
                
                if all_inputs > 0:
                    for i in range(min(5, all_inputs)):  # Check first 5 inputs
                        input_elem = page.locator("input").nth(i)
                        input_type = await input_elem.get_attribute("type")
                        input_placeholder = await input_elem.get_attribute("placeholder")
                        input_name = await input_elem.get_attribute("name")
                        input_id = await input_elem.get_attribute("id")
                        
                        logger.info(f"   Input {i+1}: type='{input_type}', placeholder='{input_placeholder}', name='{input_name}', id='{input_id}'")
            
            # Test search functionality if we found inputs
            if found_inputs:
                logger.info("Testing search functionality...")
                
                # Try the first found input
                first_selector = found_inputs[0].split(" - ")[0]
                search_input = page.locator(first_selector).first
                
                test_address = "1841 Marks Ave, Akron, OH 44305"
                
                try:
                    await search_input.fill(test_address)
                    logger.info(f"✅ Successfully entered address: {test_address}")
                    
                    # Wait a moment
                    await asyncio.sleep(2)
                    
                    # Try to submit
                    await page.keyboard.press("Enter")
                    logger.info("✅ Submitted search")
                    
                    # Wait for results
                    await asyncio.sleep(5)
                    
                    # Take another screenshot
                    result_screenshot = f"no_proxy_{site_name}_results.png"
                    await page.screenshot(path=result_screenshot)
                    logger.info(f"Results screenshot: {result_screenshot}")
                    
                    # Check if we're on a property page or results page
                    current_url_after = page.url
                    logger.info(f"URL after search: {current_url_after}")
                    
                    if current_url != current_url_after:
                        logger.info("✅ URL changed - search appears to have worked")
                        
                        # Try to extract some basic data
                        page_text = await page.text_content("body")
                        
                        # Look for property indicators
                        property_indicators = ["bed", "bath", "sqft", "sq ft", "$", "for sale"]
                        found_indicators = [ind for ind in property_indicators if ind.lower() in page_text.lower()]
                        
                        if found_indicators:
                            logger.info(f"✅ Property data indicators found: {found_indicators}")
                        else:
                            logger.info("❌ No property data indicators found")
                    
                except Exception as e:
                    logger.error(f"❌ Search test failed: {str(e)}")
            
            # Wait for user to see
            await asyncio.sleep(10)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error accessing {site_name}: {str(e)}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Test sites without proxy"""
    
    sites = [
        ("https://www.redfin.com", "redfin"),
        ("https://www.homes.com", "homes"),
        ("https://www.movoto.com", "movoto")
    ]
    
    print("No Proxy Site Access Test")
    print("=" * 30)
    
    for site_url, site_name in sites:
        print(f"\nTesting {site_name.upper()}...")
        success = await test_site_without_proxy(site_url, site_name)
        
        if success:
            print(f"✅ {site_name.upper()} - Success")
        else:
            print(f"❌ {site_name.upper()} - Failed")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())
