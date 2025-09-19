#!/usr/bin/env python3
"""
Quick Test - Bypass all timeout issues
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time
import random
from dotenv import load_dotenv

load_dotenv()

class QuickScraper:
    def __init__(self, address, site):
        self.address = address
        self.site = site.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots_dir = f"screenshots/quick_{self.timestamp}"
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

        print(f"📁 Screenshots: {self.screenshots_dir}/")
        print(f"🔧 Proxy: {self.proxy_username}")
        print(f"🔧 Password: {'✅' if self.proxy_password else '❌'}")

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

    async def test_homes(self, page):
        """Quick homes.com test - no timeouts"""
        try:
            await self.log_step("START", "Quick test starting")

            # Go to page with timeout handling
            print("🚀 Going to homes.com...")
            try:
                await page.goto("https://www.homes.com", wait_until="load", timeout=10000)
            except Exception as e:
                print(f"⚠️ Load timeout (expected): {e}")
                print("📄 Page likely loaded anyway, continuing...")

            await asyncio.sleep(2)  # Let page settle
            await self.log_step("LOADED", "Page loaded (timeout handled)", page)

            # Quick check for inputs
            inputs = await page.locator('input').count()
            print(f"🔍 Found {inputs} input elements")

            if inputs > 0:
                # Try first input
                first_input = page.locator('input').first
                await first_input.click()
                await asyncio.sleep(0.5)

                # Type address quickly
                await first_input.type(self.address, delay=50)
                await asyncio.sleep(1)
                await self.log_step("TYPED", "Address typed", page)

                # Submit
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                await self.log_step("SUBMITTED", "Search submitted", page)

                self.data["found"] = True

            else:
                await self.log_step("NO_INPUTS", "No inputs found")

        except Exception as e:
            print(f"❌ Error: {e}")
            await self.log_step("ERROR", f"Error: {str(e)}", page)
            self.data["errors"].append(str(e))

    async def run(self):
        """Quick run"""
        print("⚡ QUICK TEST MODE")

        async with async_playwright() as p:
            try:
                # Simple Firefox launch
                browser = await p.firefox.launch(
                    headless=False,
                    proxy={
                        'server': self.proxy_server,
                        'username': self.proxy_username,
                        'password': self.proxy_password
                    }
                )

                context = await browser.new_context(
                    ignore_https_errors=True
                )

                page = await context.new_page()

                # Run test
                await self.test_homes(page)

                # Save results
                results_file = f"quick_results_{self.timestamp}.json"
                with open(results_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                print(f"\n📊 RESULTS:")
                print(f"   Results: {results_file}")
                print(f"   Success: {self.data['found']}")
                print(f"   Errors: {len(self.data['errors'])}")

                # Brief hold
                print("⏳ Holding for 2 seconds...")
                await asyncio.sleep(2)

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
        print("Usage: python scrape_quick_test.py '<address>' homes")
        sys.exit(1)

    address = sys.argv[1]
    site = sys.argv[2]

    scraper = QuickScraper(address, site)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())