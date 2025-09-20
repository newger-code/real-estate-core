#!/usr/bin/env python3
"""
Quick validation test for Bright Data fixes
"""

import sys
import os
from dotenv import load_dotenv

def test_environment():
    """Test environment variable loading"""
    print("🔍 Testing Environment Variables...")
    load_dotenv()

    password = os.getenv('BRIGHT_DATA_PASSWORD')
    if password:
        print(f"✅ BRIGHT_DATA_PASSWORD loaded: {password[:6]}...")
        return True
    else:
        print("❌ BRIGHT_DATA_PASSWORD not found")
        return False

def test_certificate():
    """Test certificate file existence"""
    print("\n🔍 Testing Certificate Files...")

    possible_paths = [
        '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/bright_ca.crt',
        '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers/cert/exported_Bright Data Proxy Root CA.cer'
    ]

    found_certs = []
    for path in possible_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ Found certificate: {path} ({size} bytes)")
            found_certs.append(path)
        else:
            print(f"❌ Missing: {path}")

    return len(found_certs) > 0

def test_class_instantiation():
    """Test PropertyScraper class can be instantiated"""
    print("\n🔍 Testing PropertyScraper Class...")

    try:
        # Add current directory to path
        sys.path.insert(0, '/Users/newg_m1/real-estate-comps/avm_platform/debug-scrapers')
        from scrape_property import PropertyScraper

        # Test instantiation
        scraper = PropertyScraper("123 Test St", "homes")
        print("✅ PropertyScraper class instantiated successfully")

        # Test run method exists
        if hasattr(scraper, 'run') and callable(getattr(scraper, 'run')):
            print("✅ run() method exists and is callable")
            return True
        else:
            print("❌ run() method missing or not callable")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Bright Data Fix Validation Test")
    print("=" * 50)

    tests = [
        ("Environment Variables", test_environment),
        ("Certificate Files", test_certificate),
        ("Class Instantiation", test_class_instantiation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📝 Test: {test_name}")
        if test_func():
            passed += 1

    print(f"\n{'=' * 50}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ready to test scraping.")
        print("\n📋 Next steps:")
        print("   python scrape_property.py '1240 Pondview Ave, Akron, OH 44305' homes")
    else:
        print("⚠️  Some tests failed. Check the issues above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)