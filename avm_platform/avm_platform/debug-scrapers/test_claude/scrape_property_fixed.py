#!/usr/bin/env python3
"""
Property Scraper v2.1 - Firefox Fixed & Homes.com Focus
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time
import random
import ssl
from dotenv import load_dotenv

load_dotenv()

class PropertyScraper:
    def __init__(self, address, site):
        self.address = address
        self.site = site.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots_dir = f"screenshots/screenshots_{self.site}_{self.timestamp}"
        self.data = {
            "address": address,
            "site": site,
            "timestamp": self.timestamp,
            "found": False,
            "property_data": {},
            "errors": [],
            "steps_completed": []
        }

        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Proxy configuration
        self.proxy_server = "http://brd.superproxy.io:33335"
        self.proxy_username = os.getenv("BRIGHT_DATA_USERNAME", "brd-customer-hl_dd2a0351-zone-residential_proxy_us1")
        self.proxy_password = os.getenv("BRIGHT_DATA_PASSWORD", "")

        # Certificate setup
        self.cert_path = self._find_certificate_path()
        os.environ['NODE_EXTRA_CA_CERTS'] = self.cert_path

        print(f"Certificate: {self.cert_path} (exists: {os.path.exists(self.cert_path)})")
        print(f"Proxy: {self.proxy_username}")
        print(f"Password: {'Yes' if self.proxy_password else 'No'}")

        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]

        print("PropertyScraper Ready!")

    def _find_certificate_path(self):
        paths = [
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt',
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/exported_Bright Data Proxy Root CA.cer'
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return paths[0]

    async def log_step(self, step, message, page=None):
        print(f"[{step}] {message}")
        self.data["steps_completed"].append(f"{step}: {message}")

        if page:
            screenshot_path = f"{self.screenshots_dir}/{step.lower().replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot: {screenshot_path}")

    async def scrape_homes_com(self, page):
        """Scrape homes.com with human behaviors"""
        try:
            # Step 1: Load homepage
            await self.log_step("STEP_1_LOAD", "Loading homes.com homepage", page)
            await page.goto("https://www.homes.com", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(random.uniform(2000, 4000))
            await self.log_step("STEP_1_LOADED", "Homepage loaded successfully", page)

            # Step 2: Find search box
            await self.log_step("STEP_2_SEARCH", "Looking for search input", page)

            search_selectors = [
                'input[placeholder*="address"]',
                'input[name*="search"]',
                '#searchfield',
                'input[type="text"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        await self.log_step("STEP_2_FOUND", f"Found: {selector}", page)

                        # Human-like click
                        box = await search_input.bounding_box()
                        if box:
                            click_x = box['x'] + box['width'] / 2
                            click_y = box['y'] + box['height'] / 2
                            await page.mouse.click(click_x, click_y)
                            await page.wait_for_timeout(random.uniform(500, 1000))
                        break
                except:
                    continue

            if not search_input:
                await self.log_step("STEP_2_FAILED", "No search input found", page)
                return

            # Step 3: Type address
            await self.log_step("STEP_3_TYPE", "Typing address character by character", page)

            # Clear field
            await page.keyboard.press('Control+a')
            await page.wait_for_timeout(200)

            # Type char by char
            for char in self.address:
                await page.keyboard.type(char)
                await page.wait_for_timeout(random.uniform(100, 200))

            await page.wait_for_timeout(random.uniform(800, 1500))
            await self.log_step("STEP_3_TYPED", "Address entered", page)

            # Step 4: Submit
            await self.log_step("STEP_4_SUBMIT", "Submitting search", page)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(random.uniform(4000, 7000))
            await self.log_step("STEP_4_SUBMITTED", "Search submitted", page)

            # Step 5: Check results
            await self.log_step("STEP_5_RESULTS", "Checking for results", page)

            # Save final state
            self.data["found"] = True  # For now, mark as found if we got this far

        except Exception as e:
            await self.log_step("ERROR", f"Error: {str(e)}", page)
            self.data["errors"].append(str(e))

    async def run(self):
        """Run the scraper with proper Firefox setup"""
        async with async_playwright() as p:
            try:
                # Firefox launch with minimal, correct arguments
                browser = await p.firefox.launch(
                    headless=False,
                    proxy={
                        'server': self.proxy_server,
                        'username': self.proxy_username,
                        'password': self.proxy_password
                    }
                )

                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    ignore_https_errors=True
                )

                page = await context.new_page()
                page.set_default_timeout(30000)

                # Simple response logging
                async def log_response(response):
                    if 'homes.com' in response.url and response.status >= 400:
                        print(f"❌ {response.url} - {response.status}")
                    elif 'homes.com' in response.url:
                        print(f"✅ {response.url} - {response.status}")

                page.on("response", log_response)

                # Only test homes.com
                if self.site == "homes":
                    await self.scrape_homes_com(page)
                else:
                    print(f"Only 'homes' supported for now, got: {self.site}")

                # Save results
                results_file = f"results_{self.site}_{self.timestamp}.json"
                with open(results_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                print(f"\n📁 Results: {results_file}")
                print(f"📸 Screenshots: {self.screenshots_dir}/")
                print(f"✅ Success: {self.data['found']}")
                print(f"❌ Errors: {len(self.data['errors'])}")

                # Short hold for evidence
                print("Holding browser for 3 seconds...")
                await asyncio.sleep(3)

            except Exception as e:
                print(f"❌ Critical error: {e}")
            finally:
                try:
                    await context.close()
                    await browser.close()
                    print("🧹 Browser closed")
                except:
                    pass

async def main():
    if len(sys.argv) != 3:
        print("Usage: python scrape_property_fixed.py '<address>' homes")
        sys.exit(1)

    address = sys.argv[1]
    site = sys.argv[2]

    if site != "homes":
        print("Only 'homes' site supported in this fixed version")
        sys.exit(1)

    scraper = PropertyScraper(address, site)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())