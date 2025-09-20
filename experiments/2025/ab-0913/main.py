
"""
Main entry point for Multi-Agent Real Estate Scraping System
Orchestrates all agents for comprehensive property data extraction
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

from navigator import create_navigator
from extractor import Extractor
from validator import Validator
from integrator import Integrator
from utils.common import setup_logger
from utils.anti_bot import UserAgentRotator

class MultiAgentScraper:
    """
    Main orchestrator for multi-agent real estate scraping system
    Coordinates Navigator, Extractor, Validator, and Integrator agents
    """
    
    def __init__(self, sites: list = None, headless: bool = True):
        self.sites = sites or ["redfin", "homes", "movoto"]
        self.headless = headless
        self.logger = setup_logger("multi_agent_scraper")
        
        # Initialize agents
        self.validator = Validator()
        self.integrator = Integrator()
        self.ua_rotator = UserAgentRotator()
        
    async def scrape_property(
        self, 
        address: str,
        export_formats: list = None,
        max_retries: int = 2
    ) -> dict:
        """
        Main scraping orchestration method
        """
        export_formats = export_formats or ["json", "csv"]
        
        self.logger.info("=" * 60)
        self.logger.info("MULTI-AGENT REAL ESTATE SCRAPING SYSTEM")
        self.logger.info("=" * 60)
        self.logger.info(f"Target Address: {address}")
        self.logger.info(f"Target Sites: {', '.join(self.sites)}")
        self.logger.info(f"Export Formats: {', '.join(export_formats)}")
        self.logger.info(f"Started: {datetime.now().isoformat()}")
        self.logger.info("")
        
        results = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "sites_attempted": self.sites,
            "sites_successful": [],
            "properties": [],
            "validation_results": {},
            "exported_files": {},
            "summary": {}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions'
                ]
            )
            
            try:
                # Phase 1: Navigation and Extraction
                for site in self.sites:
                    success = await self._scrape_site(browser, site, address, results, max_retries)
                    if success:
                        results["sites_successful"].append(site)
                
                # Phase 2: Validation
                if results["properties"]:
                    self.logger.info("\n" + "=" * 40)
                    self.logger.info("VALIDATION PHASE")
                    self.logger.info("=" * 40)
                    
                    if len(results["properties"]) > 1:
                        results["validation_results"] = self.validator.cross_validate_properties(
                            results["properties"]
                        )
                    else:
                        prop = results["properties"][0]
                        key = f"{prop.source_site}_{prop.extraction_timestamp}"
                        results["validation_results"][key] = self.validator.validate_property_data(prop)
                    
                    # Log validation summary
                    for source, validation in results["validation_results"].items():
                        self.logger.info(f"{source}: {validation.get_summary()}")
                
                # Phase 3: Integration and Export
                if results["properties"]:
                    self.logger.info("\n" + "=" * 40)
                    self.logger.info("INTEGRATION PHASE")
                    self.logger.info("=" * 40)
                    
                    results["exported_files"] = await self.integrator.integrate_property_data(
                        properties=results["properties"],
                        validation_results=results["validation_results"],
                        export_formats=export_formats,
                        address=address
                    )
                    
                    self.logger.info("Export complete:")
                    for format_type, file_path in results["exported_files"].items():
                        self.logger.info(f"  {format_type.upper()}: {file_path}")
                
                # Generate summary
                results["summary"] = self._generate_summary(results)
                
                self.logger.info("\n" + "=" * 40)
                self.logger.info("SCRAPING COMPLETE")
                self.logger.info("=" * 40)
                self.logger.info(f"Success Rate: {len(results['sites_successful'])}/{len(self.sites)}")
                self.logger.info(f"Properties Extracted: {len(results['properties'])}")
                self.logger.info(f"Files Exported: {len(results['exported_files'])}")
                
                return results
                
            finally:
                await browser.close()
    
    async def _scrape_site(self, browser, site, address, results, max_retries):
        """Scrape individual site with retry logic"""
        
        self.logger.info(f"\n{'='*20} SCRAPING {site.upper()} {'='*20}")
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt} for {site}")
                    # Rotate user agent strategy on retry
                    self.ua_rotator.rotate()
                
                # Navigator Agent
                self.logger.info(f"🧭 Navigator Agent: Navigating to {site}")
                navigator = create_navigator(site)
                
                nav_result = await navigator.navigate_to_property(browser, address)
                
                if not nav_result.success:
                    self.logger.error(f"❌ Navigation failed: {nav_result.error_message}")
                    if attempt < max_retries:
                        continue
                    return False
                
                self.logger.info(f"✅ Navigation successful: {nav_result.property_url}")
                
                # Extractor Agent
                self.logger.info(f"🔍 Extractor Agent: Extracting data from {site}")
                extractor = Extractor(site)
                
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    await page.goto(nav_result.property_url, wait_until="networkidle")
                    
                    extract_result = await extractor.extract_property_data(page, nav_result.property_url)
                    
                    if extract_result.success:
                        self.logger.info(f"✅ Extraction successful: {extract_result.fields_extracted}/{extract_result.total_fields} fields")
                        results["properties"].append(extract_result.property_data)
                        return True
                    else:
                        self.logger.error(f"❌ Extraction failed: {extract_result.error_message}")
                        if attempt < max_retries:
                            continue
                        return False
                        
                finally:
                    await context.close()
                    
            except Exception as e:
                self.logger.error(f"❌ Error scraping {site} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries:
                    continue
                return False
        
        return False
    
    def _generate_summary(self, results):
        """Generate scraping summary"""
        
        total_sites = len(results["sites_attempted"])
        successful_sites = len(results["sites_successful"])
        success_rate = (successful_sites / total_sites * 100) if total_sites > 0 else 0
        
        # Calculate average completeness
        avg_completeness = 0
        if results["validation_results"]:
            avg_completeness = sum(
                v.completeness_score for v in results["validation_results"].values()
            ) / len(results["validation_results"])
        
        return {
            "total_sites_attempted": total_sites,
            "successful_sites": successful_sites,
            "success_rate_percent": success_rate,
            "properties_extracted": len(results["properties"]),
            "average_completeness": avg_completeness,
            "files_exported": len(results["exported_files"]),
            "recommendation": self._get_recommendation(success_rate, avg_completeness)
        }
    
    def _get_recommendation(self, success_rate, avg_completeness):
        """Generate recommendation based on results"""
        
        if success_rate >= 80 and avg_completeness >= 0.7:
            return "EXCELLENT - High success rate with quality data"
        elif success_rate >= 60 and avg_completeness >= 0.5:
            return "GOOD - Acceptable results with room for improvement"
        elif success_rate >= 40:
            return "FAIR - Partial success, consider investigating failures"
        else:
            return "POOR - Low success rate, review configuration and anti-bot strategies"

async def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(description="Multi-Agent Real Estate Scraping System")
    parser.add_argument("address", help="Property address to scrape")
    parser.add_argument(
        "--sites", 
        nargs="+", 
        default=["redfin", "homes", "movoto"],
        choices=["redfin", "homes", "movoto"],
        help="Sites to scrape (default: all)"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["json", "csv"],
        choices=["json", "csv", "pdf"],
        help="Export formats (default: json csv)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run in headless mode (default: False for debugging)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Max retries per site (default: 2)"
    )
    
    args = parser.parse_args()
    
    print("Multi-Agent Real Estate Scraping System")
    print("=" * 50)
    print(f"Address: {args.address}")
    print(f"Sites: {', '.join(args.sites)}")
    print(f"Formats: {', '.join(args.formats)}")
    print(f"Headless: {args.headless}")
    print("-" * 50)
    
    scraper = MultiAgentScraper(sites=args.sites, headless=args.headless)
    
    try:
        results = await scraper.scrape_property(
            address=args.address,
            export_formats=args.formats,
            max_retries=args.retries
        )
        
        print("\n" + "=" * 50)
        print("SCRAPING SUMMARY")
        print("=" * 50)
        summary = results["summary"]
        print(f"Success Rate: {summary['success_rate_percent']:.1f}%")
        print(f"Properties: {summary['properties_extracted']}")
        print(f"Completeness: {summary['average_completeness']:.2f}")
        print(f"Recommendation: {summary['recommendation']}")
        
        if results["exported_files"]:
            print("\nExported Files:")
            for format_type, file_path in results["exported_files"].items():
                print(f"  {format_type.upper()}: {file_path}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
