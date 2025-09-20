#!/usr/bin/env python3
"""
Property Scraper v2 - Human-like Behaviors & Firefox
Enhanced with advanced anti-detection techniques
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time
import random  # Added for human-like delays and UA rotation
import ssl
from dotenv import load_dotenv

# Load environment variables from .env file
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

        # Create screenshots directory
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Bright Data proxy config (using proven working configuration from AVM_deep)
        self.proxy_server = "http://brd.superproxy.io:33335"
        self.proxy_username = os.getenv("BRIGHT_DATA_USERNAME", "brd-customer-hl_dd2a0351-zone-residential_proxy_us1")  # Base per Claude/docs—green
        self.proxy_password = os.getenv("BRIGHT_DATA_PASSWORD", "")

        # Certificate configuration with multiple fallbacks
        self.cert_path = self._find_certificate_path()

        # Comprehensive SSL environment setup (proven working from AVM_deep)
        os.environ['NODE_EXTRA_CA_CERTS'] = self.cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = self.cert_path
        os.environ['SSL_CERT_FILE'] = self.cert_path
        os.environ['CURL_CA_BUNDLE'] = self.cert_path

        print(f"Certificate Path: {self.cert_path}")
        print(f"Certificate Exists: {os.path.exists(self.cert_path)}")

        # Log creds (masked) for debug
        print(f"Proxy Username: {self.proxy_username}")
        print(f"Proxy Password Set: {'Yes' if self.proxy_password else 'No (ERROR: Set in .env)'}")

        if not self.proxy_password:
            self.data["errors"].append("Proxy password not set in env—407 likely")

        # Random user-agents for anti-bot
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
        ]

        print("PropertyScraper Class Loaded—Scope Green!")  # Debug for NameError fix

    def _find_certificate_path(self):
        """Find the correct certificate path with fallbacks"""
        possible_paths = [
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt',
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/exported_Bright Data Proxy Root CA.cer',
            os.path.expanduser('~/Downloads/bright_ca.crt'),
            os.path.expanduser('~/Downloads/exported_Bright Data Proxy Root CA.cer')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found certificate at: {path}")
                return path

        # Fallback to first path even if not found
        print(f"Certificate not found, using default: {possible_paths[0]}")
        return possible_paths[0]

    async def log_step(self, step, message, page=None):
        """Log a step and optionally take screenshot"""
        print(f"[{step}] {message}")
        self.data["steps_completed"].append(f"{step}: {message}")

        if page:
            screenshot_path = f"{self.screenshots_dir}/{step.lower().replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved: {screenshot_path}")

    async def scrape_homes_com(self, page):
        """Scrape Homes.com with advanced human-like behaviors"""
        try:
            # Step 1: Navigate to homepage (human-like approach)
            await self.log_step("STEP_1_INITIAL_LOAD", "Loading Homes.com homepage", page)
            await page.goto("https://www.homes.com", wait_until="networkidle")
            await page.wait_for_timeout(2000 + random.uniform(1000, 3000))  # Variable load time

            # Human-like initial page interaction
            await page.evaluate('window.scrollTo(0, 200);')  # Small scroll to show engagement
            await page.wait_for_timeout(random.uniform(800, 1500))  # Reading pause
            await self.log_step("STEP_1_LOADED", "Homes.com homepage loaded", page)

            # Step 2: Human-like search interaction
            await self.log_step("STEP_2_SEARCH_START", "Looking for search input with human behavior", page)

            search_selectors = [
                'input[placeholder*="Enter an address"]',
                'input[placeholder*="address"]',
                'input[name="searchfield"]',
                'input[id*="search"]',
                '#searchfield',
                '.search-input',
                'input[type="text"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        await self.log_step("STEP_2_SEARCH_FOUND", f"Found search input: {selector}", page)

                        # Get element position for realistic mouse movement
                        box = await search_input.bounding_box()
                        if box:
                            # Move mouse to search box with human-like path
                            start_x, start_y = random.uniform(100, 300), random.uniform(100, 300)
                            target_x = box['x'] + box['width'] / 2
                            target_y = box['y'] + box['height'] / 2

                            # Multi-step mouse movement (more human-like)
                            mid_x = (start_x + target_x) / 2 + random.uniform(-50, 50)
                            mid_y = (start_y + target_y) / 2 + random.uniform(-30, 30)

                            await page.mouse.move(start_x, start_y)
                            await page.wait_for_timeout(random.uniform(200, 500))
                            await page.mouse.move(mid_x, mid_y)
                            await page.wait_for_timeout(random.uniform(150, 400))
                            await page.mouse.move(target_x, target_y)
                            await page.wait_for_timeout(random.uniform(300, 700))

                            # Click and focus
                            await page.mouse.click(target_x, target_y)
                            await page.wait_for_timeout(random.uniform(400, 800))
                        break
                except:
                    continue

            if not search_input:
                await self.log_step("STEP_2_SEARCH_FAILED", "Could not find search input", page)
                self.data["errors"].append("Search input not found")
                return

            # Step 3: Human-like typing (char-by-char)
            await self.log_step("STEP_3_ENTER_ADDRESS", f"Typing address human-like: {self.address}", page)

            # Clear any existing content
            await page.keyboard.press('Control+a')
            await page.wait_for_timeout(random.uniform(100, 300))

            # Type character by character with human-like delays
            for char in self.address:
                await page.keyboard.type(char)
                delay = random.uniform(80, 180)  # 80-180ms between chars
                # Occasional longer pauses (like thinking)
                if random.random() < 0.1:  # 10% chance
                    delay += random.uniform(200, 500)
                await page.wait_for_timeout(delay)

            # Brief pause after typing (human behavior)
            await page.wait_for_timeout(random.uniform(500, 1200))
            await self.log_step("STEP_3_ADDRESS_ENTERED", "Address typed with human timing", page)

            # Step 4: Submit search (random method)
            await self.log_step("STEP_4_SUBMIT_SEARCH", "Submitting search with random method", page)

            if random.random() < 0.5:  # 50% chance keyboard enter
                await page.keyboard.press("Enter")
                method = "keyboard Enter"
            else:  # 50% chance click submit button
                # Look for submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    '.search-button',
                    '[aria-label*="search"]',
                    'button:has-text("Search")'
                ]

                clicked = False
                for selector in submit_selectors:
                    try:
                        submit_btn = await page.wait_for_selector(selector, timeout=2000)
                        if submit_btn:
                            await submit_btn.click()
                            method = f"click {selector}"
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    await page.keyboard.press("Enter")  # Fallback
                    method = "keyboard Enter (fallback)"

            await page.wait_for_timeout(3000 + random.uniform(2000, 5000))
            await self.log_step("STEP_4_SEARCH_SUBMITTED", f"Search submitted via {method}", page)

            # Step 5: Look for results
            await self.log_step("STEP_5_RESULTS_CHECK", "Checking for search results", page)

            # Check if we're on a property page directly
            property_indicators = [
                '.property-details',
                '.property-info',
                '[data-testid="property-details"]',
                '.listing-details',
                'h1[data-testid="property-address"]'
            ]

            is_property_page = False
            for indicator in property_indicators:
                if await page.locator(indicator).count() > 0:
                    is_property_page = True
                    await self.log_step("STEP_5_DIRECT_PROPERTY", f"Found direct property page indicator: {indicator}", page)
                    break

            if is_property_page:
                # We're already on the property page
                await self.extract_homes_property_data(page)
            else:
                # Look for search results
                result_selectors = [
                    '.search-result',
                    '.property-card',
                    '.listing-card',
                    '[data-testid="property-card"]',
                    '.property-item'
                ]

                found_results = False
                for selector in result_selectors:
                    results = await page.locator(selector).count()
                    if results > 0:
                        await self.log_step("STEP_5_RESULTS_FOUND", f"Found {results} results with selector: {selector}", page)
                        # Click first result
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(3000 + random.uniform(0, 2000))
                        await self.log_step("STEP_6_CLICKED_RESULT", "Clicked on first search result", page)
                        await self.extract_homes_property_data(page)
                        found_results = True
                        break

                if not found_results:
                    await self.log_step("STEP_5_NO_RESULTS", "No search results found", page)
                    self.data["errors"].append("No search results found")

                    # Check for "no results" messages
                    no_results_text = await page.text_content("body")
                    if "no results" in no_results_text.lower() or "not found" in no_results_text.lower():
                        self.data["errors"].append("Search returned 'no results' message")

        except Exception as e:
            await self.log_step("ERROR", f"Error during Homes.com scraping: {str(e)}", page)
            self.data["errors"].append(f"Scraping error: {str(e)}")

    async def extract_homes_property_data(self, page):
        """Extract property data from Homes.com property page"""
        try:
            await self.log_step("EXTRACT_START", "Starting data extraction", page)

            # Extract basic property info
            property_data = {}

            # Address
            address_selectors = [
                'h1[data-testid="property-address"]',
                '.property-address',
                '.listing-address',
                'h1.address'
            ]

            for selector in address_selectors:
                try:
                    address_elem = await page.wait_for_selector(selector, timeout=2000)
                    if address_elem:
                        property_data["address"] = await address_elem.text_content()
                        break
                except:
                    continue

            # Beds, Baths, Sqft
            detail_selectors = {
                "beds": ['[data-testid="beds"]', '.beds', '[aria-label*="bed"]'],
                "baths": ['[data-testid="baths"]', '.baths', '[aria-label*="bath"]'],
                "sqft": ['[data-testid="sqft"]', '.sqft', '[aria-label*="sqft"]', '[aria-label*="square"]']
            }

            for key, selectors in detail_selectors.items():
                for selector in selectors:
                    try:
                        elem = await page.wait_for_selector(selector, timeout=2000)
                        if elem:
                            text = await elem.text_content()
                            property_data[key] = text.strip()
                            break
                    except:
                        continue

            # Year built
            year_selectors = [
                '[data-testid="year-built"]',
                '.year-built',
                '[aria-label*="year"]'
            ]

            for selector in year_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["year_built"] = await elem.text_content()
                        break
                except:
                    continue

            # Photos
            photo_selectors = [
                '.property-photos img',
                '.listing-photos img',
                '.photo-gallery img',
                '[data-testid="property-photo"]'
            ]

            photos = []
            for selector in photo_selectors:
                try:
                    photo_elements = await page.locator(selector).all()
                    for photo in photo_elements[:10]:  # Limit to 10 photos
                        src = await photo.get_attribute('src')
                        if src and 'http' in src:
                            photos.append(src)
                    if photos:
                        break
                except:
                    continue

            property_data["photos"] = photos

            # AVM/Estimate
            avm_selectors = [
                '[data-testid="avm"]',
                '.avm-value',
                '.estimate-value',
                '.property-value'
            ]

            for selector in avm_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["avm"] = await elem.text_content()
                        break
                except:
                    continue

            # Status (Listed/Not Listed)
            status_selectors = [
                '.listing-status',
                '[data-testid="listing-status"]',
                '.property-status'
            ]

            for selector in status_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["status"] = await elem.text_content()
                        break
                except:
                    continue

            # Check page content for "NOT LISTED" or similar
            page_content = await page.text_content("body")
            if "not listed" in page_content.lower():
                property_data["status"] = "NOT LISTED FOR SALE"

            self.data["property_data"] = property_data
            self.data["found"] = len(property_data) > 0

            await self.log_step("EXTRACT_COMPLETE", f"Extracted data: {json.dumps(property_data, indent=2)}", page)

        except Exception as e:
            await self.log_step("EXTRACT_ERROR", f"Error extracting data: {str(e)}", page)
            self.data["errors"].append(f"Data extraction error: {str(e)}")

    async def scrape_redfin(self, page):
        """Scrape Redfin with detailed visual documentation"""
        try:
            # Step 1: Navigate to Redfin
            await self.log_step("STEP_1_INITIAL_LOAD", "Loading Redfin homepage", page)
            await page.goto("https://www.redfin.com", wait_until="networkidle")
            await page.wait_for_timeout(3000 + random.uniform(0, 2000))
            await self.log_step("STEP_1_LOADED", "Redfin homepage loaded", page)

            # Step 2: Find search box
            await self.log_step("STEP_2_SEARCH_START", "Looking for search input", page)

            search_selectors = [
                'input[placeholder*="Enter an Address"]',
                'input[placeholder*="address"]',
                '#search-box-input',
                '.search-input-box',
                'input[data-rf-test-id="search-box-input"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=2000)
                    if search_input:
                        await self.log_step("STEP_2_SEARCH_FOUND", f"Found search input with selector: {selector}", page)
                        break
                except:
                    continue

            if not search_input:
                await self.log_step("STEP_2_SEARCH_FAILED", "Could not find search input", page)
                self.data["errors"].append("Search input not found")
                return

            # Step 3: Enter address
            await self.log_step("STEP_3_ENTER_ADDRESS", f"Entering address: {self.address}", page)
            await search_input.fill(self.address)
            await page.wait_for_timeout(1000 + random.uniform(0, 1000))
            await self.log_step("STEP_3_ADDRESS_ENTERED", "Address entered in search box", page)

            # Step 4: Submit search
            await self.log_step("STEP_4_SUBMIT_SEARCH", "Submitting search", page)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000 + random.uniform(0, 3000))
            await self.log_step("STEP_4_SEARCH_SUBMITTED", "Search submitted, waiting for results", page)

            # Step 5: Handle results
            await self.log_step("STEP_5_RESULTS_CHECK", "Checking for search results", page)

            # Check if we're on a property page directly
            if "/home/" in page.url:
                await self.log_step("STEP_5_DIRECT_PROPERTY", "Landed directly on property page", page)
                await self.extract_redfin_property_data(page)
            else:
                # Look for search results
                result_selectors = [
                    '.SearchResultsList .result',
                    '.search-result-item',
                    '[data-rf-test-id="search-result"]'
                ]

                found_results = False
                for selector in result_selectors:
                    results = await page.locator(selector).count()
                    if results > 0:
                        await self.log_step("STEP_5_RESULTS_FOUND", f"Found {results} results with selector: {selector}", page)
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(3000 + random.uniform(0, 2000))
                        await self.log_step("STEP_6_CLICKED_RESULT", "Clicked on first search result", page)
                        await self.extract_redfin_property_data(page)
                        found_results = True
                        break

                if not found_results:
                    await self.log_step("STEP_5_NO_RESULTS", "No search results found", page)
                    self.data["errors"].append("No search results found")

        except Exception as e:
            await self.log_step("ERROR", f"Error during Redfin scraping: {str(e)}", page)
            self.data["errors"].append(f"Scraping error: {str(e)}")

    async def extract_redfin_property_data(self, page):
        """Extract property data from Redfin property page"""
        try:
            await self.log_step("EXTRACT_START", "Starting data extraction", page)

            property_data = {}

            # Address
            address_selectors = [
                '.street-address',
                '[data-rf-test-id="abp-streetLine"]',
                '.address'
            ]

            for selector in address_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["address"] = await elem.text_content()
                        break
                except:
                    continue

            # Property details
            detail_selectors = {
                "beds": ['.beds .value', '[data-rf-test-id="abp-beds"]'],
                "baths": ['.baths .value', '[data-rf-test-id="abp-baths"]'],
                "sqft": ['.sqft .value', '[data-rf-test-id="abp-sqFt"]']
            }

            for key, selectors in detail_selectors.items():
                for selector in selectors:
                    try:
                        elem = await page.wait_for_selector(selector, timeout=2000)
                        if elem:
                            property_data[key] = await elem.text_content()
                            break
                    except:
                        continue

            # Year built
            year_selectors = [
                '[data-rf-test-id="abp-yearBuilt"]',
                '.year-built .value'
            ]

            for selector in year_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["year_built"] = await elem.text_content()
                        break
                except:
                    continue

            # Photos
            photo_selectors = [
                '.MediaCarousel img',
                '.photo-carousel img',
                '.property-photos img'
            ]

            photos = []
            for selector in photo_selectors:
                try:
                    photo_elements = await page.locator(selector).all()
                    for photo in photo_elements[:10]:
                        src = await photo.get_attribute('src')
                        if src and 'http' in src:
                            photos.append(src)
                    if photos:
                        break
                except:
                    continue

            property_data["photos"] = photos

            # Redfin Estimate
            estimate_selectors = [
                '.avm-value',
                '[data-rf-test-id="avm-value"]',
                '.redfin-estimate'
            ]

            for selector in estimate_selectors:
                try:
                    elem = await page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        property_data["redfin_estimate"] = await elem.text_content()
                        break
                except:
                    continue

            self.data["property_data"] = property_data
            self.data["found"] = len(property_data) > 0

            await self.log_step("EXTRACT_COMPLETE", f"Extracted data: {json.dumps(property_data, indent=2)}", page)

        except Exception as e:
            await self.log_step("EXTRACT_ERROR", f"Error extracting data: {str(e)}", page)
            self.data["errors"].append(f"Data extraction error: {str(e)}")

    async def run(self):
        """Run the scraper with Firefox and human behaviors"""
        async with async_playwright() as p:
            # Launch with Firefox for better evasion (proven success from AVM_deep)
            browser = await p.firefox.launch(
                headless=False,  # Visible for test
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    f'--user-agent={random.choice(self.user_agents)}'
                ],
                proxy={
                    'server': self.proxy_server,
                    'username': self.proxy_username,
                    'password': self.proxy_password
                }
            )

            # Create context with deeper SSL ignore
            context = await browser.new_context(ignore_https_errors=True)

            page = await context.new_page()
            page.set_default_timeout(30000)

            # Filtered network logging (avoid terminal flood)
            async def log_response(response):
                # Only log key responses, not every asset
                if any(domain in response.url for domain in ['homes.com', 'redfin.com', 'httpbin.org']) and '/api/' not in response.url:
                    status_icon = "✅" if response.status < 400 else "❌"
                    print(f"{status_icon} {response.url} - {response.status}")

                if response.status >= 400:
                    self.data["errors"].append(f"HTTP Error {response.status} on {response.url}")

            page.on("response", log_response)

            try:
                if self.site == "homes":
                    await self.scrape_homes_com(page)
                elif self.site == "redfin":
                    await self.scrape_redfin(page)
                else:
                    self.data["errors"].append(f"Unknown site: {self.site}")

                # Save results
                results_file = f"results_{self.site}_{self.timestamp}.json"
                with open(results_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                print(f"\nResults saved to: {results_file}")
                print(f"Screenshots saved to: {self.screenshots_dir}/")
                print(f"Found property: {self.data['found']}")
                print(f"Errors: {len(self.data['errors'])}")

                await asyncio.sleep(5)  # 5s hold for evidence collection

            finally:
                await context.close()
                await browser.close()

async def main():
    if len(sys.argv) != 3:
        print("Usage: python scrape_property.py '<address>' <site>")
        print("Sites: homes, redfin")
        sys.exit(1)

    address = sys.argv[1]
    site = sys.argv[2]

    scraper = PropertyScraper(address, site)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())