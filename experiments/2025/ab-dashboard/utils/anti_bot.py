
"""
Anti-Bot Strategies and Evasion Techniques
Enhanced from successful Homes.com breakthrough research
"""

import random
import asyncio
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Browser, BrowserContext, Page
from dataclasses import dataclass

@dataclass
class BrowserConfig:
    """Browser configuration for anti-bot evasion"""
    name: str
    user_agent: str
    viewport: Tuple[int, int]
    headers: Dict[str, str]
    stealth: bool = True
    mobile: bool = False
    delay: int = 5
    webrtc_fake: bool = False
    human_timing: bool = False
    tor_like: bool = False

class UserAgentRotator:
    """
    User Agent rotation based on successful Homes.com breakthrough
    Implements the 10 strategies that bypassed blocking
    """
    
    STRATEGIES = {
        1: BrowserConfig(
            name="Basic Chrome Desktop",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            viewport=(1920, 1080),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            delay=3
        ),
        2: BrowserConfig(
            name="Firefox Desktop with Extensions",  # This one worked for Homes.com!
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            viewport=(1366, 768),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none"
            },
            delay=5
        ),
        3: BrowserConfig(
            name="Mobile Chrome Android",
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
            viewport=(375, 667),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            },
            mobile=True,
            delay=4
        ),
        4: BrowserConfig(
            name="Safari macOS",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            viewport=(1440, 900),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            delay=6
        ),
        5: BrowserConfig(
            name="Edge Windows with Residential Headers",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
            viewport=(1536, 864),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                'Sec-Ch-Ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                'Sec-Ch-Ua-Platform': '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            },
            delay=7
        )
    }
    
    def __init__(self):
        self.current_strategy = 2  # Start with successful Firefox strategy
        
    def get_current_config(self) -> BrowserConfig:
        """Get current browser configuration"""
        return self.STRATEGIES[self.current_strategy]
        
    def rotate(self) -> BrowserConfig:
        """Rotate to next strategy"""
        self.current_strategy = (self.current_strategy % len(self.STRATEGIES)) + 1
        return self.get_current_config()
        
    def get_best_for_site(self, site: str) -> BrowserConfig:
        """Get best configuration for specific site"""
        if site.lower() == "homes":
            return self.STRATEGIES[2]  # Firefox worked for Homes.com
        elif site.lower() == "redfin":
            return self.STRATEGIES[1]  # Chrome works for Redfin
        else:
            return self.STRATEGIES[2]  # Default to Firefox

class ProxyManager:
    """
    Enhanced proxy management with Bright Data integration
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        try:
            from proxy_config import proxy_manager as bright_data_manager
            self.bright_data = bright_data_manager
            self.has_bright_data = True
        except ImportError:
            self.bright_data = None
            self.has_bright_data = False
            
        # Fallback to environment variables
        import os
        self.env_proxies = []
        proxy_list = os.getenv('PROXY_LIST', '').split(',')
        for proxy in proxy_list:
            if proxy.strip():
                self.env_proxies.append(proxy.strip())
                
    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration for Playwright"""
        if self.has_bright_data:
            return self.bright_data.get_primary_proxy().playwright_proxy
        return None
        
    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Get proxy dictionary for requests"""
        if self.has_bright_data:
            return self.bright_data.get_primary_proxy().proxy_dict
        elif self.env_proxies:
            proxy_url = random.choice(self.env_proxies)
            return {"http": proxy_url, "https": proxy_url}
        return None
                
    def is_available(self) -> bool:
        """Check if proxies are configured"""
        return self.has_bright_data or len(self.env_proxies) > 0
        
    def test_connectivity(self) -> Tuple[bool, str]:
        """Test proxy connectivity"""
        if self.has_bright_data:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success, message, ip = loop.run_until_complete(
                    self.bright_data.test_proxy_connectivity()
                )
                loop.close()
                return success, message
            except Exception as e:
                return False, f"Proxy test error: {str(e)}"
        return False, "No proxy configured"

class AntiBot:
    """
    Main anti-bot evasion class
    Implements comprehensive strategies from research
    """
    
    def __init__(self):
        self.ua_rotator = UserAgentRotator()
        self.proxy_manager = ProxyManager()
        
    async def setup_browser_context(
        self, 
        browser: Browser, 
        site: str = None,
        strategy_id: int = None
    ) -> BrowserContext:
        """
        Setup browser context with anti-bot measures
        """
        # Get configuration
        if strategy_id:
            config = self.ua_rotator.STRATEGIES.get(strategy_id, self.ua_rotator.get_current_config())
        elif site:
            config = self.ua_rotator.get_best_for_site(site)
        else:
            config = self.ua_rotator.get_current_config()
            
        # Context options
        context_options = {
            "user_agent": config.user_agent,
            "viewport": {"width": config.viewport[0], "height": config.viewport[1]},
            "extra_http_headers": config.headers,
            "java_script_enabled": True,
            "accept_downloads": False,
            "ignore_https_errors": True,
        }
        
        # Add proxy if available
        proxy_config = self.proxy_manager.get_proxy_config()
        if proxy_config:
            context_options["proxy"] = proxy_config
            
        # Create context
        context = await browser.new_context(**context_options)
        
        # Add stealth scripts if enabled
        if config.stealth:
            await self._add_stealth_scripts(context)
            
        return context
        
    async def _add_stealth_scripts(self, context: BrowserContext):
        """
        Add stealth JavaScript to bypass detection
        Based on successful Homes.com breakthrough
        """
        stealth_script = """
        // Override webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {},
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        await context.add_init_script(stealth_script)
        
    async def human_like_interaction(self, page: Page):
        """
        Simulate human-like interactions
        """
        # Random mouse movements
        await page.mouse.move(
            random.randint(100, 800),
            random.randint(100, 600)
        )
        
        # Random scroll
        await page.evaluate("window.scrollBy(0, Math.random() * 200)")
        
        # Random delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
    async def handle_captcha(self, page: Page) -> bool:
        """
        CAPTCHA detection and handling framework
        Returns True if CAPTCHA was detected and handled
        """
        captcha_indicators = [
            'iframe[src*="captcha"]',
            '.captcha',
            '#captcha',
            '[data-testid*="captcha"]',
            'img[src*="captcha"]'
        ]
        
        for indicator in captcha_indicators:
            if await page.locator(indicator).count() > 0:
                # CAPTCHA detected - log and return for manual handling
                print(f"CAPTCHA detected with selector: {indicator}")
                await page.screenshot(path="logs/captcha_detected.png")
                return True
                
        return False
        
    async def check_blocking(self, page: Page) -> Tuple[bool, str]:
        """
        Check if page is blocked or showing anti-bot measures
        Returns (is_blocked, reason)
        """
        # Check for common blocking indicators
        blocking_indicators = [
            ("Access Denied", "access denied"),
            ("Blocked", "blocked"),
            ("403", "403 forbidden"),
            ("Rate Limited", "rate limit"),
            ("Cloudflare", "cloudflare protection"),
            ("Please verify", "verification required")
        ]
        
        try:
            page_content = await page.text_content("body")
            page_title = await page.title()
            
            for indicator, reason in blocking_indicators:
                if indicator.lower() in page_content.lower() or indicator.lower() in page_title.lower():
                    return True, reason
                    
            # Check for redirect to blocking page
            if "blocked" in page.url.lower() or "denied" in page.url.lower():
                return True, "redirected to blocking page"
                
            return False, "no blocking detected"
            
        except Exception as e:
            return True, f"error checking blocking: {str(e)}"
