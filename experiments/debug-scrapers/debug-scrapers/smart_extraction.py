#!/usr/bin/env python3
"""
Smart Property Data Extraction Module
Standalone module for pattern-based property data extraction
Safe to modify without affecting main scraper
"""

import re
import json
from typing import Dict, List, Optional, Tuple


class SmartPropertyExtractor:
    """
    Intelligent property data extractor using content pattern recognition
    Mimics human visual scanning instead of rigid DOM selectors
    """

    def __init__(self):
        # Core property data patterns (based on actual homes.com content)
        self.core_patterns = {
            'price': r'(?:\$)?(\d{2,3},\d{3}(?:\s*-\s*\$?\d{2,3},\d{3})?)',    # $92,000 - $118,000 or 92,000 - 118,000
            'beds': r'(\d+)\s*beds?',                                           # 3 beds
            'baths': r'(\d+\.?\d*)\s*baths?',                                  # 1 bath, 2.5 baths
            'sqft': r'(\d{1,3}(?:,\d{3})*)\s*(?:sq\.?\s*ft|sqft)',           # 1,589 Sq Ft
            'address': r'(\d+.*?(?:Ave|St|Rd|Dr|Ln|Ct|Cir|Pl|Way|Blvd|Pkwy))', # Street addresses
        }

        # Extended patterns for additional data
        self.extended_patterns = {
            'property_type': r'(Single Family|Condo|Townhouse|Multi-Family|Duplex|Single-Family)',
            'property_type_inferred': r'(?:is a|Type:|Style:)\s*(home|house|residence|dwelling)(?:\s+located)',
            'year_built': r'Built in (\d{4})|(\d{4}) built',
            'lot_size': r'([\d.]+)\s*acres?',
            'price_per_sqft': r'\$(\d+)/sq\.?\s*ft',
            'status': r'(For Sale|Not Listed|Off Market|Sold|Pending|FOR SALE|NOT LISTED)',
            'last_sold': r'Last sold.*?\$[\d,]+',
            'hoa_fees': r'HOA.*?\$[\d,]+',
            'property_tax': r'(?:Property tax|Tax).*?\$[\d,]+',
            'estimate_value': r'(?:Est\.?\s*Value|Estimate).*?\$[\d,]+',
            'mortgage_estimate': r'(?:Est\.?\s*mortgage|Monthly payment).*?\$[\d,]+',

            # AVM Providers (capture provider name and dollar value from deep scroll content)
            'avm_collateral_analytics': r'Collateral Analytics[\s\S]{0,500}\$[\d,]+',
            'avm_ice_mortgage': r'ICE Mortgage Technology[\s\S]{0,500}\$[\d,]+',
            'avm_first_american': r'First American[\s\S]{0,500}\$[\d,]+',
            'avm_quantarium': r'Quantarium[\s\S]{0,500}\$[\d,]+',
            'avm_housecanary': r'HouseCanary[\s\S]{0,500}\$[\d,]+',
            'avm_average_value': r'Average Value[\s\S]{0,100}\$[\d,]+',

            # Purchase & Mortgage History
            'purchase_history': r'(?:Purchase|Bought).*?\$[\d,]+.*?\d{4}',
            'mortgage_history': r'(?:Mortgage|Loan).*?\$[\d,]+',

            # Tax History
            'tax_assessment': r'(?:Tax Assessment|Assessed Value).*?\$[\d,]+',
            'tax_paid': r'(?:Tax Paid|Property Tax).*?\$[\d,]+',
            'land_value': r'(?:Land Value).*?\$[\d,]+',
            'improvement_value': r'(?:Improvement|Building) Value.*?\$[\d,]+',

            # Demographics
            'college_grads': r'(\d+)%.*?(?:college|degree|grad)',
            'household_income': r'(?:Household Income|Income).*?\$[\d,]+',
            'median_income': r'Median.*?Income.*?\$[\d,]+',

            # Area Factors
            'crime_score': r'Crime.*?(\d+)',
            'bike_score': r'Bike.*?Score.*?(\d+)',
            'walk_score': r'Walk.*?Score.*?(\d+)',
            'transit_score': r'Transit.*?Score.*?(\d+)',

            # Environmental Factors
            'sound_risk': r'Sound.*?Risk.*?(Low|Medium|High)',
            'flood_risk': r'Flood.*?Risk.*?(Low|Medium|High)',
            'fire_risk': r'Fire.*?Risk.*?(Low|Medium|High)',
            'heat_risk': r'Heat.*?Risk.*?(Low|Medium|High)',

            # Schools
            'school_score': r'School.*?Score.*?(\d+)',
            'school_grade': r'School.*?Grade.*?([A-F])',
            'school_name': r'School.*?([\w\s]+Elementary|[\w\s]+Middle|[\w\s]+High)',
            'school_walk_distance': r'(\d+\.?\d*)\s*(?:mi|miles?).*?school',
        }

    def extract_from_content(self, page_content: str, min_fields: int = 3) -> Dict:
        """
        Extract property data from page content using pattern recognition

        Args:
            page_content: Raw text content from webpage
            min_fields: Minimum fields required to consider extraction successful

        Returns:
            Dict with extracted data and metadata
        """
        result = {
            'found': False,
            'property_data': {},
            'extraction_metadata': {
                'total_patterns_matched': 0,
                'core_patterns_matched': 0,
                'extended_patterns_matched': 0,
                'content_length': len(page_content),
                'patterns_attempted': len(self.core_patterns) + len(self.extended_patterns)
            }
        }

        if not page_content:
            result['extraction_metadata']['error'] = 'No content provided'
            return result

        # Extract core patterns first
        core_matches = 0
        for field, pattern in self.core_patterns.items():
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                # Handle tuple matches (from groups) vs string matches
                if isinstance(matches[0], tuple):
                    value = next(m for m in matches[0] if m) if matches[0] else None
                else:
                    value = matches[0]

                if value:
                    result['property_data'][field] = value.strip()
                    core_matches += 1
                    print(f"✅ Found {field}: {value}")

        # Extract extended patterns
        extended_matches = 0
        for field, pattern in self.extended_patterns.items():
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                # Handle tuple matches (from groups) vs string matches
                if isinstance(matches[0], tuple):
                    value = next(m for m in matches[0] if m) if matches[0] else None
                else:
                    value = matches[0]

                if value:
                    result['property_data'][field] = value.strip()
                    extended_matches += 1
                    print(f"✅ Found {field}: {value}")

        # Update metadata
        result['extraction_metadata']['core_patterns_matched'] = core_matches
        result['extraction_metadata']['extended_patterns_matched'] = extended_matches
        result['extraction_metadata']['total_patterns_matched'] = core_matches + extended_matches

        # Property type inference logic - override detected type with inference when applicable
        if 'property_type_inferred' in result['property_data']:
            inferred_text = result['property_data']['property_type_inferred'].lower()
            if 'home' in inferred_text or 'house' in inferred_text:
                # Override any detected property type with Single Family when inference suggests it
                old_type = result['property_data'].get('property_type', 'None')
                result['property_data']['property_type'] = 'Single Family'
                print(f"✅ Overrode property_type: '{old_type}' -> 'Single Family' based on inference: '{result['property_data']['property_type_inferred']}'")
                if old_type == 'None':
                    extended_matches += 1
                    result['extraction_metadata']['extended_patterns_matched'] = extended_matches
                    result['extraction_metadata']['total_patterns_matched'] = core_matches + extended_matches

        # Determine success
        result['found'] = core_matches >= min_fields

        return result

    def extract_from_screenshot_text(self, screenshot_text: str) -> Dict:
        """
        Extract property data from screenshot OCR text
        Wrapper for testing with screenshot content
        """
        return self.extract_from_content(screenshot_text, min_fields=3)

    def test_patterns(self, test_content: str) -> Dict:
        """
        Test all patterns against content and show what would match
        Useful for debugging and pattern refinement
        """
        test_results = {
            'core_patterns': {},
            'extended_patterns': {},
            'content_preview': test_content[:200] + '...' if len(test_content) > 200 else test_content
        }

        print("🧪 Testing Core Patterns:")
        for field, pattern in self.core_patterns.items():
            matches = re.findall(pattern, test_content, re.IGNORECASE)
            test_results['core_patterns'][field] = {
                'pattern': pattern,
                'matches': matches,
                'found': len(matches) > 0
            }
            status = "✅" if matches else "❌"
            print(f"  {status} {field}: {matches[:3] if matches else 'No matches'}")  # Show first 3

        print("\n🧪 Testing Extended Patterns:")
        for field, pattern in self.extended_patterns.items():
            matches = re.findall(pattern, test_content, re.IGNORECASE)
            test_results['extended_patterns'][field] = {
                'pattern': pattern,
                'matches': matches,
                'found': len(matches) > 0
            }
            status = "✅" if matches else "❌"
            print(f"  {status} {field}: {matches[:2] if matches else 'No matches'}")  # Show first 2

        return test_results

    def add_custom_pattern(self, field_name: str, pattern: str, category: str = 'extended'):
        """
        Add custom extraction pattern for specific sites or data types

        Args:
            field_name: Name of the field to extract
            pattern: Regular expression pattern
            category: 'core' or 'extended'
        """
        if category == 'core':
            self.core_patterns[field_name] = pattern
        else:
            self.extended_patterns[field_name] = pattern

        print(f"✅ Added {category} pattern for '{field_name}': {pattern}")


def test_with_sample_content():
    """Test function with sample property page content"""

    # Sample content based on your screenshot
    sample_content = """
    1240 Pondview Ave, Akron, OH 44305

    $92,000 - $118,000

    3 beds • 1 bath • 1,589 Sq Ft
    $65/Sq Ft Est. Value

    Single Family Home
    Built in 1952

    Property Details:
    Lot Size: 0.25 acres
    Property Tax: $1,250/year
    Est. mortgage: $450/month

    Status: For Sale
    Last sold: March 2020 for $85,000
    """

    print("🧪 TESTING SMART EXTRACTION WITH SAMPLE CONTENT")
    print("=" * 60)

    extractor = SmartPropertyExtractor()

    # Test pattern matching
    test_results = extractor.test_patterns(sample_content)

    print("\n" + "=" * 60)
    print("🎯 EXTRACTION RESULTS:")

    # Perform actual extraction
    extraction_result = extractor.extract_from_content(sample_content)

    print(f"\n📊 Success: {extraction_result['found']}")
    print(f"📊 Fields extracted: {extraction_result['extraction_metadata']['total_patterns_matched']}")
    print(f"📊 Core fields: {extraction_result['extraction_metadata']['core_patterns_matched']}")

    print("\n📋 Extracted Data:")
    for field, value in extraction_result['property_data'].items():
        print(f"  {field}: {value}")

    return extraction_result


if __name__ == "__main__":
    # Run test when executed directly
    test_with_sample_content()