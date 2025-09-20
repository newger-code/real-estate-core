
"""
Extractor Agent - Robust Property Data Extraction
Enhanced from working Redfin implementation with multi-selector fallbacks
"""

import asyncio
from typing import Dict, List, Optional, Any
from playwright.async_api import Page, Locator
from dataclasses import dataclass, field
import re

from utils.common import setup_logger, take_screenshot, extract_numeric_value

@dataclass
class PropertyData:
    """Structured property data with enhanced fields"""
    address: Optional[str] = None
    beds: Optional[str] = None
    baths: Optional[str] = None
    sqft: Optional[str] = None
    year_built: Optional[str] = None
    lot_size: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[str] = None
    avm_estimate: Optional[str] = None
    status: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    description: Optional[str] = None
    features: List[str] = field(default_factory=list)
    
    # Enhanced fields for CTO requirements
    school_scores: Optional[Dict[str, Any]] = None
    flood_plain_info: Optional[str] = None
    
    # Metadata
    source_site: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    property_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "address": self.address,
            "beds": self.beds,
            "baths": self.baths,
            "sqft": self.sqft,
            "year_built": self.year_built,
            "lot_size": self.lot_size,
            "property_type": self.property_type,
            "price": self.price,
            "avm_estimate": self.avm_estimate,
            "status": self.status,
            "photos": self.photos,
            "description": self.description,
            "features": self.features,
            "school_scores": self.school_scores,
            "flood_plain_info": self.flood_plain_info,
            "source_site": self.source_site,
            "extraction_timestamp": self.extraction_timestamp,
            "property_url": self.property_url
        }

@dataclass
class ExtractionResult:
    """Result of data extraction"""
    success: bool
    property_data: Optional[PropertyData] = None
    error_message: Optional[str] = None
    fields_extracted: int = 0
    total_fields: int = 0
    extraction_log: List[str] = field(default_factory=list)

class SelectorGroup:
    """Group of selectors for extracting specific data"""
    
    def __init__(self, name: str, selectors: List[str], extractor_func=None):
        self.name = name
        self.selectors = selectors
        self.extractor_func = extractor_func or self._default_text_extractor
    
    async def _default_text_extractor(self, element: Locator) -> str:
        """Default text extraction"""
        return await element.text_content()
    
    async def extract(self, page: Page) -> Optional[str]:
        """Try each selector until one works"""
        for selector in self.selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    result = await self.extractor_func(element)
                    if result and result.strip():
                        return result.strip()
            except:
                continue
        return None

class Extractor:
    """
    Multi-site property data extractor with fallback selectors
    Enhanced from working Redfin implementation
    """
    
    def __init__(self, site: str):
        self.site = site.lower()
        self.logger = setup_logger(f"extractor_{self.site}")
        self.selector_groups = self._get_selector_groups()
    
    def _get_selector_groups(self) -> Dict[str, SelectorGroup]:
        """Get site-specific selector groups"""
        if self.site == "redfin":
            return self._get_redfin_selectors()
        elif self.site == "homes":
            return self._get_homes_selectors()
        elif self.site == "movoto":
            return self._get_movoto_selectors()
        else:
            return self._get_generic_selectors()
    
    def _get_redfin_selectors(self) -> Dict[str, SelectorGroup]:
        """Redfin-specific selectors from working implementation"""
        return {
            "address": SelectorGroup("address", [
                '.street-address',
                '[data-rf-test-id="abp-streetLine"]',
                '.address',
                'h1.street-address'
            ]),
            "beds": SelectorGroup("beds", [
                '.beds .value',
                '[data-rf-test-id="abp-beds"]',
                '.bed-bath .beds',
                '.stats-bed'
            ]),
            "baths": SelectorGroup("baths", [
                '.baths .value',
                '[data-rf-test-id="abp-baths"]',
                '.bed-bath .baths',
                '.stats-bath'
            ]),
            "sqft": SelectorGroup("sqft", [
                '.sqft .value',
                '[data-rf-test-id="abp-sqFt"]',
                '.stats-sqft',
                '.square-feet'
            ]),
            "year_built": SelectorGroup("year_built", [
                '[data-rf-test-id="abp-yearBuilt"]',
                '.year-built .value',
                '.built-year'
            ]),
            "lot_size": SelectorGroup("lot_size", [
                '[data-rf-test-id="abp-lotSize"]',
                '.lot-size .value',
                '.lot-sqft'
            ]),
            "price": SelectorGroup("price", [
                '.price',
                '.listing-price',
                '[data-rf-test-id="abp-price"]'
            ]),
            "avm_estimate": SelectorGroup("avm_estimate", [
                '.avm-value',
                '[data-rf-test-id="avm-value"]',
                '.redfin-estimate',
                '.estimate-value'
            ]),
            "status": SelectorGroup("status", [
                '.listing-status',
                '.property-status',
                '[data-rf-test-id="listing-status"]'
            ]),
            "photos": SelectorGroup("photos", [
                '.MediaCarousel img',
                '.photo-carousel img',
                '.property-photos img',
                '.listing-photos img'
            ], self._extract_photo_urls),
            "description": SelectorGroup("description", [
                '.remarks',
                '.property-description',
                '[data-rf-test-id="abp-remarks"]'
            ]),
            "school_scores": SelectorGroup("school_scores", [
                '.school-ratings',
                '.school-scores',
                '[data-rf-test-id="school-rating"]',
                '.schools-section',
                '.school-info'
            ], self._extract_school_data),
            "flood_plain_info": SelectorGroup("flood_plain_info", [
                '.flood-risk',
                '.flood-zone',
                '[data-rf-test-id="flood-risk"]',
                '.environmental-risks',
                '.hazard-info'
            ])
        }
    
    def _get_homes_selectors(self) -> Dict[str, SelectorGroup]:
        """Homes.com selectors from breakthrough research"""
        return {
            "address": SelectorGroup("address", [
                'h1[data-testid="property-address"]',
                '.property-address',
                '.listing-address',
                'h1.address',
                '.address-line'
            ]),
            "beds": SelectorGroup("beds", [
                '[data-testid="beds"]',
                '.beds',
                '[aria-label*="bed"]',
                '.bed-count',
                '.property-beds'
            ]),
            "baths": SelectorGroup("baths", [
                '[data-testid="baths"]',
                '.baths',
                '[aria-label*="bath"]',
                '.bath-count',
                '.property-baths'
            ]),
            "sqft": SelectorGroup("sqft", [
                '[data-testid="sqft"]',
                '.sqft',
                '[aria-label*="sqft"]',
                '[aria-label*="square"]',
                '.square-feet',
                '.property-sqft'
            ]),
            "year_built": SelectorGroup("year_built", [
                '[data-testid="year-built"]',
                '.year-built',
                '[aria-label*="year"]',
                '.built-year'
            ]),
            "price": SelectorGroup("price", [
                '.price',
                '.listing-price',
                '[data-testid="price"]',
                '.property-price'
            ]),
            "avm_estimate": SelectorGroup("avm_estimate", [
                '[data-testid="avm"]',
                '.avm-value',
                '.estimate-value',
                '.property-value',
                '.home-value'
            ]),
            "status": SelectorGroup("status", [
                '.listing-status',
                '[data-testid="listing-status"]',
                '.property-status',
                '.sale-status'
            ]),
            "photos": SelectorGroup("photos", [
                '.property-photos img',
                '.listing-photos img',
                '.photo-gallery img',
                '[data-testid="property-photo"]',
                '.image-gallery img'
            ], self._extract_photo_urls),
            "description": SelectorGroup("description", [
                '.property-description',
                '.listing-description',
                '.description',
                '[data-testid="description"]'
            ]),
            "school_scores": SelectorGroup("school_scores", [
                '[data-testid="school-rating"]',
                '.school-ratings',
                '.school-scores',
                '.schools-info',
                '.school-data'
            ], self._extract_school_data),
            "flood_plain_info": SelectorGroup("flood_plain_info", [
                '[data-testid="flood-risk"]',
                '.flood-risk',
                '.flood-zone',
                '.environmental-info',
                '.hazard-data'
            ])
        }
    
    def _get_movoto_selectors(self) -> Dict[str, SelectorGroup]:
        """Movoto.com selectors"""
        return {
            "address": SelectorGroup("address", [
                '.property-address',
                '.listing-address',
                'h1.address',
                '.street-address'
            ]),
            "beds": SelectorGroup("beds", [
                '.beds',
                '.bed-count',
                '[data-label="beds"]',
                '.property-beds'
            ]),
            "baths": SelectorGroup("baths", [
                '.baths',
                '.bath-count',
                '[data-label="baths"]',
                '.property-baths'
            ]),
            "sqft": SelectorGroup("sqft", [
                '.sqft',
                '.square-feet',
                '[data-label="sqft"]',
                '.property-sqft'
            ]),
            "year_built": SelectorGroup("year_built", [
                '.year-built',
                '.built-year',
                '[data-label="year"]'
            ]),
            "price": SelectorGroup("price", [
                '.price',
                '.listing-price',
                '.property-price'
            ]),
            "avm_estimate": SelectorGroup("avm_estimate", [
                '.estimate-value',
                '.avm-value',
                '.property-value'
            ]),
            "status": SelectorGroup("status", [
                '.listing-status',
                '.property-status',
                '.sale-status'
            ]),
            "photos": SelectorGroup("photos", [
                '.property-photos img',
                '.listing-photos img',
                '.photo-gallery img'
            ], self._extract_photo_urls),
            "description": SelectorGroup("description", [
                '.property-description',
                '.listing-description',
                '.description'
            ]),
            "school_scores": SelectorGroup("school_scores", [
                '.school-ratings',
                '.school-scores',
                '.schools-section',
                '.school-info'
            ], self._extract_school_data),
            "flood_plain_info": SelectorGroup("flood_plain_info", [
                '.flood-risk',
                '.flood-zone',
                '.environmental-risks',
                '.hazard-info'
            ])
        }
    
    def _get_generic_selectors(self) -> Dict[str, SelectorGroup]:
        """Generic selectors for unknown sites"""
        return {
            "address": SelectorGroup("address", [
                '.address', '.property-address', '.listing-address', 'h1'
            ]),
            "beds": SelectorGroup("beds", [
                '.beds', '.bed', '.bedroom', '[data-label*="bed"]'
            ]),
            "baths": SelectorGroup("baths", [
                '.baths', '.bath', '.bathroom', '[data-label*="bath"]'
            ]),
            "sqft": SelectorGroup("sqft", [
                '.sqft', '.square-feet', '.sq-ft', '[data-label*="sqft"]'
            ]),
            "price": SelectorGroup("price", [
                '.price', '.listing-price', '.property-price'
            ]),
            "photos": SelectorGroup("photos", [
                '.photos img', '.property-photos img', '.gallery img'
            ], self._extract_photo_urls),
            "school_scores": SelectorGroup("school_scores", [
                '.school-ratings', '.school-scores', '.schools', '.school-info'
            ], self._extract_school_data),
            "flood_plain_info": SelectorGroup("flood_plain_info", [
                '.flood-risk', '.flood-zone', '.environmental-risks'
            ])
        }
    
    async def _extract_photo_urls(self, element: Locator) -> str:
        """Extract photo URLs from image elements"""
        photos = []
        try:
            # Get all image elements
            images = await element.locator('img').all() if await element.locator('img').count() > 0 else [element]
            
            for img in images[:10]:  # Limit to 10 photos
                src = await img.get_attribute('src')
                if src and ('http' in src or src.startswith('//')):
                    if src.startswith('//'):
                        src = 'https:' + src
                    photos.append(src)
        except:
            pass
        
        return ','.join(photos) if photos else None
    
    async def _extract_school_data(self, element: Locator) -> str:
        """Extract school scores and ratings data"""
        try:
            school_data = {}
            
            # Try to find individual school ratings
            school_elements = await element.locator('.school-item, .school-rating, .school').all()
            
            for school_elem in school_elements[:5]:  # Limit to 5 schools
                try:
                    # Extract school name
                    name_elem = await school_elem.locator('.school-name, .name, h3, h4').first
                    school_name = await name_elem.text_content() if name_elem else "Unknown School"
                    
                    # Extract rating/score
                    rating_elem = await school_elem.locator('.rating, .score, .grade').first
                    rating = await rating_elem.text_content() if rating_elem else None
                    
                    # Extract school type
                    type_elem = await school_elem.locator('.school-type, .type, .level').first
                    school_type = await type_elem.text_content() if type_elem else None
                    
                    if school_name and school_name != "Unknown School":
                        school_data[school_name.strip()] = {
                            "rating": rating.strip() if rating else None,
                            "type": school_type.strip() if school_type else None
                        }
                        
                except Exception:
                    continue
            
            # If no individual schools found, try to get overall rating
            if not school_data:
                overall_rating = await element.text_content()
                if overall_rating and any(char.isdigit() for char in overall_rating):
                    school_data["overall_rating"] = overall_rating.strip()
            
            return str(school_data) if school_data else None
            
        except Exception as e:
            return None
    
    async def extract_property_data(self, page: Page, property_url: str) -> ExtractionResult:
        """
        Extract property data from page using multi-selector fallbacks
        """
        from datetime import datetime
        
        self.logger.info(f"Starting data extraction for {self.site}")
        
        property_data = PropertyData(
            source_site=self.site,
            extraction_timestamp=datetime.now().isoformat(),
            property_url=property_url
        )
        
        extraction_log = []
        fields_extracted = 0
        total_fields = len(self.selector_groups)
        
        # Take initial screenshot
        await take_screenshot(page, "EXTRACT_START", self.site, datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # Extract each field
        for field_name, selector_group in self.selector_groups.items():
            try:
                value = await selector_group.extract(page)
                if value:
                    setattr(property_data, field_name, value)
                    fields_extracted += 1
                    extraction_log.append(f"✓ {field_name}: {value[:100]}...")
                    self.logger.info(f"Extracted {field_name}: {value[:100]}...")
                else:
                    extraction_log.append(f"✗ {field_name}: No data found")
                    self.logger.warning(f"No data found for {field_name}")
            except Exception as e:
                extraction_log.append(f"✗ {field_name}: Error - {str(e)}")
                self.logger.error(f"Error extracting {field_name}: {str(e)}")
        
        # Special handling for status detection
        await self._detect_listing_status(page, property_data, extraction_log)
        
        # Take final screenshot
        await take_screenshot(page, "EXTRACT_COMPLETE", self.site, datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        success = fields_extracted > 0
        
        self.logger.info(f"Extraction complete: {fields_extracted}/{total_fields} fields extracted")
        
        return ExtractionResult(
            success=success,
            property_data=property_data,
            fields_extracted=fields_extracted,
            total_fields=total_fields,
            extraction_log=extraction_log
        )
    
    async def _detect_listing_status(self, page: Page, property_data: PropertyData, extraction_log: List[str]):
        """
        Detect listing status from page content
        Enhanced from Homes.com breakthrough research
        """
        try:
            page_content = await page.text_content("body")
            page_content_lower = page_content.lower()
            
            # Status indicators
            status_indicators = [
                ("for sale", "FOR SALE"),
                ("active", "ACTIVE"),
                ("pending", "PENDING"),
                ("sold", "SOLD"),
                ("off market", "OFF MARKET"),
                ("not listed", "NOT LISTED FOR SALE"),
                ("not for sale", "NOT FOR SALE"),
                ("coming soon", "COMING SOON"),
                ("under contract", "UNDER CONTRACT")
            ]
            
            for indicator, status in status_indicators:
                if indicator in page_content_lower:
                    if not property_data.status:  # Only set if not already extracted
                        property_data.status = status
                        extraction_log.append(f"✓ status (detected): {status}")
                        self.logger.info(f"Detected status from content: {status}")
                    break
            
        except Exception as e:
            extraction_log.append(f"✗ status detection: Error - {str(e)}")
            self.logger.error(f"Error detecting status: {str(e)}")
