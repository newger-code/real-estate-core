
"""
Common utilities extracted and enhanced from working Redfin scraper
Provides logging, screenshot management, and timing utilities
"""

import os
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.async_api import Page

def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Setup structured logging with file and console output
    Enhanced from original Redfin implementation
    """
    # Create logs directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(f"{log_dir}/{name}_{timestamp}.log")
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

async def take_screenshot(
    page: Page, 
    step: str, 
    site: str, 
    timestamp: str,
    screenshots_dir: str = "logs/screenshots"
) -> str:
    """
    Enhanced screenshot utility from Redfin scraper
    Organizes screenshots by site and timestamp for better debugging
    """
    # Create organized directory structure
    screenshot_dir = Path(screenshots_dir) / site / timestamp
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{step.lower().replace(' ', '_')}.png"
    screenshot_path = screenshot_dir / filename
    
    try:
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    except Exception as e:
        # Fallback to basic screenshot
        fallback_path = screenshot_dir / f"error_{filename}"
        try:
            await page.screenshot(path=str(fallback_path))
            return str(fallback_path)
        except:
            return f"Screenshot failed: {str(e)}"

async def random_delay(min_seconds: float = 2.0, max_seconds: float = 10.0) -> None:
    """
    Human-like random delays for anti-bot evasion
    Enhanced with configurable ranges
    """
    import random
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)

def sanitize_address(address: str) -> str:
    """
    Sanitize address for URL construction and file naming
    """
    import re
    # Remove special characters, keep alphanumeric and basic punctuation
    sanitized = re.sub(r'[^\w\s\-\.,]', '', address)
    # Replace spaces with hyphens for URLs
    return sanitized.strip()

def extract_numeric_value(text: str) -> Optional[float]:
    """
    Extract numeric values from text (e.g., "$141,280" -> 141280.0)
    Useful for price, sqft, year extraction
    """
    import re
    if not text:
        return None
    
    # Remove currency symbols and commas, extract numbers
    numbers = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return None
    return None

class StepTracker:
    """
    Track scraping steps for debugging and validation
    Enhanced from original Redfin step logging
    """
    
    def __init__(self, site: str, address: str):
        self.site = site
        self.address = address
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.steps = []
        self.errors = []
        self.screenshots = []
        
    def add_step(self, step: str, message: str, screenshot_path: str = None):
        """Add a completed step"""
        step_data = {
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path
        }
        self.steps.append(step_data)
        
    def add_error(self, error: str, step: str = None):
        """Add an error"""
        error_data = {
            "error": error,
            "step": step,
            "timestamp": datetime.now().isoformat()
        }
        self.errors.append(error_data)
        
    def get_summary(self) -> dict:
        """Get summary of all steps and errors"""
        return {
            "site": self.site,
            "address": self.address,
            "timestamp": self.timestamp,
            "total_steps": len(self.steps),
            "total_errors": len(self.errors),
            "steps": self.steps,
            "errors": self.errors,
            "success": len(self.errors) == 0
        }
