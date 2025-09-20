
"""
Integrator Agent - Data Integration and Export
Feeds data into analysis pipeline, exports to multiple formats, and handles notifications
"""

import json
import csv
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import pandas as pd

from extractor import PropertyData
from validator import ValidationResult
from utils.common import setup_logger

class Integrator:
    """
    Data integration and export agent
    Handles JSON/CSV/PDF export and pipeline integration
    """
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("integrator")
        
    async def integrate_property_data(
        self,
        properties: List[PropertyData],
        validation_results: Dict[str, ValidationResult],
        export_formats: List[str] = ["json", "csv"],
        address: str = None
    ) -> Dict[str, str]:
        """
        Integrate property data and export to specified formats
        Returns dict of format -> file_path
        """
        self.logger.info(f"Integrating {len(properties)} property records")
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        address_safe = self._sanitize_filename(address) if address else "property"
        
        exported_files = {}
        
        # Prepare integrated data
        integrated_data = self._prepare_integrated_data(properties, validation_results)
        
        # Export to requested formats
        for format_type in export_formats:
            try:
                if format_type.lower() == "json":
                    file_path = await self._export_json(integrated_data, address_safe, timestamp)
                    exported_files["json"] = file_path
                    
                elif format_type.lower() == "csv":
                    file_path = await self._export_csv(integrated_data, address_safe, timestamp)
                    exported_files["csv"] = file_path
                    
                elif format_type.lower() == "pdf":
                    file_path = await self._export_pdf(integrated_data, address_safe, timestamp)
                    exported_files["pdf"] = file_path
                    
                else:
                    self.logger.warning(f"Unsupported export format: {format_type}")
                    
            except Exception as e:
                self.logger.error(f"Error exporting to {format_type}: {str(e)}")
        
        # Send to deal analyzer pipeline
        await self._send_to_deal_analyzer(integrated_data)
        
        # Generate notifications
        await self._generate_notifications(integrated_data, exported_files)
        
        self.logger.info(f"Integration complete. Exported: {list(exported_files.keys())}")
        
        return exported_files
    
    def _prepare_integrated_data(
        self,
        properties: List[PropertyData],
        validation_results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """Prepare integrated data structure"""
        
        # Convert properties to dictionaries
        property_dicts = [prop.to_dict() for prop in properties]
        
        # Add validation results
        validation_summary = {}
        for source, result in validation_results.items():
            validation_summary[source] = {
                "is_valid": result.is_valid,
                "completeness_score": result.completeness_score,
                "critical_issues": result.critical_issues,
                "warning_issues": result.warning_issues,
                "info_issues": result.info_issues,
                "issues": [
                    {
                        "field": issue.field,
                        "level": issue.level.value,
                        "message": issue.message,
                        "expected": issue.expected,
                        "actual": issue.actual
                    }
                    for issue in result.issues
                ]
            }
        
        # Create consolidated property data
        consolidated = self._consolidate_property_data(properties)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(properties, validation_results)
        
        integrated_data = {
            "metadata": {
                "integration_timestamp": datetime.now().isoformat(),
                "total_sources": len(properties),
                "sources": [prop.source_site for prop in properties],
                "address_searched": properties[0].address if properties else None
            },
            "individual_sources": property_dicts,
            "validation_results": validation_summary,
            "consolidated_data": consolidated,
            "confidence_scores": confidence_scores,
            "summary": self._generate_summary(properties, validation_results)
        }
        
        return integrated_data
    
    def _consolidate_property_data(self, properties: List[PropertyData]) -> Dict[str, Any]:
        """Consolidate data from multiple sources into best estimates"""
        
        if not properties:
            return {}
        
        consolidated = {}
        
        # For each field, choose the best value
        fields = ["address", "beds", "baths", "sqft", "year_built", "lot_size", 
                 "property_type", "price", "avm_estimate", "status", "description"]
        
        for field in fields:
            values = []
            for prop in properties:
                value = getattr(prop, field, None)
                if value and (isinstance(value, str) and value.strip() or not isinstance(value, str)):
                    values.append((value, prop.source_site))
            
            if values:
                # Choose best value (prioritize Redfin, then others)
                best_value = self._choose_best_value(values, field)
                consolidated[field] = best_value
        
        # Consolidate photos from all sources
        all_photos = []
        for prop in properties:
            if prop.photos:
                all_photos.extend(prop.photos)
        consolidated["photos"] = list(set(all_photos))  # Remove duplicates
        
        # Consolidate features
        all_features = []
        for prop in properties:
            if prop.features:
                all_features.extend(prop.features)
        consolidated["features"] = list(set(all_features))
        
        return consolidated
    
    def _choose_best_value(self, values: List[tuple], field: str) -> Any:
        """Choose the best value from multiple sources"""
        
        if len(values) == 1:
            return values[0][0]
        
        # Source priority (Redfin is most reliable based on testing)
        source_priority = {"redfin": 3, "homes": 2, "movoto": 1}
        
        # Sort by source priority
        values_with_priority = [
            (value, source, source_priority.get(source, 0))
            for value, source in values
        ]
        values_with_priority.sort(key=lambda x: x[2], reverse=True)
        
        # For numeric fields, prefer non-zero values
        if field in ["beds", "baths", "sqft", "year_built"]:
            for value, source, priority in values_with_priority:
                try:
                    numeric_value = float(str(value).replace(',', ''))
                    if numeric_value > 0:
                        return value
                except:
                    continue
        
        # Return highest priority value
        return values_with_priority[0][0]
    
    def _calculate_confidence_scores(
        self,
        properties: List[PropertyData],
        validation_results: Dict[str, ValidationResult]
    ) -> Dict[str, float]:
        """Calculate confidence scores for each field"""
        
        confidence_scores = {}
        
        # Base confidence on validation results and source agreement
        fields = ["address", "beds", "baths", "sqft", "year_built", "price", "status"]
        
        for field in fields:
            values = []
            for prop in properties:
                value = getattr(prop, field, None)
                if value:
                    values.append(value)
            
            if not values:
                confidence_scores[field] = 0.0
                continue
            
            # Calculate agreement score
            unique_values = len(set(str(v).lower().strip() for v in values))
            agreement_score = 1.0 - (unique_values - 1) / max(len(values), 1)
            
            # Factor in validation scores
            avg_validation_score = sum(
                result.completeness_score for result in validation_results.values()
            ) / len(validation_results) if validation_results else 0.5
            
            # Combine scores
            confidence_scores[field] = (agreement_score * 0.6 + avg_validation_score * 0.4)
        
        return confidence_scores
    
    def _generate_summary(
        self,
        properties: List[PropertyData],
        validation_results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        
        total_sources = len(properties)
        valid_sources = sum(1 for result in validation_results.values() if result.is_valid)
        avg_completeness = sum(
            result.completeness_score for result in validation_results.values()
        ) / len(validation_results) if validation_results else 0.0
        
        # Count available data points
        data_availability = {}
        fields = ["address", "beds", "baths", "sqft", "year_built", "price", "status"]
        
        for field in fields:
            available = sum(1 for prop in properties if getattr(prop, field, None))
            data_availability[field] = {
                "available_sources": available,
                "percentage": (available / total_sources * 100) if total_sources > 0 else 0
            }
        
        return {
            "total_sources": total_sources,
            "valid_sources": valid_sources,
            "validation_pass_rate": (valid_sources / total_sources * 100) if total_sources > 0 else 0,
            "average_completeness": avg_completeness,
            "data_availability": data_availability,
            "recommendation": self._generate_recommendation(avg_completeness, valid_sources, total_sources)
        }
    
    def _generate_recommendation(self, avg_completeness: float, valid_sources: int, total_sources: int) -> str:
        """Generate data quality recommendation"""
        
        if avg_completeness >= 0.8 and valid_sources == total_sources:
            return "EXCELLENT - High quality data from all sources"
        elif avg_completeness >= 0.6 and valid_sources >= total_sources * 0.8:
            return "GOOD - Reliable data with minor gaps"
        elif avg_completeness >= 0.4 and valid_sources >= total_sources * 0.5:
            return "FAIR - Usable data but consider additional sources"
        else:
            return "POOR - Data quality issues detected, manual review recommended"
    
    async def _export_json(self, data: Dict[str, Any], address: str, timestamp: str) -> str:
        """Export to JSON format"""
        
        filename = f"property_data_{address}_{timestamp}.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Exported JSON: {file_path}")
        return str(file_path)
    
    async def _export_csv(self, data: Dict[str, Any], address: str, timestamp: str) -> str:
        """Export to CSV format"""
        
        filename = f"property_data_{address}_{timestamp}.csv"
        file_path = self.output_dir / filename
        
        # Flatten data for CSV
        rows = []
        
        # Add consolidated data row
        consolidated = data.get("consolidated_data", {})
        if consolidated:
            row = {"source": "CONSOLIDATED", **consolidated}
            # Convert lists to strings
            for key, value in row.items():
                if isinstance(value, list):
                    row[key] = "; ".join(str(v) for v in value)
            rows.append(row)
        
        # Add individual source rows
        for source_data in data.get("individual_sources", []):
            row = source_data.copy()
            # Convert lists to strings
            for key, value in row.items():
                if isinstance(value, list):
                    row[key] = "; ".join(str(v) for v in value)
            rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False, encoding='utf-8')
            self.logger.info(f"Exported CSV: {file_path}")
        
        return str(file_path)
    
    async def _export_pdf(self, data: Dict[str, Any], address: str, timestamp: str) -> str:
        """Export to PDF format using reportlab"""
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            filename = f"property_report_{address}_{timestamp}.pdf"
            file_path = self.output_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(file_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("Property Data Report", title_style))
            story.append(Spacer(1, 20))
            
            # Metadata
            metadata = data.get("metadata", {})
            story.append(Paragraph(f"<b>Address:</b> {metadata.get('address_searched', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Generated:</b> {metadata.get('integration_timestamp', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Sources:</b> {', '.join(metadata.get('sources', []))}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Summary
            summary = data.get("summary", {})
            story.append(Paragraph("<b>Data Quality Summary</b>", styles['Heading2']))
            story.append(Paragraph(f"Recommendation: {summary.get('recommendation', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Average Completeness: {summary.get('average_completeness', 0):.2f}", styles['Normal']))
            story.append(Paragraph(f"Validation Pass Rate: {summary.get('validation_pass_rate', 0):.1f}%", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Consolidated Data
            consolidated = data.get("consolidated_data", {})
            if consolidated:
                story.append(Paragraph("<b>Consolidated Property Data</b>", styles['Heading2']))
                
                # Create table data
                table_data = [["Field", "Value"]]
                for key, value in consolidated.items():
                    if isinstance(value, list):
                        value = "; ".join(str(v) for v in value[:3])  # Limit to first 3 items
                    table_data.append([key.replace('_', ' ').title(), str(value)])
                
                # Create table
                table = Table(table_data, colWidths=[2*inch, 4*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
            
            # Build PDF
            doc.build(story)
            self.logger.info(f"Exported PDF: {file_path}")
            return str(file_path)
            
        except ImportError:
            self.logger.warning("reportlab not available, skipping PDF export")
            return ""
        except Exception as e:
            self.logger.error(f"Error creating PDF: {str(e)}")
            return ""
    
    async def _send_to_deal_analyzer(self, data: Dict[str, Any]):
        """Send data to deal analyzer pipeline"""
        
        # Create deal analyzer input file
        analyzer_file = self.output_dir / "deal_analyzer_input.json"
        
        # Extract relevant data for deal analysis
        consolidated = data.get("consolidated_data", {})
        deal_data = {
            "property": {
                "address": consolidated.get("address"),
                "beds": consolidated.get("beds"),
                "baths": consolidated.get("baths"),
                "sqft": consolidated.get("sqft"),
                "year_built": consolidated.get("year_built"),
                "estimated_value": consolidated.get("avm_estimate"),
                "listing_price": consolidated.get("price"),
                "status": consolidated.get("status")
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "data_quality": data.get("summary", {}).get("recommendation", "UNKNOWN"),
            "confidence_scores": data.get("confidence_scores", {}),
            "sources": data.get("metadata", {}).get("sources", [])
        }
        
        with open(analyzer_file, 'w') as f:
            json.dump(deal_data, f, indent=2, default=str)
        
        self.logger.info(f"Deal analyzer input saved: {analyzer_file}")
        
        # TODO: Implement webhook or API call to actual deal analyzer
        # await self._call_deal_analyzer_api(deal_data)
    
    async def _generate_notifications(self, data: Dict[str, Any], exported_files: Dict[str, str]):
        """Generate notifications for CRM and alerts"""
        
        # Create notification summary
        summary = data.get("summary", {})
        consolidated = data.get("consolidated_data", {})
        
        notification = {
            "type": "property_data_extracted",
            "timestamp": datetime.now().isoformat(),
            "address": consolidated.get("address", "Unknown"),
            "status": consolidated.get("status", "Unknown"),
            "data_quality": summary.get("recommendation", "Unknown"),
            "sources_count": summary.get("total_sources", 0),
            "exported_files": exported_files,
            "requires_attention": summary.get("recommendation", "").startswith("POOR")
        }
        
        # Save notification
        notification_file = self.output_dir / "notifications.json"
        
        # Load existing notifications
        notifications = []
        if notification_file.exists():
            try:
                with open(notification_file, 'r') as f:
                    notifications = json.load(f)
            except:
                notifications = []
        
        notifications.append(notification)
        
        # Keep only last 100 notifications
        notifications = notifications[-100:]
        
        with open(notification_file, 'w') as f:
            json.dump(notifications, f, indent=2, default=str)
        
        self.logger.info(f"Notification generated: {notification['type']}")
        
        # TODO: Implement actual CRM integration
        # await self._send_to_crm(notification)
    
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filenames"""
        import re
        # Remove special characters, keep alphanumeric and basic punctuation
        sanitized = re.sub(r'[^\w\s\-\.]', '', text)
        # Replace spaces with underscores
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized.strip()[:50]  # Limit length
