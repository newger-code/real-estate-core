#!/usr/bin/env python3
"""
Enhanced Movoto.com Scraper with Press-and-Hold Challenge Bypass
Implements advanced anti-bot evasion and challenge solving
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
    source_site: str = "movoto"
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.school_scores is None:
            self.school_scores = {}

class EnhancedMovotoScraperConfig:
    """Advanced browser configurations for Movoto.com"""
    
    STEALTH_CONFIGS = [
        {
            "name": "Chrome_Residential_Ultra_Stealth",
            "browser": "chromium",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone": "America/New_York",
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
        },
        {
            "name": "Firefox_Anti_Detection",
            "browser": "firefox",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-US",
            "timezone": "America/Chicago",
            "extra_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        }
    ]

class EnhancedMovotoScraper:
    """Enhanced Movoto.com scraper with press-and-hold challenge bypass"""
    
    def __init__(self):
        self.logger = setup_logger("enhanced_movoto_scraper")
        self.config = EnhancedMovotoScraperConfig()
        self.base_url = "https://www.movoto.com"
        self.screenshots_dir = Path("logs/screenshots/movoto")
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
        
        # Advanced Chrome launch args for maximum stealth
        chrome_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
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
            "--allow-running-insecure-content",
            "--disable-component-extensions-with-background-pages",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-domain-reliability",
            "--disable-features=TranslateUI",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-background-downloads",
            "--disable-add-to-shelf",
            "--disable-client-side-phishing-detection",
            "--disable-datasaver-prompt",
            "--disable-desktop-notifications",
            "--disable-domain-reliability"
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
                args=chrome_args
            )
        
        # Create context with maximum stealth
        context_options = {
            "viewport": config["viewport"],
            "user_agent": config["user_agent"],
            "locale": config["locale"],
            "timezone_id": config["timezone"],
            "extra_http_headers": config["extra_headers"],
            "java_script_enabled": True,
            "accept_downloads": False,
            "ignore_https_errors": True,
            "bypass_csp": True,
            "permissions": ["geolocation", "notifications"]
        }
            
        context = await browser.new_context(**context_options)
        
        # Advanced stealth scripts
        await context.add_init_script("""
            // Remove webdriver property completely
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override the plugins property to use a custom getter.
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override the languages property to use a custom getter.
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override the permissions property
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {
                    return {
                        commitLoadTime: 1484781665.637,
                        connectionInfo: 'http/1.1',
                        finishDocumentLoadTime: 1484781665.842,
                        finishLoadTime: 1484781665.842,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: 1484781665.849,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'unknown',
                        requestTime: 1484781665.637,
                        startLoadTime: 1484781665.637,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    };
                },
                csi: function() {
                    return {
                        onloadT: 1484781665842,
                        pageT: 205.94499999999138,
                        startE: 1484781665637,
                        tran: 15
                    };
                }
            };
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
            
            // Mock hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 4,
            });
            
            // Mock device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    downlink: 10,
                    effectiveType: '4g',
                    rtt: 50,
                    saveData: false
                }),
            });
        """)
        
        page = await context.new_page()
        
        # Additional page-level stealth
        await page.evaluate("""
            // Override the Date.getTimezoneOffset method
            Date.prototype.getTimezoneOffset = function() {
                return -300; // EST timezone
            };
            
            // Mock screen properties
            Object.defineProperty(screen, 'availHeight', {
                get: () => 1040,
            });
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1920,
            });
            Object.defineProperty(screen, 'colorDepth', {
                get: () => 24,
            });
            Object.defineProperty(screen, 'height', {
                get: () => 1080,
            });
            Object.defineProperty(screen, 'pixelDepth', {
                get: () => 24,
            });
            Object.defineProperty(screen, 'width', {
                get: () => 1920,
            });
        """)
        
        return browser, context, page
    
    async def detect_and_solve_press_hold_challenge(self, page: Page) -> bool:
        """Detect and solve press-and-hold challenges"""
        try:
            self.logger.info("Checking for press-and-hold challenges")
            
            # Common press-and-hold challenge selectors
            challenge_selectors = [
                'button[data-callback*="press"]',
                'button[data-callback*="hold"]',
                'button[aria-label*="press"]',
                'button[aria-label*="hold"]',
                'div[class*="press"]',
                'div[class*="hold"]',
                'button[class*="challenge"]',
                'div[class*="challenge"]',
                '[data-testid*="challenge"]',
                '[data-testid*="press"]',
                '[data-testid*="hold"]',
                'button:has-text("Press")',
                'button:has-text("Hold")',
                'div:has-text("Press and hold")',
                'div:has-text("Hold down")',
                '.human-challenge',
                '.press-hold',
                '.verification-button'
            ]
            
            challenge_element = None
            challenge_selector = None
            
            # Look for challenge elements
            for selector in challenge_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0 and await element.is_visible():
                        challenge_element = element
                        challenge_selector = selector
                        self.logger.info(f"Found press-and-hold challenge: {selector}")
                        break
                except:
                    continue
            
            if not challenge_element:
                # Check page content for challenge text
                page_content = await page.content()
                challenge_keywords = [
                    "press and hold",
                    "hold down",
                    "press to continue",
                    "human verification",
                    "verify you are human",
                    "challenge"
                ]
                
                if any(keyword in page_content.lower() for keyword in challenge_keywords):
                    self.logger.info("Challenge detected in page content, looking for interactive elements")
                    
                    # Look for any button or clickable element
                    generic_selectors = [
                        'button',
                        'input[type="button"]',
                        'input[type="submit"]',
                        'div[role="button"]',
                        '[onclick]'
                    ]
                    
                    for selector in generic_selectors:
                        try:
                            elements = page.locator(selector)
                            count = await elements.count()
                            for i in range(count):
                                element = elements.nth(i)
                                if await element.is_visible():
                                    text = await element.text_content()
                                    if text and any(keyword in text.lower() for keyword in ["press", "hold", "verify", "continue"]):
                                        challenge_element = element
                                        challenge_selector = f"{selector}:nth({i})"
                                        self.logger.info(f"Found challenge button: {text}")
                                        break
                        except:
                            continue
                        if challenge_element:
                            break
                
                if not challenge_element:
                    self.logger.info("No press-and-hold challenge detected")
                    return True
            
            # Solve the challenge
            if challenge_element:
                await self.solve_press_hold_challenge(page, challenge_element, challenge_selector)
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Challenge detection error: {str(e)}")
            return False
    
    async def solve_press_hold_challenge(self, page: Page, element, selector: str):
        """Solve press-and-hold challenge with human-like behavior"""
        try:
            self.logger.info(f"Solving press-and-hold challenge: {selector}")
            
            # Take screenshot before challenge
            screenshot_path = self.screenshots_dir / f"challenge_before_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            
            # Get element position for precise interaction
            box = await element.bounding_box()
            if box:
                center_x = box['x'] + box['width'] / 2
                center_y = box['y'] + box['height'] / 2
                
                # Move mouse to element with human-like path
                await self.human_like_mouse_movement(page, center_x, center_y)
                
                # Press and hold with realistic timing
                await page.mouse.down()
                self.logger.info("Mouse down - starting hold")
                
                # Hold for realistic duration (3-7 seconds)
                hold_duration = random.uniform(3.0, 7.0)
                self.logger.info(f"Holding for {hold_duration:.2f} seconds")
                
                # Add micro-movements during hold to simulate human tremor
                start_time = time.time()
                while time.time() - start_time < hold_duration:
                    # Small random movements (1-2 pixels)
                    offset_x = random.uniform(-2, 2)
                    offset_y = random.uniform(-2, 2)
                    await page.mouse.move(center_x + offset_x, center_y + offset_y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Release mouse
                await page.mouse.up()
                self.logger.info("Mouse up - challenge completed")
                
            else:
                # Fallback: click and hold using element methods
                await element.hover()
                await random_delay(0.5, 1)
                await element.click()
                await asyncio.sleep(random.uniform(3.0, 7.0))
            
            # Wait for challenge to process
            await random_delay(2, 4)
            
            # Take screenshot after challenge
            screenshot_path = self.screenshots_dir / f"challenge_after_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            
            # Check if challenge was solved
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            self.logger.info("Press-and-hold challenge solved")
            
        except Exception as e:
            self.logger.error(f"Challenge solving error: {str(e)}")
    
    async def human_like_mouse_movement(self, page: Page, target_x: float, target_y: float):
        """Move mouse in human-like curved path"""
        try:
            # Get current mouse position (start from random position)
            start_x = random.uniform(100, 500)
            start_y = random.uniform(100, 400)
            
            # Calculate path with curve
            steps = random.randint(15, 25)
            
            for i in range(steps):
                progress = i / steps
                
                # Add curve to the movement
                curve_offset_x = 50 * math.sin(progress * math.pi)
                curve_offset_y = 20 * math.sin(progress * math.pi * 2)
                
                current_x = start_x + (target_x - start_x) * progress + curve_offset_x
                current_y = start_y + (target_y - start_y) * progress + curve_offset_y
                
                await page.mouse.move(current_x, current_y)
                await asyncio.sleep(random.uniform(0.01, 0.03))
                
        except Exception as e:
            self.logger.warning(f"Mouse movement error: {str(e)}")
            # Fallback to direct movement
            await page.mouse.move(target_x, target_y)
    
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
            
            # Check for and solve challenges
            if not await self.detect_and_solve_press_hold_challenge(page):
                return False
            
            # Human-like scrolling after challenge
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
            for _ in range(random.randint(3, 6)):
                x = random.randint(100, 1200)
                y = random.randint(100, 800)
                await page.mouse.move(x, y)
                await random_delay(0.5, 1.5)
            
            # Random scrolling with realistic patterns
            for _ in range(random.randint(3, 7)):
                scroll_amount = random.randint(200, 600)
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
            
            # Enhanced search selectors for Movoto
            search_selectors = [
                'input[placeholder*="Enter address"]',
                'input[placeholder*="address"]',
                'input[placeholder*="city"]',
                'input[placeholder*="location"]',
                'input[name="search"]',
                'input[name="query"]',
                'input[id*="search"]',
                'input[id*="address"]',
                '#search-input',
                '#address-input',
                '.search-input',
                '.search-field',
                '.search-box input',
                'input[type="text"]',
                'input[type="search"]',
                '[data-testid*="search"]',
                '[data-testid*="address"]',
                '[aria-label*="search"]',
                '[aria-label*="address"]'
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
            
            # Type with human-like delays and occasional typos
            for i, char in enumerate(address):
                # Occasional typo simulation
                if random.random() < 0.02:  # 2% chance of typo
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await search_input.type(wrong_char)
                    await random_delay(0.1, 0.3)
                    await search_input.press('Backspace')
                    await random_delay(0.1, 0.2)
                
                await search_input.type(char)
                await random_delay(0.05, 0.2)
            
            await random_delay(1, 2)
            
            # Try to submit search
            await search_input.press("Enter")
            await random_delay(3, 5)
            
            # Check if search was successful
            await page.wait_for_load_state("networkidle", timeout=15000)
            
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
            
            # Enhanced extraction selectors for Movoto
            extraction_map = {
                "price": [
                    '[data-testid*="price"]',
                    '.price',
                    '.listing-price',
                    '.property-price',
                    '.home-price',
                    '[class*="price"]',
                    'span[class*="Price"]',
                    'div[class*="price"]',
                    '.price-display'
                ],
                "beds": [
                    '[data-testid*="bed"]',
                    '.beds',
                    '.bedroom',
                    '.bed-count',
                    '[class*="bed"]',
                    'span[class*="Bed"]',
                    '.property-beds'
                ],
                "baths": [
                    '[data-testid*="bath"]',
                    '.baths',
                    '.bathroom',
                    '.bath-count',
                    '[class*="bath"]',
                    'span[class*="Bath"]',
                    '.property-baths'
                ],
                "sqft": [
                    '[data-testid*="sqft"]',
                    '[data-testid*="square"]',
                    '.sqft',
                    '.square-feet',
                    '.sq-ft',
                    '[class*="sqft"]',
                    '[class*="square"]',
                    '.property-sqft'
                ],
                "year_built": [
                    '[data-testid*="year"]',
                    '.year-built',
                    '.built-year',
                    '.construction-year',
                    '[class*="year"]',
                    '.property-year'
                ],
                "status": [
                    '[data-testid*="status"]',
                    '.status',
                    '.listing-status',
                    '.property-status',
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
                'img[src*="listing"]',
                '.property-photo img',
                '.listing-photo img',
                '.gallery img',
                '[data-testid*="photo"] img',
                '.image-gallery img'
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
                '.property-value',
                '.estimated-value',
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
            self.logger.info(f"Starting enhanced Movoto scrape for: {address}")
            
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

# Add missing import
import math

async def test_enhanced_movoto_scraper():
    """Test the enhanced scraper"""
    scraper = EnhancedMovotoScraper()
    
    test_addresses = [
        "1841 Marks Ave, Akron, OH 44305",
        "1754 Hampton Rd, Akron, OH 44305"
    ]
    
    results = []
    
    for address in test_addresses:
        print(f"\n{'='*60}")
        print(f"Testing Enhanced Movoto.com Scraper")
        print(f"Address: {address}")
        print(f"{'='*60}")
        
        # Try different configurations
        for config_name in ["Chrome_Residential_Ultra_Stealth", "Firefox_Anti_Detection"]:
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
                result_file = Path(f"data/movoto_{address.replace(' ', '_').replace(',', '')}.json")
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
    print(f"ENHANCED MOVOTO.COM SCRAPER TEST COMPLETE")
    print(f"Successful extractions: {len(results)}")
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_enhanced_movoto_scraper())
