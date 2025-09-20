#!/usr/bin/env python3
"""
Property Scraper Debug Version - Find exactly where it fails
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
from smart_extraction import SmartPropertyExtractor

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

        # No-proxy test flag (disable proxy for isolate; env NO_PROXY=true to toggle)
        self.no_proxy = os.getenv("NO_PROXY", "false").lower() == "true"
        if self.no_proxy:
            print("NO_PROXY MODE - Running without proxy for test (IP block risk long-term)")

        # Bright Data proxy config (hands off if no_proxy)
        self.proxy_server = "http://brd.superproxy.io:33335"
        self.proxy_username = os.getenv("BRIGHT_DATA_USERNAME", "brd-customer-hl_dd2a0351-zone-residential_proxy_us1")
        self.proxy_password = os.getenv("BRIGHT_DATA_PASSWORD", "")

        # Load cert for Node/Playwright trust
        os.environ['NODE_EXTRA_CA_CERTS'] = '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt'
        print("Cert Path Loaded: /Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt")

        # Log creds (masked) for debug
        print(f"Proxy Username: {self.proxy_username}")
        print(f"Proxy Password Set: {'Yes' if self.proxy_password else 'No (ERROR: Set in .env)'}")

        if not self.proxy_password and not self.no_proxy:
            self.data["errors"].append("Proxy password not set in env—407 likely")

        # Random user-agents for anti-bot
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
        ]

        print(f"📁 Screenshots will go to: {self.screenshots_dir}/")
        print("PropertyScraper Class Loaded—Scope Green!")  # Debug for NameError fix

        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]

    def _find_certificate_path(self):
        paths = [
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt',
            '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/exported_Bright Data Proxy Root CA.cer'
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return paths[0]

    async def log_step(self, step, message, page=None, take_screenshot=True):
        print(f"\n🔍 [{step}] {message}")
        self.data["steps_completed"].append(f"{step}: {message}")

        if page and take_screenshot:
            screenshot_path = f"{self.screenshots_dir}/{step.lower().replace(' ', '_')}.png"
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"⚠️ Screenshot failed: {e}")

    async def debug_page_content(self, page, step_name):
        """Debug what's actually on the page"""
        try:
            # Get page title and URL
            title = await page.title()
            url = page.url
            print(f"🌐 Page: {title} | URL: {url}")

            # Look for any input elements
            inputs = await page.locator('input').count()
            print(f"🔍 Found {inputs} input elements")

            if inputs > 0:
                for i in range(min(inputs, 5)):  # Check first 5 inputs
                    input_elem = page.locator('input').nth(i)
                    try:
                        input_type = await input_elem.get_attribute('type') or 'text'
                        placeholder = await input_elem.get_attribute('placeholder') or 'no placeholder'
                        name = await input_elem.get_attribute('name') or 'no name'
                        print(f"   Input {i}: type='{input_type}', placeholder='{placeholder}', name='{name}'")
                    except:
                        print(f"   Input {i}: could not get attributes")

            # Take debug screenshot
            await self.log_step(f"DEBUG_{step_name}", f"Page analysis: {inputs} inputs found", page)

        except Exception as e:
            print(f"❌ Debug failed: {e}")

    async def scrape_homes_com(self, page):
        """Scrape Homes.com with detailed visual documentation"""
        try:
            # Step 1: Navigate to homepage for search bar (screenshot green—dropdown suggestions confirm)
            await self.log_step("STEP_1_INITIAL_LOAD", "Loading Homes.com homepage", page)

            # Handle timeout gracefully
            try:
                await page.goto("https://www.homes.com", wait_until="networkidle", timeout=15000)
            except Exception as e:
                print(f"⚠️ Page load timeout, but continuing anyway: {e}")
                # Continue - page might be partially loaded and usable

            await page.wait_for_timeout(3000 + random.uniform(0, 2000))  # Variable timing
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2);')  # Human scroll down
            await page.wait_for_timeout(random.uniform(1000, 3000))  # Pause like reading
            await page.evaluate('window.scrollTo(0, 0);')  # Scroll back up
            await self.log_step("STEP_1_LOADED", "Homes.com homepage loaded", page)

            # Step 2: Find and interact with search bar (hover/focus for human-like)
            await self.log_step("STEP_2_SEARCH_START", "Looking for search input", page)

            search_selectors = [
                'input[placeholder*="Place, Neighborhood, School or Agent"]',  # From screenshot—specific placeholder
                'input[placeholder*="Enter an address"]',
                'input[placeholder*="address"]',
                'input[name="searchfield"]',
                'input[id*="search"]',
                '#searchfield',
                '.search-input',
                'input[type="text"]',
                '[aria-label*="search"]'  # Aria for accessibility
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=2000)
                    if search_input:
                        await self.log_step("STEP_2_SEARCH_FOUND", f"Found search input with selector: {selector}", page)
                        # Human-like mouse hover/focus
                        await page.mouse.move(random.uniform(100, 200), random.uniform(100, 200))  # Random cursor wiggle
                        await page.wait_for_timeout(random.uniform(500, 1000))  # Delay
                        await page.focus(selector)  # Focus like tab/user
                        await page.wait_for_timeout(random.uniform(300, 800))  # Variable focus delay
                        break
                except:
                    continue

            if not search_input:
                await self.log_step("STEP_2_SEARCH_FAILED", "Could not find search input", page)
                self.data["errors"].append("Search input not found")
                return

            # Step 3: Type address human-like (char-by-char with delays)
            await self.log_step("STEP_3_ENTER_ADDRESS", f"Entering address: {self.address}", page)
            for char in self.address:
                await search_input.type(char, delay=random.uniform(50, 150))  # Variable typing speed
            await page.wait_for_timeout(2000 + random.uniform(0, 2000))
            await self.log_step("STEP_3_ADDRESS_ENTERED", "Address entered in search bar", page)

            # Step 4: Submit search (consistent Enter key for better autocomplete compatibility)
            await self.log_step("STEP_4_SUBMIT_SEARCH", "Submitting search", page)
            await page.keyboard.press("Enter")  # Consistent Enter key usage
            submit_method = "keyboard Enter"

            await page.wait_for_timeout(5000 + random.uniform(0, 3000))
            await self.log_step("STEP_4_SEARCH_SUBMITTED", f"Search submitted via {submit_method}", page)

            # Step 5: Look for results
            await self.log_step("STEP_5_RESULTS_CHECK", "Checking for search results", page)

            # Check if we're on a property page directly
            current_url = page.url

            # First check: URL-based detection (most reliable)
            is_property_page = "/property/" in current_url and "homes.com" in current_url

            if is_property_page:
                await self.log_step("STEP_5_DIRECT_PROPERTY", f"Direct property page detected via URL: {current_url}", page)
            else:
                # Second check: CSS selectors
                property_indicators = [
                    '.property-details',
                    '.property-info',
                    '[data-testid="property-details"]',
                    '.listing-details',
                    'h1[data-testid="property-address"]',
                    '.property-title',
                    '.address-info'
                ]

                for indicator in property_indicators:
                    if await page.locator(indicator).count() > 0:
                        is_property_page = True
                        await self.log_step("STEP_5_DIRECT_PROPERTY", f"Found direct property page indicator: {indicator}", page)
                        break

            if is_property_page:
                # We're already on the property page
                print("⏳ Waiting for property page to fully load...")
                await page.wait_for_timeout(3000)

                # Scroll to load all content before extraction
                await self.scroll_page_for_complete_content(page)

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
                        await page.wait_for_timeout(5000 + random.uniform(0, 2000))  # More time to load
                        await self.log_step("STEP_6_CLICKED_RESULT", "Clicked on first search result", page)

                        # Give property page extra time to fully render
                        print("⏳ Waiting for property page to fully load...")
                        await page.wait_for_timeout(3000)

                        # Scroll to load all content before extraction
                        await self.scroll_page_for_complete_content(page)

                        await self.extract_homes_property_data(page)
                        found_results = True
                        break

                if not found_results:
                    await self.log_step("STEP_5_NO_RESULTS", "No search results found", page)
                    self.data["errors"].append("No search results found")

                    # Check for "no results" messages
                    no_results_text = await page.text_content("body")
                    if no_results_text and "no results" in no_results_text.lower():
                        self.data["errors"].append("Search returned 'no results' message")

        except Exception as e:
            await self.log_step("ERROR", f"Error during Homes.com scraping: {str(e)}", page)
            self.data["errors"].append(f"Scraping error: {str(e)}")

    async def scroll_page_for_complete_content(self, page):
        """Scroll through the page to ensure all content is loaded and accessible"""
        try:
            print("📜 Scrolling page to load all content...")

            # Get initial page height
            page_height = await page.evaluate("document.body.scrollHeight")

            # Scroll down gradually to trigger lazy loading
            scroll_step = 500  # Scroll 500px at a time
            current_position = 0

            while current_position < page_height:
                current_position += scroll_step
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                await page.wait_for_timeout(1000)  # Wait for content to load

                # Check if page height increased (more content loaded)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > page_height:
                    page_height = new_height

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)

            print(f"📜 Scrolling complete. Final page height: {page_height}px")

        except Exception as e:
            print(f"⚠️ Scrolling error: {str(e)} - continuing without scrolling")

    async def extract_homes_property_data(self, page):
        """Extract property data from Homes.com property page using smart pattern matching"""
        await self.log_step("EXTRACT_START", "Starting smart property data extraction", page)

        try:
            # Get page content for smart extraction
            print("🧠 Using smart pattern extraction instead of rigid CSS selectors")
            page_content = await page.text_content("body")

            if not page_content or len(page_content.strip()) < 100:
                self.data["errors"].append("No sufficient page content found")
                return

            # Initialize smart extractor
            extractor = SmartPropertyExtractor()

            # Perform smart extraction
            extraction_result = extractor.extract_from_content(page_content)

            # Update our data structure
            if extraction_result['found']:
                self.data["property_data"] = extraction_result['property_data']
                self.data["found"] = True

                extracted_count = len([v for v in extraction_result['property_data'].values() if v and str(v).strip()])

                print(f"✅ SMART EXTRACTION SUCCESS: Found {extracted_count} fields")
                print(f"📊 Extraction metadata: {extraction_result['extraction_metadata']}")

                await self.log_step("EXTRACT_COMPLETE", f"Smart extraction found {extracted_count} data fields", page)

            else:
                # Fallback: Keep original CSS selector method commented out for now
                print("❌ Smart extraction found insufficient data, would try CSS selectors as fallback")
                self.data["found"] = False
                self.data["errors"].append("Smart extraction insufficient - need CSS selector fallback")
                await self.log_step("EXTRACT_FAILED", "Smart extraction insufficient", page)

        except Exception as e:
            await self.log_step("EXTRACT_ERROR", f"Smart extraction error: {str(e)}", page)
            self.data["errors"].append(f"Smart extraction error: {str(e)}")
            print(f"❌ Smart extraction failed: {str(e)}")

    async def extract_homes_property_data_OLD_CSS_FALLBACK(self, page):
        """OLD CSS selector method - kept as fallback (currently commented out)"""
        try:
            # Extract address
            address_selectors = [
                'h1[data-testid="property-address"]',
                '.property-address',
                '.listing-address',
                'h1:has-text("Ave")',
                'h1:has-text("St")',
                'h1:has-text("Rd")'
            ]

            for selector in address_selectors:
                try:
                    address_elem = await page.wait_for_selector(selector, timeout=2000)
                    if address_elem:
                        address_text = await address_elem.text_content()
                        if address_text and len(address_text.strip()) > 10:
                            self.data["property_data"]["address"] = address_text.strip()
                            print(f"✅ Found address: {self.data['property_data']['address'][:50]}...")
                            break
                except Exception as e:
                    print(f"❌ Address selector '{selector}' failed: {str(e)[:50]}...")
                    continue

            # Extract status (listed/not listed)
            status_selectors = [
                '[data-testid="property-status"]',
                '.property-status',
                '.listing-status',
                'text*="NOT LISTED"',
                'text*="For Sale"'
            ]

            for selector in status_selectors:
                try:
                    status_elem = await page.wait_for_selector(selector, timeout=2000)
                    if status_elem:
                        status_text = await status_elem.text_content()
                        if status_text:
                            self.data["property_data"]["status"] = status_text.strip()
                            break
                except:
                    continue

            # Extract basic property details (beds, baths, sqft, year)
            detail_selectors = [
                '[data-testid*="bed"]',
                '[data-testid*="bath"]',
                '[data-testid*="sqft"]',
                '[data-testid*="year"]',
                'text*="bed"',
                'text*="bath"',
                'text*="sqft"',
                'text*="Built"'
            ]

            for selector in detail_selectors:
                try:
                    detail_elems = await page.locator(selector).all()
                    for elem in detail_elems[:10]:  # Check first 10 matches
                        text = await elem.text_content()
                        if text:
                            text = text.lower().strip()
                            if 'bed' in text and 'bedroom' not in self.data["property_data"]:
                                self.data["property_data"]["beds"] = text
                            elif 'bath' in text and 'bathroom' not in self.data["property_data"]:
                                self.data["property_data"]["baths"] = text
                            elif 'sqft' in text or 'sq ft' in text:
                                self.data["property_data"]["sqft"] = text
                            elif 'built' in text or 'year' in text:
                                self.data["property_data"]["year_built"] = text
                except:
                    continue

            # Extract photos (first 10)
            photo_selectors = [
                'img[src*="homes.com"]',
                '.property-photo img',
                '.listing-photo img',
                '.gallery img'
            ]

            photos = []
            for selector in photo_selectors:
                try:
                    img_elems = await page.locator(selector).all()
                    for img in img_elems[:10]:  # First 10 photos
                        src = await img.get_attribute('src')
                        if src and 'homes.com' in src and len(src) > 20:
                            photos.append(src)
                            if len(photos) >= 10:
                                break
                    if photos:
                        break
                except:
                    continue

            self.data["property_data"]["photos"] = photos

            # Extract current listing price
            price_selectors = [
                '[data-testid*="price"]',
                '.listing-price',
                '.price',
                'text*="$"',
                '.property-price'
            ]

            for selector in price_selectors:
                try:
                    price_elems = await page.locator(selector).all()
                    for elem in price_elems[:3]:
                        text = await elem.text_content()
                        if text and '$' in text and (',' in text or len(text) > 6):  # Likely price format
                            self.data["property_data"]["price"] = text.strip()
                            break
                except:
                    continue

            # Extract lot size
            lot_selectors = [
                '[data-testid*="lot"]',
                'text*="acre"',
                'text*="Lot"',
                '.lot-size'
            ]

            for selector in lot_selectors:
                try:
                    lot_elems = await page.locator(selector).all()
                    for elem in lot_elems[:3]:
                        text = await elem.text_content()
                        if text and ('acre' in text.lower() or 'lot' in text.lower()):
                            self.data["property_data"]["lot_size"] = text.strip()
                            break
                except:
                    continue

            # Extract property type
            type_selectors = [
                '[data-testid*="property-type"]',
                '.property-type',
                'text*="Single Family"',
                'text*="Condo"',
                'text*="Townhouse"'
            ]

            for selector in type_selectors:
                try:
                    type_elems = await page.locator(selector).all()
                    for elem in type_elems[:3]:
                        text = await elem.text_content()
                        if text and any(ptype in text for ptype in ['Single', 'Condo', 'Town', 'Multi']):
                            self.data["property_data"]["property_type"] = text.strip()
                            break
                except:
                    continue

            # Extract last sold information
            sold_selectors = [
                '[data-testid*="sold"]',
                '.sold-date',
                '.sale-history',
                'text*="Sold"',
                'text*="Last sold"'
            ]

            for selector in sold_selectors:
                try:
                    sold_elems = await page.locator(selector).all()
                    for elem in sold_elems[:3]:
                        text = await elem.text_content()
                        if text and 'sold' in text.lower():
                            if '$' in text:
                                self.data["property_data"]["last_sold_price"] = text.strip()
                            elif any(char.isdigit() for char in text) and ('/' in text or '-' in text):
                                self.data["property_data"]["last_sold_date"] = text.strip()
                            break
                except:
                    continue

            # Extract homes.com AVM estimate (their proprietary estimate)
            avm_selectors = [
                '[data-testid*="estimate"]',
                '[data-testid*="value"]',
                '.property-value',
                '.estimate-value',
                '.avm-estimate',
                'text*="Estimate"'
            ]

            for selector in avm_selectors:
                try:
                    avm_elems = await page.locator(selector).all()
                    for elem in avm_elems[:5]:
                        text = await elem.text_content()
                        if text and '$' in text and ('estimate' in text.lower() or 'value' in text.lower()):
                            self.data["property_data"]["homes_estimate"] = text.strip()
                            break
                    if "homes_estimate" in self.data["property_data"]:
                        break
                except:
                    continue

            # Extract AVM range (if homes.com provides estimate ranges)
            range_selectors = [
                '[data-testid*="range"]',
                '.estimate-range',
                '.value-range',
                'text*="Range"',
                'text*=" - $"'
            ]

            for selector in range_selectors:
                try:
                    range_elems = await page.locator(selector).all()
                    for elem in range_elems[:3]:
                        text = await elem.text_content()
                        if text and '$' in text and ('-' in text or 'range' in text.lower()):
                            self.data["property_data"]["avm_range"] = text.strip()
                            break
                    if "avm_range" in self.data["property_data"]:
                        break
                except:
                    continue

            # Validate extraction success BEFORE marking as found
            extracted_count = len([v for v in self.data["property_data"].values() if v])  # Count non-empty values

            await self.log_step("EXTRACT_COMPLETE", f"Extracted {extracted_count} data fields with values", page)

            # Only mark as found if we got meaningful data
            if extracted_count >= 3:  # Require at least 3 fields to consider success
                self.data["found"] = True
                print(f"✅ SUCCESS: Extracted {extracted_count} fields")
            else:
                self.data["found"] = False
                self.data["errors"].append(f"Insufficient data extracted: only {extracted_count} fields found")
                print(f"❌ FAILED: Only extracted {extracted_count} fields, need at least 3")

        except Exception as e:
            await self.log_step("EXTRACT_ERROR", f"Property extraction error: {str(e)}", page)
            self.data["errors"].append(f"Property extraction error: {str(e)}")

    async def run(self):
        """Run debug version"""
        print("🐛 DEBUG MODE - Detailed logging enabled")

        async with async_playwright() as p:
            try:
                # Launch browser with or without proxy based on NO_PROXY flag
                if self.no_proxy:
                    browser = await p.firefox.launch(headless=False)
                else:
                    browser = await p.firefox.launch(
                        headless=False,
                        proxy={
                            'server': self.proxy_server,
                            'username': self.proxy_username,
                            'password': self.proxy_password
                        }
                    )

                context = await browser.new_context(
                    user_agent=self.user_agents[0],
                    ignore_https_errors=True
                )

                page = await context.new_page()
                page.set_default_timeout(30000)

                # Minimal response logging
                async def log_response(response):
                    if 'homes.com' in response.url and not any(ext in response.url for ext in ['.jpg', '.png', '.css']):
                        status_icon = "✅" if response.status < 400 else "❌"
                        print(f"{status_icon} {response.url} - {response.status}")

                page.on("response", log_response)

                # Run the scraping
                await self.scrape_homes_com(page)

                # Save results
                results_file = f"debug_results_{self.timestamp}.json"
                with open(results_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                print(f"\n📊 RESULTS:")
                print(f"   Results file: {results_file}")
                print(f"   Screenshots: {self.screenshots_dir}/")
                print(f"   Success: {self.data['found']}")
                print(f"   Errors: {len(self.data['errors'])}")
                print(f"   Steps completed: {len(self.data['steps_completed'])}")

                # Hold longer to see results
                print(f"\n⏳ Holding browser for 10 seconds to review results...")
                print(f"📊 Data found: {self.data['found']}")
                print(f"📝 Fields extracted: {list(self.data['property_data'].keys()) if self.data['property_data'] else 'None'}")
                await asyncio.sleep(10)

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
        print("Usage: python scrape_property_debug.py '<address>' homes")
        sys.exit(1)

    address = sys.argv[1]
    site = sys.argv[2]

    scraper = PropertyScraper(address, site)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())