# Homes.com Smart Scraper

Advanced property data scraper for Homes.com using smart pattern-based extraction.

## Features

- Smart content-based data extraction using regex patterns
- Extracts 19+ property data fields including AVM values
- Handles dynamic content loading with deep scrolling
- Popup blocker detection and handling
- URL-based property page detection
- Human-like browsing behaviors

## Files

- `scrape_property.py` - Main scraper with navigation and extraction
- `smart_extraction.py` - Modular pattern-based extraction engine

## Usage

```bash
NO_PROXY=true python scrape_property.py "1240 Pondview Ave, Akron, OH 44305" homes
```

## Data Fields Extracted

- Core property data (price, beds, baths, sqft)
- AVM provider values (4+ providers)
- Property details and type inference
- Tax and financial history
- Demographics and environmental factors
- School information
- Similar homes data

## Status

Current extraction success: 19/38 target fields
Latest version includes AVM dollar value extraction through enhanced deep scrolling.