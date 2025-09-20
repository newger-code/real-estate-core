#!/usr/bin/env python3
"""
Enhanced Homes.com Scraper with Advanced Anti-Bot Evasion
Implements research-backed strategies for bypassing Homes.com blocks
"""

import asyncio
import random
import json
import time
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from dataclasses import dataclass
from pathlib import Path
import logging

from proxy_config import get_playwright_proxy
from utils.common import setup_logger, take_screenshot, random_delay

@dataclass
class PropertyData:
    """Property data structure"""
    address: str = ""
    beds: str = ""
    baths: str = ""
    sqft: str = ""
    year_built: str = ""
    price: str = ""
    avm_estimate: str = ""
    status: str = ""
    photos: List[str] = None
    school_scores: Dict[str, str] = None
    flood_info: str = ""
    source_site: str = "homes"
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.school_scores is None:
            self.school_scores = {}

class EnhancedHomesScraperConfig:
    """Advanced browser configurations for Homes.com"""
    
    STEALTH_CONFIGS = [
        {
            "name": "Firefox_Residential_Stealth",
            "browser": "firefox",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-US",
            "timezone": "America/New_York",
            "extra_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
        },
        {
            "name": "Chrome_Mobile_Stealth",
            "browser": "chromium",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "viewport": {"width": 375, "height": 812},
            "locale": "en-US",
            "timezone": "America/Los_Angeles",
            "is_mobile": True,
            "extra_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        },
        {
            "name": "Chrome_Desktop_Enhanced",
            "browser": "chromium",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone": "America/Chicago",
            "extra_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
        }
    ]

class EnhancedHomesScraper:
    """Enhanced Homes.com scraper with advanced anti-bot evasion"""
    
    def __init__(self):
        self.logger = setup_logger("enhanced_homes_scraper")
        self.config = EnhancedHomesScraperConfig()
        self.base_url = "https://www.homes.com"
        self.screenshots_dir = Path("logs/screenshots/homes")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_stealth_browser(self, config_name: str = None) -> Tuple[Browser, BrowserContext, Page]:
        """Create a stealth browser with advanced evasion"""
        
        # Select configuration
        if config_name:
            config = next((c for c in self.config.STEALTH_CONFIGS if c["name"] == config_name), 
                         self.config.STEALTH_CONFIGS[0])
        else:
            config = random.choice(self.config.STEALTH_CONFIGS)
            
        self.logger.info(f"Using browser config: {config['name']}")
        
        playwright = await async_playwright().start()
        
        # Browser launch args for stealth
        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions-except=/path/to/extension",
            "--disable-plugins-discovery",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-popup-blocking",
            "--disable-translate",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-sync",
            "--disable-ipc-flooding-protection",
            "--enable-features=NetworkService,NetworkServiceLogging",
            "--force-color-profile=srgb",
            "--metrics-recording-only",
            "--use-mock-keychain",
            "--disable-web-security",
            "--allow-running-insecure-content"
        ]
        
        # Get proxy configuration
        proxy_config = get_playwright_proxy()
        
        # Launch browser
        if config["browser"] == "firefox":
            browser = await playwright.firefox.launch(
                headless=False,  # Start with headful for debugging
                proxy=proxy_config,
                args=["--width=1366", "--height=768"]
            )
        else:
            browser = await playwright.chromium.launch(
                headless=False,
                proxy=proxy_config,
                args=launch_args
            )
        
        # Create context with stealth settings
        context_options = {
            "viewport": config["viewport"],
            "user_agent": config["user_agent"],
            "locale": config["locale"],
            "timezone_id": config["timezone"],
            "extra_http_headers": config["extra_headers"],
            "java_script_enabled": True,
            "accept_downloads": False,
            "ignore_https_errors": True,
            "bypass_csp": True
        }
        
        if config.get("is_mobile"):
            context_options["is_mobile"] = True
            context_options["has_touch"] = True
            
        context = await browser.new_context(**context_options)
        
        # Add stealth scripts
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {},
            };
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
        
        page = await context.new_page()
        
        # Set additional page properties
        await page.evaluate("""
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 4,
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
        """)
        
        return browser, context, page
    
    async def human_like_navigation(self, page: Page, url: str) -> bool:
        """Navigate with human-like behavior"""
        try:
            self.logger.info(f"Navigating to: {url}")
            
            # Random delay before navigation
            await random_delay(2, 5)
            
            # Navigate with timeout
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if not response or response.status >= 400:
                self.logger.error(f"Navigation failed with status: {response.status if response else 'No response'}")
                return False
            
            # Wait for page to stabilize
            await random_delay(3, 6)
            
            # Human-like scrolling
            await self.simulate_human_behavior(page)
            
            # Take screenshot for debugging
            screenshot_path = self.screenshots_dir / f"navigation_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Navigation error: {str(e)}")
            return False
    
    async def simulate_human_behavior(self, page: Page):
        """Simulate human-like interactions"""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await random_delay(0.5, 1.5)
            
            # Random scrolling
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(200, 800)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await random_delay(1, 3)
            
            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await random_delay(1, 2)
            
        except Exception as e:
            self.logger.warning(f"Human behavior simulation error: {str(e)}")
    
    async def search_property(self, page: Page, address: str) -> bool:
        """Search for property with enhanced selectors"""
        try:
            self.logger.info(f"Searching for property: {address}")
            
            # Enhanced search selectors based on research
            search_selectors = [
                'input[placeholder*="Enter an address"]',
                'input[placeholder*="address"]',
                'input[placeholder*="city"]',
                'input[name="searchfield"]',
                'input[name="search"]',
                'input[id*="search"]',
                'input[id*="address"]',
                '#searchfield',
                '#search-input',
                '#address-input',
                '.search-input',
                '.search-field',
                'input[type="text"]',
                'input[type="search"]',
                '[data-testid*="search"]',
                '[data-testid*="address"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0 and await element.is_visible():
                        search_input = element
                        self.logger.info(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                self.logger.error("No search input found")
                return False
            
            # Clear and type address with human-like behavior
            await search_input.click()
            await random_delay(0.5, 1)
            await search_input.clear()
            await random_delay(0.5, 1)
            
            # Type with human-like delays
            for char in address:
                await search_input.type(char)
                await random_delay(0.05, 0.15)
            
            await random_delay(1, 2)
            
            # Try to submit search
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button[aria-label*="Search"]',
                'button[title*="Search"]',
                '.search-button',
                '.search-btn',
                '[data-testid*="search-button"]',
                '[data-testid*="submit"]'
            ]
            
            # Try Enter key first
            await search_input.press("Enter")
            await random_delay(2, 4)
            
            # Check if search was successful
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Take screenshot after search
            screenshot_path = self.screenshots_dir / f"search_results_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            self.logger.info(f"Search screenshot saved: {screenshot_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return False
    
    async def extract_property_data(self, page: Page, address: str) -> PropertyData:
        """Extract property data with enhanced selectors"""
        property_data = PropertyData(address=address)
        
        try:
            self.logger.info("Extracting property data")
            
            # Wait for content to load
            await random_delay(3, 5)
            
            # Enhanced extraction selectors
            extraction_map = {
                "price": [
                    '[data-testid*="price"]',
                    '.price',
                    '.listing-price',
                    '.property-price',
                    '[class*="price"]',
                    'span[class*="Price"]',
                    'div[class*="price"]'
                ],
                "beds": [
                    '[data-testid*="bed"]',
                    '.beds',
                    '.bedroom',
                    '[class*="bed"]',
                    'span[class*="Bed"]'
                ],
                "baths": [
                    '[data-testid*="bath"]',
                    '.baths',
                    '.bathroom',
                    '[class*="bath"]',
                    'span[class*="Bath"]'
                ],
                "sqft": [
                    '[data-testid*="sqft"]',
                    '[data-testid*="square"]',
                    '.sqft',
                    '.square-feet',
                    '[class*="sqft"]',
                    '[class*="square"]'
                ],
                "year_built": [
                    '[data-testid*="year"]',
                    '.year-built',
                    '.built-year',
                    '[class*="year"]'
                ],
                "status": [
                    '[data-testid*="status"]',
                    '.status',
                    '.listing-status',
                    '[class*="status"]'
                ]
            }
            
            # Extract each field
            for field, selectors in extraction_map.items():
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            text = await element.text_content()
                            if text and text.strip():
                                setattr(property_data, field, text.strip())
                                self.logger.info(f"Extracted {field}: {text.strip()}")
                                break
                    except:
                        continue
            
            # Extract photos
            photo_selectors = [
                'img[src*="photo"]',
                'img[src*="image"]',
                '.property-photo img',
                '.listing-photo img',
                '[data-testid*="photo"] img',
                '.gallery img'
            ]
            
            for selector in photo_selectors:
                try:
                    images = page.locator(selector)
                    count = await images.count()
                    for i in range(min(count, 10)):  # Limit to 10 photos
                        src = await images.nth(i).get_attribute("src")
                        if src and src.startswith("http"):
                            property_data.photos.append(src)
                    if property_data.photos:
                        break
                except:
                    continue
            
            # Extract AVM estimate
            avm_selectors = [
                '[data-testid*="estimate"]',
                '[data-testid*="avm"]',
                '.estimate',
                '.avm',
                '.home-value',
                '[class*="estimate"]'
            ]
            
            for selector in avm_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        text = await element.text_content()
                        if text and text.strip():
                            property_data.avm_estimate = text.strip()
                            break
                except:
                    continue
            
            self.logger.info(f"Extraction complete. Found {len([f for f in [property_data.price, property_data.beds, property_data.baths, property_data.sqft] if f])} core fields")
            
        except Exception as e:
            self.logger.error(f"Extraction error: {str(e)}")
        
        return property_data
    
    async def scrape_property(self, address: str, config_name: str = None) -> Optional[PropertyData]:
        """Main scraping method"""
        browser = None
        try:
            self.logger.info(f"Starting enhanced scrape for: {address}")
            
            # Create stealth browser
            browser, context, page = await self.create_stealth_browser(config_name)
            
            # Navigate to homepage
            if not await self.human_like_navigation(page, self.base_url):
                return None
            
            # Check for access denied or blocks
            page_content = await page.content()
            if any(block_indicator in page_content.lower() for block_indicator in 
                   ["access denied", "blocked", "captcha", "cloudflare", "403 forbidden"]):
                self.logger.error("Site blocked access - detected blocking page")
                return None
            
            # Search for property
            if not await self.search_property(page, address):
                return None
            
            # Extract property data
            property_data = await self.extract_property_data(page, address)
            
            # Take final screenshot
            screenshot_path = self.screenshots_dir / f"final_extraction_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"Scraping error: {str(e)}")
            return None
        finally:
            if browser:
                await browser.close()

async def test_enhanced_homes_scraper():
    """Test the enhanced scraper"""
    scraper = EnhancedHomesScraper()
    
    test_addresses = [
        "1841 Marks Ave, Akron, OH 44305",
        "1754 Hampton Rd, Akron, OH 44305"
    ]
    
    results = []
    
    for address in test_addresses:
        print(f"\n{'='*60}")
        print(f"Testing Enhanced Homes.com Scraper")
        print(f"Address: {address}")
        print(f"{'='*60}")
        
        # Try different configurations
        for config_name in ["Firefox_Residential_Stealth", "Chrome_Desktop_Enhanced"]:
            print(f"\nTrying configuration: {config_name}")
            
            result = await scraper.scrape_property(address, config_name)
            
            if result:
                print(f"✅ SUCCESS with {config_name}")
                print(f"Price: {result.price}")
                print(f"Beds: {result.beds}")
                print(f"Baths: {result.baths}")
                print(f"Sqft: {result.sqft}")
                print(f"Photos: {len(result.photos)}")
                
                # Save result
                result_file = Path(f"data/homes_{address.replace(' ', '_').replace(',', '')}.json")
                result_file.parent.mkdir(exist_ok=True)
                
                result_dict = {
                    "address": result.address,
                    "price": result.price,
                    "beds": result.beds,
                    "baths": result.baths,
                    "sqft": result.sqft,
                    "year_built": result.year_built,
                    "avm_estimate": result.avm_estimate,
                    "status": result.status,
                    "photos": result.photos,
                    "school_scores": result.school_scores,
                    "flood_info": result.flood_info,
                    "source_site": result.source_site,
                    "extraction_timestamp": time.time(),
                    "config_used": config_name
                }
                
                with open(result_file, 'w') as f:
                    json.dump(result_dict, f, indent=2)
                
                print(f"Result saved to: {result_file}")
                results.append(result_dict)
                break
            else:
                print(f"❌ FAILED with {config_name}")
        
        # Add delay between addresses
        await asyncio.sleep(10)
    
    print(f"\n{'='*60}")
    print(f"ENHANCED HOMES.COM SCRAPER TEST COMPLETE")
    print(f"Successful extractions: {len(results)}")
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_enhanced_homes_scraper())
