#!/usr/bin/env python3
"""
No Proxy Test - Isolate search logic vs proxy performance issues
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time
import random

class NoProxyScraper:
    def __init__(self, address, site):
        self.address = address
        self.site = site.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots_dir = f"screenshots/no_proxy_{self.timestamp}"
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
        print(f"📁 Screenshots: {self.screenshots_dir}/")
        print("🚫 NO PROXY MODE - Testing search logic directly")

    async def log_step(self, step, message, page=None):
        print(f"🔍 [{step}] {message}")
        self.data["steps_completed"].append(f"{step}: {message}")

        if page:
            screenshot_path = f"{self.screenshots_dir}/{step.lower().replace(' ', '_')}.png"
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot: {screenshot_path}")
            except:
                print(f"⚠️ Screenshot failed")

    async def test_homes_search(self, page):
        """Test homes.com search without proxy interference"""
        try:
            await self.log_step("START", "Starting no-proxy homes.com test")

            # Should load instantly without proxy
            print("🚀 Loading homes.com (no proxy)...")
            await page.goto("https://www.homes.com")
            await asyncio.sleep(2)
            await self.log_step("LOADED", "Page loaded instantly", page)

            # Debug inputs available
            inputs = await page.locator('input').count()
            print(f"🔍 Found {inputs} input elements")

            if inputs == 0:
                await self.log_step("NO_INPUTS", "No inputs found", page)
                return

            # Test first few inputs for interactivity
            for i in range(min(inputs, 3)):
                input_elem = page.locator('input').nth(i)
                try:
                    placeholder = await input_elem.get_attribute('placeholder') or 'no placeholder'
                    is_visible = await input_elem.is_visible()
                    is_enabled = await input_elem.is_enabled()

                    print(f"   Input {i}: placeholder='{placeholder}', visible={is_visible}, enabled={is_enabled}")

                    # Try the first search-like input
                    if ('address' in placeholder.lower() or 'search' in placeholder.lower()) and is_visible and is_enabled:
                        await self.log_step("FOUND_SEARCH", f"Found search input {i}: {placeholder}", page)

                        # Test interaction
                        await input_elem.click()
                        await asyncio.sleep(0.5)
                        await self.log_step("CLICKED", "Search input clicked", page)

                        # Type address
                        await input_elem.type(self.address, delay=100)
                        await asyncio.sleep(1)
                        await self.log_step("TYPED", f"Address '{self.address}' typed", page)

                        # Submit
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(3)
                        await self.log_step("SUBMITTED", "Search submitted", page)

                        self.data["found"] = True
                        return

                except Exception as e:
                    print(f"   Input {i} failed: {e}")
                    continue

            await self.log_step("NO_SEARCH_INPUT", "No suitable search input found", page)

        except Exception as e:
            print(f"❌ Error: {e}")
            await self.log_step("ERROR", f"Error: {str(e)}", page)
            self.data["errors"].append(str(e))

    async def run(self):
        """Run no-proxy test"""
        print("🚫 NO PROXY TEST MODE - Isolating search logic")

        async with async_playwright() as p:
            try:
                # Firefox launch WITHOUT proxy
                browser = await p.firefox.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                # Run test
                await self.test_homes_search(page)

                # Save results
                results_file = f"no_proxy_results_{self.timestamp}.json"
                with open(results_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                print(f"\n📊 NO PROXY RESULTS:")
                print(f"   Results: {results_file}")
                print(f"   Success: {self.data['found']}")
                print(f"   Errors: {len(self.data['errors'])}")
                print(f"   Steps: {len(self.data['steps_completed'])}")

                # Hold for analysis
                print("⏳ Holding for 3 seconds...")
                await asyncio.sleep(3)

            except Exception as e:
                print(f"💥 Browser error: {e}")
            finally:
                try:
                    await context.close()
                    await browser.close()
                    print("🧹 Browser closed")
                except:
                    pass

async def main():
    if len(sys.argv) != 3:
        print("Usage: python scrape_no_proxy_test.py '<address>' homes")
        sys.exit(1)

    address = sys.argv[1]
    site = sys.argv[2]

    scraper = NoProxyScraper(address, site)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())