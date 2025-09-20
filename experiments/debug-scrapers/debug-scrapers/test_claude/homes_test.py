
#!/usr/bin/env python3
"""
Homes.com Anti-Bot Testing Script
Tests 10 different strategies to bypass blocking
"""

import asyncio
import yaml
import json
import time
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HomesAntiBot:
    def __init__(self):
        self.base_url = "https://www.homes.com/"
        self.results = []
        self.attempt_dir = Path("attempt_logs")
        self.attempt_dir.mkdir(exist_ok=True)
        
        # Load configuration
        with open("homes_anti_bot_config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
    
    async def test_strategy(self, strategy_id, strategy_config):
        """Test a single anti-bot strategy"""
        strategy_name = strategy_config["name"]
        logger.info(f"Testing Strategy {strategy_id}: {strategy_name}")
        
        result = {
            "strategy_id": strategy_id,
            "strategy_name": strategy_name,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "status_code": None,
            "error": None,
            "response_size": 0,
            "load_time": 0,
            "screenshot_path": None,
            "page_title": None,
            "detected_blocks": []
        }
        
        try:
            async with async_playwright() as p:
                # Choose browser based on user agent
                if "Firefox" in strategy_config["user_agent"]:
                    browser = await p.firefox.launch(headless=True)
                elif "Safari" in strategy_config["user_agent"]:
                    browser = await p.webkit.launch(headless=True)
                else:
                    browser = await p.chromium.launch(headless=True)
                
                # Create context with strategy configuration
                context_options = {
                    "user_agent": strategy_config["user_agent"],
                    "viewport": {
                        "width": strategy_config["viewport"][0],
                        "height": strategy_config["viewport"][1]
                    },
                    "extra_http_headers": strategy_config["headers"]
                }
                
                # Add mobile simulation if specified
                if strategy_config.get("mobile", False):
                    context_options["is_mobile"] = True
                    context_options["has_touch"] = True
                
                context = await browser.new_context(**context_options)
                
                # Add stealth modifications if enabled
                if strategy_config.get("stealth", False):
                    await self.apply_stealth_modifications(context)
                
                page = await context.new_page()
                
                # Add additional stealth measures
                if strategy_config.get("webrtc_fake", False):
                    await self.fake_webrtc(page)
                
                if strategy_config.get("tor_like", False):
                    await self.apply_tor_like_settings(page)
                
                # Navigate with timing
                start_time = time.time()
                
                # Add human-like delay before navigation
                if strategy_config.get("human_timing", False):
                    await asyncio.sleep(random.uniform(2, 5))
                
                try:
                    response = await page.goto(
                        self.base_url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )
                    
                    load_time = time.time() - start_time
                    result["load_time"] = load_time
                    
                    if response:
                        result["status_code"] = response.status
                        
                        # Wait for additional delay as specified
                        await asyncio.sleep(strategy_config.get("delay", 3))
                        
                        # Check for blocking indicators
                        page_content = await page.content()
                        result["response_size"] = len(page_content)
                        
                        # Detect common blocking patterns
                        blocking_indicators = [
                            "access denied",
                            "blocked",
                            "cloudflare",
                            "security check",
                            "bot detection",
                            "captcha",
                            "forbidden",
                            "rate limit"
                        ]
                        
                        content_lower = page_content.lower()
                        for indicator in blocking_indicators:
                            if indicator in content_lower:
                                result["detected_blocks"].append(indicator)
                        
                        # Get page title
                        try:
                            result["page_title"] = await page.title()
                        except:
                            result["page_title"] = "Unable to get title"
                        
                        # Take screenshot
                        screenshot_path = self.attempt_dir / f"strategy_{strategy_id}_screenshot.png"
                        await page.screenshot(path=str(screenshot_path), full_page=True)
                        result["screenshot_path"] = str(screenshot_path)
                        
                        # Check if we successfully reached the site
                        if (response.status == 200 and 
                            len(result["detected_blocks"]) == 0 and
                            "homes.com" in content_lower):
                            result["success"] = True
                            logger.info(f"✅ Strategy {strategy_id} SUCCESS!")
                        else:
                            logger.info(f"❌ Strategy {strategy_id} BLOCKED - Status: {response.status}, Blocks: {result['detected_blocks']}")
                    
                except Exception as nav_error:
                    result["error"] = f"Navigation error: {str(nav_error)}"
                    logger.error(f"Strategy {strategy_id} navigation failed: {nav_error}")
                
                await context.close()
                await browser.close()
                
        except Exception as e:
            result["error"] = f"Browser error: {str(e)}"
            logger.error(f"Strategy {strategy_id} browser error: {e}")
        
        return result
    
    async def apply_stealth_modifications(self, context):
        """Apply stealth modifications to avoid detection"""
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
        """)
    
    async def fake_webrtc(self, page):
        """Fake WebRTC to avoid fingerprinting"""
        await page.add_init_script("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) Iris(TM) Graphics 6100';
                }
                return getParameter.call(this, parameter);
            };
        """)
    
    async def apply_tor_like_settings(self, page):
        """Apply Tor-like privacy settings"""
        await page.add_init_script("""
            // Disable WebRTC
            window.RTCPeerConnection = undefined;
            window.RTCSessionDescription = undefined;
            window.RTCIceCandidate = undefined;
            
            // Spoof timezone
            Date.prototype.getTimezoneOffset = function() {
                return 0;
            };
        """)
    
    async def run_all_tests(self):
        """Run all 10 anti-bot strategies"""
        logger.info("Starting Homes.com Anti-Bot Testing")
        logger.info("=" * 50)
        
        for strategy_id, strategy_config in self.config["strategies"].items():
            result = await self.test_strategy(int(strategy_id), strategy_config)
            self.results.append(result)
            
            # Stop early if we find a working strategy
            if result["success"]:
                logger.info(f"🎉 BREAKTHROUGH! Strategy {strategy_id} worked!")
                break
            
            # Small delay between attempts
            await asyncio.sleep(2)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save test results to JSON file"""
        results_file = self.attempt_dir / f"homes_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to: {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 50)
        logger.info("HOMES.COM ANTI-BOT TEST SUMMARY")
        logger.info("=" * 50)
        
        successful_strategies = [r for r in self.results if r["success"]]
        
        if successful_strategies:
            logger.info(f"✅ SUCCESS! {len(successful_strategies)} strategy(ies) worked:")
            for result in successful_strategies:
                logger.info(f"   - Strategy {result['strategy_id']}: {result['strategy_name']}")
                logger.info(f"     Status: {result['status_code']}, Load time: {result['load_time']:.2f}s")
        else:
            logger.info("❌ ALL STRATEGIES FAILED")
            logger.info("Common blocking patterns detected:")
            all_blocks = []
            for result in self.results:
                all_blocks.extend(result["detected_blocks"])
            
            if all_blocks:
                from collections import Counter
                block_counts = Counter(all_blocks)
                for block, count in block_counts.most_common():
                    logger.info(f"   - '{block}': {count} times")
            
            logger.info("\nRecommendation: Switch to Movoto.com testing")
        
        logger.info(f"\nScreenshots and logs saved in: {self.attempt_dir}")

async def main():
    tester = HomesAntiBot()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
