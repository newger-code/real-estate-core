#!/usr/bin/env python3
"""
Quick test to understand AVM section content on the live page
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_avm_content():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        # Go directly to the property page
        url = "https://www.homes.com/property/1240-pondview-ave-akron-oh/5qr1h5v7vqxsj/"
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        # Get page content
        content = await page.text_content("body")

        # Look for AVM-related content
        print("=== SEARCHING FOR AVM CONTENT ===")

        # Find content around "Automated Valuation" or "AVM"
        lines = content.split('\n')
        avm_context = []
        found_avm_section = False

        for i, line in enumerate(lines):
            if any(term in line.lower() for term in ['automated valuation', 'avm', 'collateral analytics', 'corelogic', 'first american', 'housecanary']):
                found_avm_section = True
                # Get context around this line
                start = max(0, i-3)
                end = min(len(lines), i+3)
                avm_context.extend(lines[start:end])
                print(f"Found AVM content at line {i}: {line.strip()}")

        print("\n=== AVM SECTION CONTEXT ===")
        for line in avm_context:
            if line.strip():
                print(f"  {line.strip()}")

        # Test updated patterns against actual content
        print("\n=== TESTING UPDATED PATTERNS ===")
        patterns = {
            'avm_collateral_analytics': r'Collateral Analytics.*?(?:\$[\d,]+|Not Available|does not have data)',
            'avm_ice_mortgage': r'ICE Mortgage Technology.*?(?:\$[\d,]+|Not Available|does not have data)',
            'avm_first_american': r'First American.*?(?:\$[\d,]+|Not Available|does not have data)',
            'avm_housecanary': r'HouseCanary.*?(?:\$[\d,]+|Not Available|does not have data)',
            'all_avm_providers': r'(Collateral Analytics|ICE Mortgage Technology|First American|HouseCanary)',
        }

        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"{pattern_name}: {matches}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_avm_content())