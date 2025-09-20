#!/usr/bin/env python3
"""
Real Website Testing Script with Bright Data Proxy Integration
Tests actual scraping with proof of data extraction
"""

import asyncio
import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from main import MultiAgentScraper
from proxy_config import proxy_manager
from utils.common import setup_logger

class RealScrapingTester:
    """
    Comprehensive real website testing with proof generation
    """
    
    def __init__(self):
        self.logger = setup_logger("real_scraping_tester")
        self.test_addresses = [
            "1841 Marks Ave, Akron, OH 44305",
            "1754 Hampton Rd, Akron, OH 44305"
        ]
        self.sites = ["redfin", "homes", "movoto"]
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directories
        self.output_dir = Path("test_results") / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_dir = self.output_dir / "scraped_data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.reports_dir = self.output_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    async def run_comprehensive_test(self):
        """Run comprehensive testing with all sites and addresses"""
        
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE REAL WEBSITE SCRAPING TEST")
        self.logger.info("=" * 80)
        self.logger.info(f"Test Timestamp: {self.timestamp}")
        self.logger.info(f"Test Addresses: {self.test_addresses}")
        self.logger.info(f"Target Sites: {self.sites}")
        self.logger.info(f"Output Directory: {self.output_dir}")
        
        # Step 1: Test proxy connectivity
        await self._test_proxy_connectivity()
        
        # Step 2: Test each address on each site
        for address in self.test_addresses:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"TESTING ADDRESS: {address}")
            self.logger.info(f"{'='*60}")
            
            address_results = {}
            
            for site in self.sites:
                self.logger.info(f"\n{'-'*40}")
                self.logger.info(f"Testing {site.upper()} for {address}")
                self.logger.info(f"{'-'*40}")
                
                site_result = await self._test_site_address(site, address)
                address_results[site] = site_result
                
                # Save individual result
                await self._save_individual_result(site, address, site_result)
            
            self.results[address] = address_results
        
        # Step 3: Generate comprehensive report
        await self._generate_comprehensive_report()
        
        # Step 4: Create proof files
        await self._create_proof_files()
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("TESTING COMPLETE")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Results saved to: {self.output_dir}")
        
        return self.results
    
    async def _test_proxy_connectivity(self):
        """Test Bright Data proxy connectivity"""
        self.logger.info("\n" + "="*40)
        self.logger.info("PROXY CONNECTIVITY TEST")
        self.logger.info("="*40)
        
        try:
            success, message, ip = await proxy_manager.test_proxy_connectivity()
            
            if success:
                self.logger.info(f"✅ Proxy test successful!")
                self.logger.info(f"   External IP: {ip}")
                self.logger.info(f"   Message: {message}")
            else:
                self.logger.error(f"❌ Proxy test failed: {message}")
                
            # Save proxy test result
            proxy_result = {
                "success": success,
                "message": message,
                "external_ip": ip,
                "timestamp": datetime.now().isoformat(),
                "proxy_config": proxy_manager.get_proxy_stats()
            }
            
            with open(self.reports_dir / "proxy_test.json", "w") as f:
                json.dump(proxy_result, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Proxy test error: {str(e)}")
    
    async def _test_site_address(self, site: str, address: str) -> Dict[str, Any]:
        """Test specific site with specific address"""
        
        result = {
            "site": site,
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error_message": None,
            "property_data": None,
            "extraction_stats": {},
            "files_created": []
        }
        
        try:
            # Create scraper for single site
            scraper = MultiAgentScraper(sites=[site], headless=True)
            
            # Run scraping
            scrape_result = await scraper.scrape_property(
                address=address,
                export_formats=["json", "csv"],
                max_retries=2
            )
            
            if scrape_result["properties"]:
                result["success"] = True
                result["property_data"] = scrape_result["properties"][0].to_dict()
                result["extraction_stats"] = {
                    "fields_extracted": len([v for v in result["property_data"].values() if v is not None]),
                    "total_fields": len(result["property_data"]),
                    "completeness_score": len([v for v in result["property_data"].values() if v is not None]) / len(result["property_data"])
                }
                result["files_created"] = list(scrape_result.get("exported_files", {}).values())
                
                self.logger.info(f"✅ {site.upper()} SUCCESS")
                self.logger.info(f"   Fields extracted: {result['extraction_stats']['fields_extracted']}/{result['extraction_stats']['total_fields']}")
                self.logger.info(f"   Completeness: {result['extraction_stats']['completeness_score']:.2%}")
                
                # Log key extracted data
                prop_data = result["property_data"]
                if prop_data.get("address"):
                    self.logger.info(f"   Address: {prop_data['address']}")
                if prop_data.get("beds") and prop_data.get("baths"):
                    self.logger.info(f"   Beds/Baths: {prop_data['beds']}/{prop_data['baths']}")
                if prop_data.get("sqft"):
                    self.logger.info(f"   Square Feet: {prop_data['sqft']}")
                if prop_data.get("price"):
                    self.logger.info(f"   Price: {prop_data['price']}")
                if prop_data.get("school_scores"):
                    self.logger.info(f"   School Data: Found")
                if prop_data.get("flood_plain_info"):
                    self.logger.info(f"   Flood Info: {prop_data['flood_plain_info'][:50]}...")
                    
            else:
                result["error_message"] = "No property data extracted"
                self.logger.error(f"❌ {site.upper()} FAILED: No property data extracted")
                
        except Exception as e:
            result["error_message"] = str(e)
            self.logger.error(f"❌ {site.upper()} ERROR: {str(e)}")
        
        return result
    
    async def _save_individual_result(self, site: str, address: str, result: Dict[str, Any]):
        """Save individual scraping result"""
        
        # Clean address for filename
        clean_address = address.replace(",", "_").replace(" ", "_").replace("/", "_")
        filename = f"{site}_{clean_address}_{self.timestamp}"
        
        # Save JSON
        json_path = self.data_dir / f"{filename}.json"
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)
        
        # Save CSV if property data exists
        if result["success"] and result["property_data"]:
            csv_path = self.data_dir / f"{filename}.csv"
            
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Write headers
                headers = list(result["property_data"].keys())
                writer.writerow(headers)
                
                # Write data
                values = [str(result["property_data"].get(h, "")) for h in headers]
                writer.writerow(values)
        
        self.logger.info(f"   Saved: {json_path.name}")
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        
        report = {
            "test_summary": {
                "timestamp": self.timestamp,
                "addresses_tested": len(self.test_addresses),
                "sites_tested": len(self.sites),
                "total_tests": len(self.test_addresses) * len(self.sites)
            },
            "success_rates": {},
            "site_performance": {},
            "address_performance": {},
            "detailed_results": self.results,
            "recommendations": []
        }
        
        # Calculate success rates
        total_tests = 0
        successful_tests = 0
        
        for address, address_results in self.results.items():
            address_success = 0
            for site, site_result in address_results.items():
                total_tests += 1
                if site_result["success"]:
                    successful_tests += 1
                    address_success += 1
            
            report["address_performance"][address] = {
                "success_rate": address_success / len(self.sites),
                "successful_sites": address_success,
                "total_sites": len(self.sites)
            }
        
        # Site performance
        for site in self.sites:
            site_success = 0
            for address in self.test_addresses:
                if self.results[address][site]["success"]:
                    site_success += 1
            
            report["site_performance"][site] = {
                "success_rate": site_success / len(self.test_addresses),
                "successful_addresses": site_success,
                "total_addresses": len(self.test_addresses)
            }
        
        report["success_rates"]["overall"] = successful_tests / total_tests if total_tests > 0 else 0
        
        # Generate recommendations
        if report["success_rates"]["overall"] >= 0.8:
            report["recommendations"].append("EXCELLENT: High success rate across all sites")
        elif report["success_rates"]["overall"] >= 0.6:
            report["recommendations"].append("GOOD: Acceptable performance with room for improvement")
        else:
            report["recommendations"].append("NEEDS IMPROVEMENT: Low success rate requires investigation")
        
        # Identify best performing site
        best_site = max(report["site_performance"].items(), key=lambda x: x[1]["success_rate"])
        report["recommendations"].append(f"Best performing site: {best_site[0]} ({best_site[1]['success_rate']:.1%} success)")
        
        # Save report
        report_path = self.reports_dir / "comprehensive_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"\n📊 COMPREHENSIVE REPORT")
        self.logger.info(f"Overall Success Rate: {report['success_rates']['overall']:.1%}")
        self.logger.info(f"Best Site: {best_site[0]} ({best_site[1]['success_rate']:.1%})")
        self.logger.info(f"Report saved: {report_path}")
        
        return report
    
    async def _create_proof_files(self):
        """Create proof files showing actual scraped data"""
        
        proof_data = {
            "test_metadata": {
                "timestamp": self.timestamp,
                "tester": "Multi-Agent Real Estate Scraper",
                "proxy_used": "Bright Data Residential Proxy",
                "addresses_tested": self.test_addresses,
                "sites_tested": self.sites
            },
            "scraped_properties": []
        }
        
        # Collect all successfully scraped properties
        for address, address_results in self.results.items():
            for site, site_result in address_results.items():
                if site_result["success"] and site_result["property_data"]:
                    proof_data["scraped_properties"].append({
                        "source_site": site,
                        "test_address": address,
                        "scraped_data": site_result["property_data"],
                        "extraction_stats": site_result["extraction_stats"]
                    })
        
        # Save proof file
        proof_path = self.reports_dir / "PROOF_OF_SCRAPED_DATA.json"
        with open(proof_path, "w") as f:
            json.dump(proof_data, f, indent=2)
        
        # Create summary proof file
        summary_path = self.reports_dir / "PROOF_SUMMARY.txt"
        with open(summary_path, "w") as f:
            f.write("REAL ESTATE SCRAPER - PROOF OF ACTUAL DATA EXTRACTION\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Proxy Used: Bright Data Residential Proxy\n")
            f.write(f"Total Properties Scraped: {len(proof_data['scraped_properties'])}\n\n")
            
            for i, prop in enumerate(proof_data["scraped_properties"], 1):
                f.write(f"PROPERTY {i}:\n")
                f.write(f"  Site: {prop['source_site'].upper()}\n")
                f.write(f"  Test Address: {prop['test_address']}\n")
                f.write(f"  Scraped Address: {prop['scraped_data'].get('address', 'N/A')}\n")
                f.write(f"  Beds/Baths: {prop['scraped_data'].get('beds', 'N/A')}/{prop['scraped_data'].get('baths', 'N/A')}\n")
                f.write(f"  Square Feet: {prop['scraped_data'].get('sqft', 'N/A')}\n")
                f.write(f"  Price: {prop['scraped_data'].get('price', 'N/A')}\n")
                f.write(f"  Status: {prop['scraped_data'].get('status', 'N/A')}\n")
                f.write(f"  School Data: {'Yes' if prop['scraped_data'].get('school_scores') else 'No'}\n")
                f.write(f"  Flood Info: {'Yes' if prop['scraped_data'].get('flood_plain_info') else 'No'}\n")
                f.write(f"  Fields Extracted: {prop['extraction_stats']['fields_extracted']}/{prop['extraction_stats']['total_fields']}\n")
                f.write(f"  Completeness: {prop['extraction_stats']['completeness_score']:.1%}\n\n")
        
        self.logger.info(f"🎯 PROOF FILES CREATED")
        self.logger.info(f"   Detailed Proof: {proof_path}")
        self.logger.info(f"   Summary Proof: {summary_path}")
        self.logger.info(f"   Properties Scraped: {len(proof_data['scraped_properties'])}")

async def main():
    """Main test execution"""
    
    print("Real Estate Scraper - Comprehensive Testing")
    print("=" * 50)
    
    tester = RealScrapingTester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Print final summary
        total_tests = sum(len(addr_results) for addr_results in results.values())
        successful_tests = sum(
            1 for addr_results in results.values() 
            for site_result in addr_results.values() 
            if site_result["success"]
        )
        
        print(f"\n{'='*50}")
        print("FINAL SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Success Rate: {successful_tests/total_tests:.1%}")
        print(f"Output Directory: {tester.output_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
