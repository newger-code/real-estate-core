#!/usr/bin/env python3
"""
Quick proxy connectivity test without full scraping
"""

import asyncio
import os
import ssl
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def test_proxy():
    """Test Bright Data proxy connectivity"""
    load_dotenv()

    proxy_server = "http://brd.superproxy.io:33335"
    proxy_username = os.getenv("BRIGHT_DATA_USERNAME", "brd-customer-hl_dd2a0351-zone-residential_proxy_us1-country-us-session")
    proxy_password = os.getenv("BRIGHT_DATA_PASSWORD", "")
    cert_path = "/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt"

    print("🔍 Quick Proxy Test")
    print("=" * 40)
    print(f"Proxy: {proxy_server}")
    print(f"Username: {proxy_username}")
    print(f"Password: {'Set' if proxy_password else 'NOT SET'}")
    print(f"Certificate: {cert_path} ({'exists' if os.path.exists(cert_path) else 'missing'})")

    if not proxy_password:
        print("❌ Cannot test - proxy password not configured")
        return False

    # Set SSL environment
    os.environ['NODE_EXTRA_CA_CERTS'] = cert_path

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--disable-web-security'
                ],
                proxy={
                    'server': proxy_server,
                    'username': proxy_username,
                    'password': proxy_password
                }
            )

            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            print("\n🌐 Testing connectivity to httpbin.org...")

            try:
                await page.goto("https://httpbin.org/ip", timeout=15000)
                content = await page.content()

                if "origin" in content:
                    # Extract IP from response
                    import json
                    text = await page.inner_text("body")
                    data = json.loads(text)
                    ip = data.get("origin", "unknown")
                    print(f"✅ Proxy working! External IP: {ip}")
                    return True
                else:
                    print("❌ Unexpected response format")
                    return False

            except Exception as e:
                print(f"❌ Connection failed: {e}")
                return False

        except Exception as e:
            print(f"❌ Browser launch failed: {e}")
            return False

        finally:
            try:
                await context.close()
                await browser.close()
            except:
                pass

if __name__ == "__main__":
    success = asyncio.run(test_proxy())
    exit(0 if success else 1)