#!/usr/bin/env python3
"""
Test AVM extraction with extensive scrolling to capture dollar values
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_avm_with_deep_scroll():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        # Go directly to the property page
        url = "https://www.homes.com/property/1240-pondview-ave-akron-oh/5qr1h5v7vqxsj/"
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        print("=== DEEP SCROLLING TO CAPTURE AVM DATA ===")

        # Enhanced scrolling similar to main scraper but more aggressive
        page_height = await page.evaluate("document.body.scrollHeight")
        print(f"Initial page height: {page_height}px")

        # Scroll down gradually
        scroll_step = 300
        current_position = 0

        while current_position < page_height:
            current_position += scroll_step
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await page.wait_for_timeout(2000)  # Longer wait for content to load

            # Check if page height increased
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height
                print(f"Page expanded to: {page_height}px")

        # Extra deep scroll to bottom and wait
        print("Deep scrolling to absolute bottom...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(5000)  # Long wait for AVM section

        # Get final content
        content = await page.text_content("body")

        # Look for AVM content around the specific values you mentioned
        print("\n=== SEARCHING FOR AVM VALUES ===")

        # Search for dollar amounts near AVM providers
        avm_patterns = {
            'collateral_analytics_full': r'Collateral Analytics[\s\S]{0,200}\$[\d,]+',
            'ice_mortgage_full': r'ICE Mortgage Technology[\s\S]{0,200}\$[\d,]+',
            'first_american_full': r'First American[\s\S]{0,200}\$[\d,]+',
            'corelogic_full': r'CoreLogic[\s\S]{0,200}\$[\d,]+',
            'housecanary_full': r'HouseCanary[\s\S]{0,200}\$[\d,]+',
            'any_avm_value': r'(?:Collateral Analytics|ICE Mortgage Technology|First American|CoreLogic|HouseCanary)[\s\S]{0,300}\$[\d,]+',
            'all_dollar_amounts': r'\$[\d,]+',
        }

        for pattern_name, pattern in avm_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"\n✅ {pattern_name}:")
                for match in matches[:5]:  # Show first 5 matches
                    clean_match = ' '.join(match.split())  # Clean up whitespace
                    if len(clean_match) > 100:
                        clean_match = clean_match[:100] + "..."
                    print(f"    {clean_match}")
            else:
                print(f"❌ {pattern_name}: No matches")

        # Look for the specific AVM section
        print("\n=== AVM SECTION DETECTION ===")
        avm_indicators = ["Automated Valuation Model", "AVM", "valuation"]

        lines = content.split('\n')
        in_avm_section = False
        avm_section_content = []

        for i, line in enumerate(lines):
            if any(indicator.lower() in line.lower() for indicator in avm_indicators):
                in_avm_section = True
                print(f"Found AVM section at line {i}: {line.strip()}")
                # Capture surrounding context
                start = max(0, i-5)
                end = min(len(lines), i+20)
                avm_section_content.extend(lines[start:end])

        if avm_section_content:
            print("\n=== AVM SECTION CONTENT ===")
            for line in avm_section_content:
                if line.strip():
                    print(f"  {line.strip()}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_avm_with_deep_scroll())