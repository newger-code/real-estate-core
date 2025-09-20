#!/usr/bin/env python3
"""
Direct Browser Test - See what's actually happening
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from proxy_config import get_playwright_proxy
from utils.common import setup_logger

async def test_site_access(site_url: str, site_name: str):
    """Test direct access to a site"""
    
    logger = setup_logger(f"direct_test_{site_name}")
    
    async with async_playwright() as p:
        # Get proxy config
        proxy_config = get_playwright_proxy()
        
        browser = await p.chromium.launch(
            headless=False,  # Show browser for debugging
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with proxy
        context = await browser.new_context(
            proxy=proxy_config,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            viewport={"width": 1366, "height": 768},
            ignore_https_errors=True  # Ignore SSL errors for proxy
        )
        
        page = await context.new_page()
        
        try:
            logger.info(f"Loading {site_name}: {site_url}")
            
            # Navigate to site
            await page.goto(site_url, wait_until="networkidle", timeout=30000)
            
            # Take screenshot
            screenshot_path = f"direct_test_{site_name}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Get page title and URL
            title = await page.title()
            current_url = page.url
            
            logger.info(f"Title: {title}")
            logger.info(f"Current URL: {current_url}")
            
            # Check for blocking indicators
            page_content = await page.text_content("body")
            
            blocking_keywords = ["blocked", "access denied", "403", "cloudflare", "captcha"]
            for keyword in blocking_keywords:
                if keyword.lower() in page_content.lower():
                    logger.warning(f"⚠️  Potential blocking detected: {keyword}")
            
            # Look for search inputs
            search_selectors = [
                'input[placeholder*="address"]',
                'input[placeholder*="Address"]',
                'input[type="search"]',
                'input[type="text"]',
                '#search',
                '.search-input'
            ]
            
            found_inputs = []
            for selector in search_selectors:
                try:
                    elements = await page.locator(selector).count()
                    if elements > 0:
                        found_inputs.append(f"{selector} ({elements} elements)")
                except:
                    pass
            
            if found_inputs:
                logger.info("✅ Search inputs found:")
                for inp in found_inputs:
                    logger.info(f"   {inp}")
            else:
                logger.warning("❌ No search inputs found")
            
            # Wait a bit for user to see
            await asyncio.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error accessing {site_name}: {str(e)}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Test direct access to all sites"""
    
    sites = [
        ("https://www.redfin.com", "redfin"),
        ("https://www.homes.com", "homes"),
        ("https://www.movoto.com", "movoto")
    ]
    
    print("Direct Site Access Test")
    print("=" * 30)
    
    for site_url, site_name in sites:
        print(f"\nTesting {site_name.upper()}...")
        success = await test_site_access(site_url, site_name)
        
        if success:
            print(f"✅ {site_name.upper()} - Accessible")
        else:
            print(f"❌ {site_name.upper()} - Failed")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())
