
"""
Navigator Agent - Multi-Site Real Estate Navigation
Handles browsing, anti-bot evasion, and navigation flow
Enhanced from working Redfin implementation with Homes.com breakthrough
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Browser, BrowserContext, Page
from dataclasses import dataclass

from utils.common import setup_logger, take_screenshot, random_delay, StepTracker
from utils.anti_bot import AntiBot

@dataclass
class NavigationResult:
    """Result of navigation attempt"""
    success: bool
    property_url: Optional[str] = None
    error_message: Optional[str] = None
    screenshots: List[str] = None
    steps_completed: List[str] = None
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.steps_completed is None:
            self.steps_completed = []

class Navigator(ABC):
    """
    Abstract base class for site-specific navigators
    Implements common navigation patterns with anti-bot evasion
    """
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.logger = setup_logger(f"navigator_{site_name}")
        self.anti_bot = AntiBot()
        self.step_tracker = None
        
    @abstractmethod
    async def get_base_url(self) -> str:
        """Get base URL for the site"""
        pass
        
    @abstractmethod
    async def get_search_selectors(self) -> List[str]:
        """Get list of search input selectors to try"""
        pass
        
    @abstractmethod
    async def get_result_selectors(self) -> List[str]:
        """Get list of search result selectors to try"""
        pass
        
    @abstractmethod
    async def handle_search_results(self, page: Page, address: str) -> Optional[str]:
        """Handle search results and return property URL"""
        pass
        
    async def navigate_to_property(
        self, 
        browser: Browser, 
        address: str,
        strategy_id: int = None
    ) -> NavigationResult:
        """
        Main navigation method - navigate from homepage to property page
        """
        self.step_tracker = StepTracker(self.site_name, address)
        context = None
        
        try:
            # Setup browser context with anti-bot measures
            context = await self.anti_bot.setup_browser_context(
                browser, 
                site=self.site_name,
                strategy_id=strategy_id
            )
            
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            # Step 1: Navigate to homepage
            base_url = await self.get_base_url()
            await self._log_step(page, "STEP_1_INITIAL_LOAD", f"Loading {self.site_name} homepage")
            
            await page.goto(base_url, wait_until="networkidle")
            await random_delay(2, 5)
            
            # Check for blocking
            is_blocked, block_reason = await self.anti_bot.check_blocking(page)
            if is_blocked:
                error_msg = f"Site blocked access: {block_reason}"
                self.step_tracker.add_error(error_msg, "STEP_1_INITIAL_LOAD")
                return NavigationResult(
                    success=False,
                    error_message=error_msg,
                    screenshots=self.step_tracker.screenshots,
                    steps_completed=[s["step"] for s in self.step_tracker.steps]
                )
            
            await self._log_step(page, "STEP_1_LOADED", f"{self.site_name} homepage loaded successfully")
            
            # Step 2: Find and interact with search
            search_url = await self._perform_search(page, address)
            if not search_url:
                error_msg = "Failed to perform search or find results"
                return NavigationResult(
                    success=False,
                    error_message=error_msg,
                    screenshots=self.step_tracker.screenshots,
                    steps_completed=[s["step"] for s in self.step_tracker.steps]
                )
            
            # Step 3: Navigate to property page if needed
            if search_url != page.url:
                await self._log_step(page, "STEP_3_NAVIGATE_PROPERTY", f"Navigating to property page")
                await page.goto(search_url, wait_until="networkidle")
                await random_delay(2, 4)
                await self._log_step(page, "STEP_3_PROPERTY_LOADED", "Property page loaded")
            
            # Add human-like interaction
            await self.anti_bot.human_like_interaction(page)
            
            return NavigationResult(
                success=True,
                property_url=page.url,
                screenshots=self.step_tracker.screenshots,
                steps_completed=[s["step"] for s in self.step_tracker.steps]
            )
            
        except Exception as e:
            error_msg = f"Navigation error: {str(e)}"
            self.logger.error(error_msg)
            if self.step_tracker:
                self.step_tracker.add_error(error_msg)
            
            return NavigationResult(
                success=False,
                error_message=error_msg,
                screenshots=self.step_tracker.screenshots if self.step_tracker else [],
                steps_completed=[s["step"] for s in self.step_tracker.steps] if self.step_tracker else []
            )
            
        finally:
            if context:
                await context.close()
    
    async def _perform_search(self, page: Page, address: str) -> Optional[str]:
        """Perform search and return property URL"""
        
        # Step 2A: Find search input
        await self._log_step(page, "STEP_2_SEARCH_START", "Looking for search input")
        
        search_selectors = await self.get_search_selectors()
        search_input = None
        
        for selector in search_selectors:
            try:
                search_input = await page.wait_for_selector(selector, timeout=3000)
                if search_input:
                    await self._log_step(page, "STEP_2_SEARCH_FOUND", f"Found search input: {selector}")
                    break
            except:
                continue
        
        if not search_input:
            await self._log_step(page, "STEP_2_SEARCH_FAILED", "Could not find search input")
            self.step_tracker.add_error("Search input not found")
            return None
        
        # Step 2B: Enter address
        await self._log_step(page, "STEP_2_ENTER_ADDRESS", f"Entering address: {address}")
        await search_input.fill(address)
        await random_delay(1, 2)
        await self._log_step(page, "STEP_2_ADDRESS_ENTERED", "Address entered")
        
        # Step 2C: Submit search
        await self._log_step(page, "STEP_2_SUBMIT_SEARCH", "Submitting search")
        await page.keyboard.press("Enter")
        await random_delay(3, 7)  # Wait for results
        await self._log_step(page, "STEP_2_SEARCH_SUBMITTED", "Search submitted")
        
        # Step 2D: Handle results
        return await self.handle_search_results(page, address)
    
    async def _log_step(self, page: Page, step: str, message: str):
        """Log step with screenshot"""
        self.logger.info(f"[{step}] {message}")
        
        screenshot_path = await take_screenshot(
            page, step, self.site_name, self.step_tracker.timestamp
        )
        
        self.step_tracker.add_step(step, message, screenshot_path)

class RedfinNavigator(Navigator):
    """
    Redfin-specific navigator
    Based on working implementation from comprehensive test
    """
    
    def __init__(self):
        super().__init__("redfin")
    
    async def get_base_url(self) -> str:
        return "https://www.redfin.com"
    
    async def get_search_selectors(self) -> List[str]:
        return [
            'input[placeholder*="Enter an Address"]',
            'input[placeholder*="address"]',
            '#search-box-input',
            '.search-input-box',
            'input[data-rf-test-id="search-box-input"]'
        ]
    
    async def get_result_selectors(self) -> List[str]:
        return [
            '.SearchResultsList .result',
            '.search-result-item',
            '[data-rf-test-id="search-result"]'
        ]
    
    async def handle_search_results(self, page: Page, address: str) -> Optional[str]:
        """Handle Redfin search results"""
        await self._log_step(page, "STEP_2_RESULTS_CHECK", "Checking for search results")
        
        # Check if we landed directly on property page
        if "/home/" in page.url:
            await self._log_step(page, "STEP_2_DIRECT_PROPERTY", "Landed directly on property page")
            return page.url
        
        # Look for search results
        result_selectors = await self.get_result_selectors()
        
        for selector in result_selectors:
            try:
                results = await page.locator(selector).count()
                if results > 0:
                    await self._log_step(page, "STEP_2_RESULTS_FOUND", f"Found {results} results with: {selector}")
                    
                    # Click first result
                    await page.locator(selector).first.click()
                    await random_delay(2, 4)
                    await self._log_step(page, "STEP_2_CLICKED_RESULT", "Clicked first search result")
                    
                    return page.url
            except:
                continue
        
        await self._log_step(page, "STEP_2_NO_RESULTS", "No search results found")
        self.step_tracker.add_error("No search results found")
        return None

class HomesNavigator(Navigator):
    """
    Homes.com navigator with breakthrough anti-bot strategy
    Uses successful Firefox configuration from research
    """
    
    def __init__(self):
        super().__init__("homes")
    
    async def get_base_url(self) -> str:
        return "https://www.homes.com"
    
    async def get_search_selectors(self) -> List[str]:
        return [
            'input[placeholder*="Enter an address"]',
            'input[placeholder*="address"]',
            'input[name="searchfield"]',
            'input[id*="search"]',
            '#searchfield',
            '.search-input',
            'input[type="text"]'
        ]
    
    async def get_result_selectors(self) -> List[str]:
        return [
            '.search-result',
            '.property-card',
            '.listing-card',
            '[data-testid="property-card"]',
            '.property-item'
        ]
    
    async def handle_search_results(self, page: Page, address: str) -> Optional[str]:
        """Handle Homes.com search results with property page detection"""
        await self._log_step(page, "STEP_2_RESULTS_CHECK", "Checking for search results")
        
        # Check if we're already on a property page
        property_indicators = [
            '.property-details',
            '.property-info',
            '[data-testid="property-details"]',
            '.listing-details',
            'h1[data-testid="property-address"]'
        ]
        
        for indicator in property_indicators:
            if await page.locator(indicator).count() > 0:
                await self._log_step(page, "STEP_2_DIRECT_PROPERTY", f"Found property page: {indicator}")
                return page.url
        
        # Look for search results
        result_selectors = await self.get_result_selectors()
        
        for selector in result_selectors:
            try:
                results = await page.locator(selector).count()
                if results > 0:
                    await self._log_step(page, "STEP_2_RESULTS_FOUND", f"Found {results} results with: {selector}")
                    
                    # Click first result
                    await page.locator(selector).first.click()
                    await random_delay(2, 4)
                    await self._log_step(page, "STEP_2_CLICKED_RESULT", "Clicked first search result")
                    
                    return page.url
            except:
                continue
        
        # Check for "no results" messages
        try:
            page_content = await page.text_content("body")
            if "no results" in page_content.lower() or "not found" in page_content.lower():
                await self._log_step(page, "STEP_2_NO_RESULTS_MSG", "Found 'no results' message")
                self.step_tracker.add_error("Search returned 'no results' message")
            else:
                await self._log_step(page, "STEP_2_NO_RESULTS", "No search results found")
                self.step_tracker.add_error("No search results found")
        except:
            pass
        
        return None

class MovotoNavigator(Navigator):
    """
    Movoto.com navigator
    Based on basic access proof from uploaded evidence
    """
    
    def __init__(self):
        super().__init__("movoto")
    
    async def get_base_url(self) -> str:
        return "https://www.movoto.com"
    
    async def get_search_selectors(self) -> List[str]:
        return [
            'input[placeholder*="Enter address"]',
            'input[placeholder*="address"]',
            'input[name="search"]',
            '#search-input',
            '.search-box input',
            'input[type="search"]',
            'input[type="text"]'
        ]
    
    async def get_result_selectors(self) -> List[str]:
        return [
            '.property-result',
            '.listing-item',
            '.search-result',
            '.property-card',
            '[data-testid="property"]'
        ]
    
    async def handle_search_results(self, page: Page, address: str) -> Optional[str]:
        """Handle Movoto search results"""
        await self._log_step(page, "STEP_2_RESULTS_CHECK", "Checking for search results")
        
        # Check for direct property page
        if "/property/" in page.url or "/home/" in page.url:
            await self._log_step(page, "STEP_2_DIRECT_PROPERTY", "Landed on property page")
            return page.url
        
        # Look for search results
        result_selectors = await self.get_result_selectors()
        
        for selector in result_selectors:
            try:
                results = await page.locator(selector).count()
                if results > 0:
                    await self._log_step(page, "STEP_2_RESULTS_FOUND", f"Found {results} results with: {selector}")
                    
                    # Click first result
                    await page.locator(selector).first.click()
                    await random_delay(2, 4)
                    await self._log_step(page, "STEP_2_CLICKED_RESULT", "Clicked first search result")
                    
                    return page.url
            except:
                continue
        
        await self._log_step(page, "STEP_2_NO_RESULTS", "No search results found")
        self.step_tracker.add_error("No search results found")
        return None

# Factory function for creating navigators
def create_navigator(site: str) -> Navigator:
    """Create navigator for specific site"""
    site = site.lower()
    
    if site == "redfin":
        return RedfinNavigator()
    elif site == "homes":
        return HomesNavigator()
    elif site == "movoto":
        return MovotoNavigator()
    else:
        raise ValueError(f"Unsupported site: {site}")
