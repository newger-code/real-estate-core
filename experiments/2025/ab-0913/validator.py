
"""
Validator Agent - Data Completeness and Cross-Reference Validation
Ensures data quality and consistency across multiple sources
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re

from extractor import PropertyData
from utils.common import setup_logger, extract_numeric_value

class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    field: str
    level: ValidationLevel
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of property data validation"""
    is_valid: bool
    completeness_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    critical_issues: int = 0
    warning_issues: int = 0
    info_issues: int = 0
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue and update counters"""
        self.issues.append(issue)
        if issue.level == ValidationLevel.CRITICAL:
            self.critical_issues += 1
        elif issue.level == ValidationLevel.WARNING:
            self.warning_issues += 1
        else:
            self.info_issues += 1
    
    def get_summary(self) -> str:
        """Get validation summary"""
        return (f"Validation: {'PASS' if self.is_valid else 'FAIL'} "
                f"(Score: {self.completeness_score:.2f}, "
                f"Critical: {self.critical_issues}, "
                f"Warnings: {self.warning_issues})")

class Validator:
    """
    Property data validator with completeness checks and cross-referencing
    Implements business rules for real estate data quality
    """
    
    def __init__(self):
        self.logger = setup_logger("validator")
        
        # Required fields for different property types
        self.required_fields = {
            "basic": ["address"],
            "residential": ["address", "beds", "baths", "sqft"],
            "commercial": ["address", "sqft"],
            "land": ["address"]
        }
        
        # Field validation patterns
        self.validation_patterns = {
            "beds": r'^\d+(\.\d+)?$',
            "baths": r'^\d+(\.\d+)?$',
            "sqft": r'[\d,]+',
            "year_built": r'^(19|20)\d{2}$',
            "price": r'[\$\d,]+',
        }
    
    def validate_property_data(
        self, 
        property_data: PropertyData,
        validation_level: str = "residential"
    ) -> ValidationResult:
        """
        Validate property data completeness and consistency
        """
        self.logger.info(f"Validating property data from {property_data.source_site}")
        
        result = ValidationResult(is_valid=True, completeness_score=0.0)
        
        # Check required fields
        self._validate_required_fields(property_data, validation_level, result)
        
        # Validate individual fields
        self._validate_field_formats(property_data, result)
        
        # Validate business logic
        self._validate_business_rules(property_data, result)
        
        # Calculate completeness score
        result.completeness_score = self._calculate_completeness_score(property_data)
        
        # Determine overall validity
        result.is_valid = result.critical_issues == 0 and result.completeness_score >= 0.3
        
        self.logger.info(f"Validation complete: {result.get_summary()}")
        
        return result
    
    def cross_validate_properties(
        self, 
        properties: List[PropertyData]
    ) -> Dict[str, ValidationResult]:
        """
        Cross-validate property data from multiple sources
        """
        self.logger.info(f"Cross-validating {len(properties)} property records")
        
        results = {}
        
        if len(properties) < 2:
            self.logger.warning("Need at least 2 properties for cross-validation")
            return results
        
        # Validate each property individually first
        for prop in properties:
            site_key = f"{prop.source_site}_{prop.extraction_timestamp}"
            results[site_key] = self.validate_property_data(prop)
        
        # Cross-reference validation
        self._cross_validate_addresses(properties, results)
        self._cross_validate_numeric_fields(properties, results)
        self._cross_validate_status(properties, results)
        
        return results
    
    def _validate_required_fields(
        self, 
        property_data: PropertyData, 
        validation_level: str, 
        result: ValidationResult
    ):
        """Validate required fields are present"""
        required = self.required_fields.get(validation_level, self.required_fields["basic"])
        
        for field in required:
            value = getattr(property_data, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                result.add_issue(ValidationIssue(
                    field=field,
                    level=ValidationLevel.CRITICAL,
                    message=f"Required field '{field}' is missing or empty",
                    expected="Non-empty value",
                    actual=str(value)
                ))
    
    def _validate_field_formats(self, property_data: PropertyData, result: ValidationResult):
        """Validate field formats using regex patterns"""
        
        for field, pattern in self.validation_patterns.items():
            value = getattr(property_data, field, None)
            if value and isinstance(value, str):
                if not re.search(pattern, value):
                    result.add_issue(ValidationIssue(
                        field=field,
                        level=ValidationLevel.WARNING,
                        message=f"Field '{field}' format may be invalid",
                        expected=f"Pattern: {pattern}",
                        actual=value
                    ))
    
    def _validate_business_rules(self, property_data: PropertyData, result: ValidationResult):
        """Validate business logic rules"""
        
        # Year built should be reasonable
        if property_data.year_built:
            year = extract_numeric_value(property_data.year_built)
            if year and (year < 1800 or year > 2025):
                result.add_issue(ValidationIssue(
                    field="year_built",
                    level=ValidationLevel.WARNING,
                    message="Year built seems unreasonable",
                    expected="1800-2025",
                    actual=str(year)
                ))
        
        # Beds should be reasonable
        if property_data.beds:
            beds = extract_numeric_value(property_data.beds)
            if beds and (beds < 0 or beds > 20):
                result.add_issue(ValidationIssue(
                    field="beds",
                    level=ValidationLevel.WARNING,
                    message="Number of bedrooms seems unreasonable",
                    expected="0-20",
                    actual=str(beds)
                ))
        
        # Baths should be reasonable
        if property_data.baths:
            baths = extract_numeric_value(property_data.baths)
            if baths and (baths < 0 or baths > 20):
                result.add_issue(ValidationIssue(
                    field="baths",
                    level=ValidationLevel.WARNING,
                    message="Number of bathrooms seems unreasonable",
                    expected="0-20",
                    actual=str(baths)
                ))
        
        # Square footage should be reasonable
        if property_data.sqft:
            sqft = extract_numeric_value(property_data.sqft)
            if sqft and (sqft < 100 or sqft > 50000):
                result.add_issue(ValidationIssue(
                    field="sqft",
                    level=ValidationLevel.WARNING,
                    message="Square footage seems unreasonable",
                    expected="100-50,000",
                    actual=str(sqft)
                ))
        
        # Address should contain basic components
        if property_data.address:
            address = property_data.address.lower()
            if not any(word in address for word in ['st', 'ave', 'rd', 'dr', 'ln', 'ct', 'way', 'blvd']):
                result.add_issue(ValidationIssue(
                    field="address",
                    level=ValidationLevel.INFO,
                    message="Address may be missing street type",
                    expected="Street type (St, Ave, Rd, etc.)",
                    actual=property_data.address
                ))
    
    def _calculate_completeness_score(self, property_data: PropertyData) -> float:
        """Calculate data completeness score (0.0 to 1.0)"""
        
        # Define field weights
        field_weights = {
            "address": 0.20,
            "beds": 0.15,
            "baths": 0.15,
            "sqft": 0.15,
            "year_built": 0.10,
            "price": 0.10,
            "avm_estimate": 0.05,
            "status": 0.05,
            "photos": 0.03,
            "description": 0.02
        }
        
        total_score = 0.0
        
        for field, weight in field_weights.items():
            value = getattr(property_data, field, None)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    total_score += weight
                elif isinstance(value, str) and value.strip():
                    total_score += weight
                elif value:  # Other non-empty values
                    total_score += weight
        
        return min(total_score, 1.0)
    
    def _cross_validate_addresses(
        self, 
        properties: List[PropertyData], 
        results: Dict[str, ValidationResult]
    ):
        """Cross-validate addresses across sources"""
        
        addresses = [(prop.address, prop.source_site) for prop in properties if prop.address]
        
        if len(addresses) < 2:
            return
        
        # Normalize addresses for comparison
        normalized_addresses = []
        for addr, site in addresses:
            normalized = re.sub(r'[^\w\s]', '', addr.lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            normalized_addresses.append((normalized, site))
        
        # Check for significant differences
        base_addr, base_site = normalized_addresses[0]
        for addr, site in normalized_addresses[1:]:
            similarity = self._calculate_address_similarity(base_addr, addr)
            
            if similarity < 0.8:  # Less than 80% similar
                # Add issue to both results
                for result_key, result in results.items():
                    if base_site in result_key or site in result_key:
                        result.add_issue(ValidationIssue(
                            field="address",
                            level=ValidationLevel.WARNING,
                            message=f"Address mismatch between {base_site} and {site}",
                            expected=f"{base_site}: {base_addr}",
                            actual=f"{site}: {addr}"
                        ))
    
    def _cross_validate_numeric_fields(
        self, 
        properties: List[PropertyData], 
        results: Dict[str, ValidationResult]
    ):
        """Cross-validate numeric fields across sources"""
        
        numeric_fields = ["beds", "baths", "sqft", "year_built"]
        
        for field in numeric_fields:
            values = []
            for prop in properties:
                value = getattr(prop, field, None)
                if value:
                    numeric_value = extract_numeric_value(value)
                    if numeric_value:
                        values.append((numeric_value, prop.source_site))
            
            if len(values) < 2:
                continue
            
            # Check for significant differences
            base_value, base_site = values[0]
            for value, site in values[1:]:
                # Calculate percentage difference
                diff_percent = abs(value - base_value) / max(base_value, value) * 100
                
                # Different thresholds for different fields
                threshold = {
                    "beds": 0,      # Should be exact
                    "baths": 10,    # Allow 10% difference
                    "sqft": 20,     # Allow 20% difference
                    "year_built": 0 # Should be exact
                }.get(field, 15)
                
                if diff_percent > threshold:
                    # Add issue to both results
                    for result_key, result in results.items():
                        if base_site in result_key or site in result_key:
                            result.add_issue(ValidationIssue(
                                field=field,
                                level=ValidationLevel.WARNING,
                                message=f"{field} mismatch between sources ({diff_percent:.1f}% difference)",
                                expected=f"{base_site}: {base_value}",
                                actual=f"{site}: {value}"
                            ))
    
    def _cross_validate_status(
        self, 
        properties: List[PropertyData], 
        results: Dict[str, ValidationResult]
    ):
        """Cross-validate listing status across sources"""
        
        statuses = [(prop.status, prop.source_site) for prop in properties if prop.status]
        
        if len(statuses) < 2:
            return
        
        # Normalize statuses
        status_mappings = {
            "for sale": "active",
            "active": "active",
            "listed": "active",
            "sold": "sold",
            "off market": "off_market",
            "not listed": "off_market",
            "not for sale": "off_market",
            "pending": "pending",
            "under contract": "pending"
        }
        
        normalized_statuses = []
        for status, site in statuses:
            normalized = status_mappings.get(status.lower(), status.lower())
            normalized_statuses.append((normalized, site, status))
        
        # Check for conflicts
        base_status, base_site, base_original = normalized_statuses[0]
        for status, site, original in normalized_statuses[1:]:
            if status != base_status:
                # Add issue to both results
                for result_key, result in results.items():
                    if base_site in result_key or site in result_key:
                        result.add_issue(ValidationIssue(
                            field="status",
                            level=ValidationLevel.INFO,
                            message=f"Status conflict between sources",
                            expected=f"{base_site}: {base_original}",
                            actual=f"{site}: {original}"
                        ))
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate similarity between two addresses (0.0 to 1.0)"""
        
        # Simple word-based similarity
        words1 = set(addr1.split())
        words2 = set(addr2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def generate_validation_report(
        self, 
        validation_results: Dict[str, ValidationResult]
    ) -> str:
        """Generate human-readable validation report"""
        
        report = ["=" * 60]
        report.append("PROPERTY DATA VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        for source, result in validation_results.items():
            report.append(f"Source: {source}")
            report.append("-" * 40)
            report.append(f"Overall Status: {'✓ PASS' if result.is_valid else '✗ FAIL'}")
            report.append(f"Completeness Score: {result.completeness_score:.2f}")
            report.append(f"Issues: {result.critical_issues} Critical, {result.warning_issues} Warnings, {result.info_issues} Info")
            report.append("")
            
            if result.issues:
                report.append("Issues Found:")
                for issue in result.issues:
                    level_symbol = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                    report.append(f"  {level_symbol.get(issue.level.value, '•')} {issue.field}: {issue.message}")
                    if issue.expected and issue.actual:
                        report.append(f"    Expected: {issue.expected}")
                        report.append(f"    Actual: {issue.actual}")
                report.append("")
            else:
                report.append("No issues found.")
                report.append("")
        
        # Summary
        total_sources = len(validation_results)
        passed_sources = sum(1 for r in validation_results.values() if r.is_valid)
        avg_completeness = sum(r.completeness_score for r in validation_results.values()) / total_sources
        
        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Sources Validated: {total_sources}")
        report.append(f"Sources Passed: {passed_sources}")
        report.append(f"Average Completeness: {avg_completeness:.2f}")
        report.append("")
        
        return "\n".join(report)
