#!/usr/bin/env python3
"""
Quick Real Website Test - Single Site Focus
Tests one site at a time with immediate results
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from main import MultiAgentScraper
from proxy_config import proxy_manager
from utils.common import setup_logger

async def quick_test_site(site: str, address: str):
    """Quick test of single site"""
    
    logger = setup_logger("quick_test")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"QUICK TEST: {site.upper()} - {address}")
    logger.info("=" * 60)
    
    # Test proxy first
    logger.info("Testing proxy...")
    try:
        success, message, ip = await proxy_manager.test_proxy_connectivity()
        if success:
            logger.info(f"✅ Proxy working - IP: {ip}")
        else:
            logger.error(f"❌ Proxy failed: {message}")
            return None
    except Exception as e:
        logger.error(f"❌ Proxy error: {str(e)}")
        return None
    
    # Create output directory
    output_dir = Path("quick_test_results") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create scraper
        scraper = MultiAgentScraper(sites=[site], headless=True)
        
        # Run scraping with shorter timeout
        logger.info(f"Starting scrape of {site} for {address}...")
        
        result = await scraper.scrape_property(
            address=address,
            export_formats=["json"],
            max_retries=1  # Reduced retries for speed
        )
        
        if result["properties"]:
            prop_data = result["properties"][0].to_dict()
            
            # Save result
            result_file = output_dir / f"{site}_{address.replace(' ', '_').replace(',', '')}.json"
            with open(result_file, "w") as f:
                json.dump(prop_data, f, indent=2)
            
            logger.info("✅ SUCCESS! Property data extracted:")
            logger.info(f"   Address: {prop_data.get('address', 'N/A')}")
            logger.info(f"   Beds/Baths: {prop_data.get('beds', 'N/A')}/{prop_data.get('baths', 'N/A')}")
            logger.info(f"   Square Feet: {prop_data.get('sqft', 'N/A')}")
            logger.info(f"   Price: {prop_data.get('price', 'N/A')}")
            logger.info(f"   Status: {prop_data.get('status', 'N/A')}")
            logger.info(f"   School Data: {'Yes' if prop_data.get('school_scores') else 'No'}")
            logger.info(f"   Flood Info: {'Yes' if prop_data.get('flood_plain_info') else 'No'}")
            
            # Count non-null fields
            non_null_fields = sum(1 for v in prop_data.values() if v is not None and v != "" and v != [])
            total_fields = len(prop_data)
            
            logger.info(f"   Fields Extracted: {non_null_fields}/{total_fields} ({non_null_fields/total_fields:.1%})")
            logger.info(f"   Saved to: {result_file}")
            
            return prop_data
        else:
            logger.error("❌ FAILED: No property data extracted")
            return None
            
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        return None

async def main():
    """Main test function"""
    
    # Test parameters
    test_address = "1841 Marks Ave, Akron, OH 44305"
    sites_to_test = ["redfin", "homes", "movoto"]
    
    print("Quick Real Estate Scraper Test")
    print("=" * 40)
    print(f"Address: {test_address}")
    print(f"Sites: {', '.join(sites_to_test)}")
    print()
    
    results = {}
    
    for site in sites_to_test:
        print(f"\nTesting {site.upper()}...")
        print("-" * 30)
        
        try:
            result = await quick_test_site(site, test_address)
            results[site] = {
                "success": result is not None,
                "data": result
            }
            
            if result:
                print(f"✅ {site.upper()} - SUCCESS")
            else:
                print(f"❌ {site.upper()} - FAILED")
                
        except Exception as e:
            print(f"❌ {site.upper()} - ERROR: {str(e)}")
            results[site] = {
                "success": False,
                "error": str(e)
            }
    
    # Summary
    successful_sites = sum(1 for r in results.values() if r["success"])
    total_sites = len(sites_to_test)
    
    print(f"\n{'='*40}")
    print("FINAL SUMMARY")
    print(f"{'='*40}")
    print(f"Successful Sites: {successful_sites}/{total_sites}")
    print(f"Success Rate: {successful_sites/total_sites:.1%}")
    
    if successful_sites > 0:
        print("\n🎯 PROOF OF SCRAPED DATA:")
        for site, result in results.items():
            if result["success"]:
                data = result["data"]
                print(f"\n{site.upper()}:")
                print(f"  Address: {data.get('address', 'N/A')}")
                print(f"  Beds/Baths: {data.get('beds', 'N/A')}/{data.get('baths', 'N/A')}")
                print(f"  Sqft: {data.get('sqft', 'N/A')}")
                print(f"  Price: {data.get('price', 'N/A')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
