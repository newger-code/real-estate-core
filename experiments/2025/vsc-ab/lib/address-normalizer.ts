
// Removed node-postal dependency to avoid native binding issues
import Fuse from 'fuse.js';
import winston from 'winston';

// US States mapping for normalization
const US_STATES = {
  'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
  'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
  'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
  'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
  'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
  'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ',
  'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
  'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
  'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT',
  'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
  'DISTRICT OF COLUMBIA': 'DC', 'WASHINGTON DC': 'DC', 'WASHINGTON D.C.': 'DC'
};

// Street suffix normalization
const STREET_SUFFIXES = {
  'AVENUE': 'Ave', 'AVE': 'Ave', 'AV': 'Ave',
  'STREET': 'St', 'STR': 'St', 'ST': 'St',
  'BOULEVARD': 'Blvd', 'BLVD': 'Blvd', 'BL': 'Blvd',
  'DRIVE': 'Dr', 'DR': 'Dr', 'DRV': 'Dr',
  'LANE': 'Ln', 'LN': 'Ln', 'LA': 'Ln',
  'ROAD': 'Rd', 'RD': 'Rd', 'RO': 'Rd',
  'PLACE': 'Pl', 'PL': 'Pl', 'PLC': 'Pl',
  'COURT': 'Ct', 'CT': 'Ct', 'CRT': 'Ct',
  'CIRCLE': 'Cir', 'CIR': 'Cir', 'CIRC': 'Cir',
  'PARKWAY': 'Pkwy', 'PKWY': 'Pkwy', 'PKY': 'Pkwy',
  'TERRACE': 'Ter', 'TER': 'Ter', 'TERR': 'Ter',
  'WAY': 'Way', 'WY': 'Way'
};

// Directional normalization
const DIRECTIONALS = {
  'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W',
  'NORTHEAST': 'NE', 'NORTHWEST': 'NW', 'SOUTHEAST': 'SE', 'SOUTHWEST': 'SW'
};

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

export interface NormalizedAddress {
  original: string;
  normalized: string;
  components: {
    houseNumber?: string;
    streetName?: string;
    streetSuffix?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country?: string;
    unitType?: string;
    unitNumber?: string;
    preDirection?: string;
    postDirection?: string;
  };
  confidence: number;
  suggestions?: string[];
  method: 'postal' | 'regex' | 'fuzzy' | 'fallback';
  errors?: string[];
}

export interface AddressSearchSuggestion {
  address: string;
  confidence: number;
  source: 'database' | 'external' | 'cache';
  components: NormalizedAddress['components'];
}

export class AddressNormalizer {
  private fuse: Fuse<any> | null = null;
  private cache = new Map<string, NormalizedAddress>();
  private suggestionCache = new Map<string, AddressSearchSuggestion[]>();

  constructor() {
    this.initializeFuzzySearch();
  }

  /**
   * Initialize fuzzy search with common address patterns
   */
  private initializeFuzzySearch() {
    try {
      this.fuse = new Fuse([], {
        keys: ['address', 'city', 'state'],
        threshold: 0.3,
        minMatchCharLength: 3
      });
    } catch (error) {
      logger.warn('Failed to initialize fuzzy search:', error);
    }
  }

  /**
   * Primary method to normalize an address
   */
  async normalizeAddress(address: string): Promise<NormalizedAddress> {
    const cacheKey = address.toLowerCase().trim();
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      logger.debug(`Address normalization cache hit: ${address}`);
      return this.cache.get(cacheKey)!;
    }

    let result: NormalizedAddress;

    try {
      // Use regex-based normalization (removed postal dependency for compatibility)
      result = await this.normalizeWithRegex(address);
    } catch (error) {
      logger.warn(`Address normalization failed for "${address}":`, error);
      // Fallback to basic normalization
      result = await this.normalizeWithBasicFallback(address);
    }

    // Cache the result
    this.cache.set(cacheKey, result);
    
    // Log normalization activity
    logger.info(`Address normalized: "${address}" -> "${result.normalized}" (confidence: ${result.confidence}, method: ${result.method})`);

    return result;
  }

  /**
   * Basic fallback normalization method
   */
  private async normalizeWithBasicFallback(address: string): Promise<NormalizedAddress> {
    const components: NormalizedAddress['components'] = {};
    const errors: string[] = ['Using basic fallback normalization'];
    
    // Very basic parsing - just extract what we can
    const parts = address.split(',').map(p => p.trim());
    
    if (parts.length >= 3) {
      // Try to extract basic components
      const addressPart = parts[0];
      const cityPart = parts[1];
      const stateZipPart = parts[2];
      
      // Extract house number if present
      const houseMatch = addressPart.match(/^(\d+)\s+(.+)$/);
      if (houseMatch) {
        components.houseNumber = houseMatch[1];
        components.streetName = this.capitalizeWords(houseMatch[2]);
      } else {
        components.streetName = this.capitalizeWords(addressPart);
      }
      
      components.city = this.capitalizeWords(cityPart);
      
      // Try to extract state and ZIP from last part
      const stateZipMatch = stateZipPart.match(/([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?/i);
      if (stateZipMatch) {
        components.state = stateZipMatch[1].toUpperCase();
        if (stateZipMatch[2]) {
          components.zipCode = stateZipMatch[2];
        }
      }
    } else {
      errors.push('Address format not recognized - using as-is');
    }

    const normalized = components.houseNumber && components.streetName 
      ? this.buildNormalizedAddress(components)
      : address;
    
    return Promise.resolve({
      original: address,
      normalized,
      components,
      confidence: 0.5, // Low confidence for fallback method
      method: 'fallback',
      errors
    });
  }

  /**
   * Normalize address using regex patterns (fallback method)
   */
  private normalizeWithRegex(address: string): Promise<NormalizedAddress> {
    const components: NormalizedAddress['components'] = {};
    const errors: string[] = [];
    
    try {
      // Enhanced regex patterns for US addresses
      const patterns = {
        // Basic pattern: 123 Main St, City, ST 12345
        full: /^(\d+(?:\s+\w+)?)\s+(.+?),\s*(.+?),?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$/i,
        // Without zip: 123 Main St, City, ST
        noZip: /^(\d+(?:\s+\w+)?)\s+(.+?),\s*(.+?),?\s*([A-Z]{2})$/i,
        // Street only: 123 Main Street
        streetOnly: /^(\d+(?:\s+\w+)?)\s+(.+)$/i,
        // With unit: 123 Main St #456, City, ST 12345
        withUnit: /^(\d+(?:\s+\w+)?)\s+(.+?)\s+(#|apt|unit|suite)\s*(\w+),?\s*(.+?),?\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?$/i
      };

      let matched = false;

      // Try full pattern first
      let match = address.match(patterns.full);
      if (match) {
        components.houseNumber = match[1].trim();
        components.streetName = this.normalizeStreetName(match[2].trim());
        components.city = this.capitalizeWords(match[3].trim());
        components.state = this.normalizeState(match[4].trim());
        components.zipCode = this.normalizeZipCode(match[5].trim());
        matched = true;
      }

      // Try pattern with unit
      if (!matched) {
        match = address.match(patterns.withUnit);
        if (match) {
          components.houseNumber = match[1].trim();
          components.streetName = this.normalizeStreetName(match[2].trim());
          components.unitType = match[3].trim();
          components.unitNumber = match[4].trim();
          components.city = this.capitalizeWords(match[5].trim());
          components.state = this.normalizeState(match[6].trim());
          components.zipCode = match[7] ? this.normalizeZipCode(match[7].trim()) : undefined;
          matched = true;
        }
      }

      // Try no zip pattern
      if (!matched) {
        match = address.match(patterns.noZip);
        if (match) {
          components.houseNumber = match[1].trim();
          components.streetName = this.normalizeStreetName(match[2].trim());
          components.city = this.capitalizeWords(match[3].trim());
          components.state = this.normalizeState(match[4].trim());
          matched = true;
        }
      }

      // Try street only pattern (lowest confidence)
      if (!matched) {
        match = address.match(patterns.streetOnly);
        if (match) {
          components.houseNumber = match[1].trim();
          components.streetName = this.normalizeStreetName(match[2].trim());
          matched = true;
          errors.push('Incomplete address - missing city, state, or ZIP code');
        }
      }

      if (!matched) {
        errors.push('Unable to parse address with regex patterns');
      }

      const normalized = this.buildNormalizedAddress(components);
      const confidence = this.calculateConfidence(components, 'regex');

      return Promise.resolve({
        original: address,
        normalized,
        components,
        confidence,
        method: 'regex',
        errors
      });
    } catch (error) {
      logger.error('Regex normalization failed:', error);
      return Promise.resolve({
        original: address,
        normalized: address,
        components: {},
        confidence: 0.1,
        method: 'fallback',
        errors: [String(error)]
      });
    }
  }

  /**
   * Get address suggestions for auto-complete functionality
   */
  async getAddressSuggestions(partial: string, limit: number = 5): Promise<AddressSearchSuggestion[]> {
    const cacheKey = `${partial.toLowerCase()}_${limit}`;
    
    if (this.suggestionCache.has(cacheKey)) {
      return this.suggestionCache.get(cacheKey)!;
    }

    const suggestions: AddressSearchSuggestion[] = [];

    // Method 1: Check if partial looks like start of address
    if (/^\d+\s+\w/.test(partial.trim())) {
      // This looks like it starts with a house number
      const enhancedSuggestions = await this.generateAddressSuggestions(partial);
      suggestions.push(...enhancedSuggestions);
    }

    // Method 2: City/State suggestions
    if (partial.includes(',') || partial.length > 10) {
      const locationSuggestions = await this.generateLocationSuggestions(partial);
      suggestions.push(...locationSuggestions);
    }

    // Cache and return
    const limitedSuggestions = suggestions.slice(0, limit);
    this.suggestionCache.set(cacheKey, limitedSuggestions);
    
    return limitedSuggestions;
  }

  /**
   * Generate address suggestions based on partial input
   */
  private async generateAddressSuggestions(partial: string): Promise<AddressSearchSuggestion[]> {
    const suggestions: AddressSearchSuggestion[] = [];
    
    // This would typically integrate with external APIs like Google Places, 
    // Here we'll create some mock suggestions based on the partial input
    
    const commonStreets = ['Main St', 'Oak Ave', 'Elm St', 'Park Rd', 'First Ave', 'Second St'];
    const match = partial.match(/^(\d+)\s+(.*)$/);
    
    if (match) {
      const houseNumber = match[1];
      const streetStart = match[2].toLowerCase();
      
      commonStreets.forEach(street => {
        if (street.toLowerCase().startsWith(streetStart)) {
          const fullAddress = `${houseNumber} ${street}`;
          suggestions.push({
            address: fullAddress,
            confidence: 0.8,
            source: 'database',
            components: {
              houseNumber,
              streetName: street.split(' ')[0],
              streetSuffix: street.split(' ')[1]
            }
          });
        }
      });
    }

    return suggestions;
  }

  /**
   * Generate location (city/state) suggestions
   */
  private async generateLocationSuggestions(partial: string): Promise<AddressSearchSuggestion[]> {
    const suggestions: AddressSearchSuggestion[] = [];
    
    // Common US cities for demonstration
    const commonCities = [
      'Akron, OH', 'Cleveland, OH', 'Columbus, OH', 'Cincinnati, OH', 'Toledo, OH',
      'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX', 'Phoenix, AZ'
    ];
    
    const searchTerm = partial.toLowerCase();
    
    commonCities.forEach(cityState => {
      if (cityState.toLowerCase().includes(searchTerm)) {
        const [city, state] = cityState.split(', ');
        suggestions.push({
          address: cityState,
          confidence: 0.9,
          source: 'database',
          components: {
            city,
            state
          }
        });
      }
    });

    return suggestions;
  }

  /**
   * Normalize street name
   */
  private normalizeStreetName(street: string): string {
    let normalized = street.trim().toUpperCase();
    
    // Replace street suffixes
    Object.entries(STREET_SUFFIXES).forEach(([old, newSuffix]) => {
      const regex = new RegExp(`\\b${old}\\b$`, 'i');
      normalized = normalized.replace(regex, newSuffix);
    });

    // Replace directionals
    Object.entries(DIRECTIONALS).forEach(([old, newDir]) => {
      const regex = new RegExp(`\\b${old}\\b`, 'gi');
      normalized = normalized.replace(regex, newDir);
    });

    return this.capitalizeWords(normalized);
  }

  /**
   * Normalize state name or abbreviation
   */
  private normalizeState(state: string): string {
    const normalized = state.trim().toUpperCase();
    
    // If it's already a 2-letter code, return it
    if (normalized.length === 2 && /^[A-Z]{2}$/.test(normalized)) {
      return normalized;
    }
    
    // Try to find full state name
    return (US_STATES as Record<string, string>)[normalized] || normalized;
  }

  /**
   * Normalize ZIP code
   */
  private normalizeZipCode(zip: string): string {
    const cleaned = zip.trim().replace(/[^\d-]/g, '');
    
    // Ensure 5-digit format or 5+4 format
    if (/^\d{5}$/.test(cleaned)) {
      return cleaned;
    } else if (/^\d{5}-?\d{4}$/.test(cleaned)) {
      return cleaned.includes('-') ? cleaned : cleaned.slice(0, 5) + '-' + cleaned.slice(5);
    }
    
    return cleaned;
  }

  /**
   * Capitalize words properly
   */
  private capitalizeWords(text: string): string {
    return text.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Build normalized address string from components
   */
  private buildNormalizedAddress(components: NormalizedAddress['components']): string {
    const parts: string[] = [];

    if (components.houseNumber) {
      parts.push(components.houseNumber);
    }

    if (components.preDirection) {
      parts.push(components.preDirection);
    }

    if (components.streetName) {
      let streetPart = components.streetName;
      if (components.streetSuffix) {
        streetPart += ' ' + components.streetSuffix;
      }
      parts.push(streetPart);
    }

    if (components.postDirection) {
      parts.push(components.postDirection);
    }

    if (components.unitType && components.unitNumber) {
      parts.push(`${components.unitType} ${components.unitNumber}`);
    }

    let addressLine = parts.join(' ');

    if (components.city) {
      addressLine += ', ' + components.city;
    }

    if (components.state) {
      addressLine += ', ' + components.state;
    }

    if (components.zipCode) {
      addressLine += ' ' + components.zipCode;
    }

    return addressLine.trim();
  }

  /**
   * Calculate confidence score based on completeness and method
   */
  private calculateConfidence(components: NormalizedAddress['components'], method: string): number {
    let score = 0;
    let maxScore = 0;

    // Required components
    if (components.houseNumber) score += 20; maxScore += 20;
    if (components.streetName) score += 25; maxScore += 25;
    if (components.city) score += 20; maxScore += 20;
    if (components.state) score += 15; maxScore += 15;
    if (components.zipCode) score += 10; maxScore += 10;

    // Optional components
    if (components.streetSuffix) score += 5; maxScore += 5;
    if (components.preDirection || components.postDirection) score += 3; maxScore += 3;
    if (components.unitType && components.unitNumber) score += 2; maxScore += 2;

    let confidence = maxScore > 0 ? score / maxScore : 0;

    // Method-based adjustment
    switch (method) {
      case 'postal':
        confidence *= 1.0; // Best method
        break;
      case 'regex':
        confidence *= 0.85; // Good but not as reliable
        break;
      case 'fuzzy':
        confidence *= 0.7; // Less reliable
        break;
      default:
        confidence *= 0.5; // Fallback
    }

    return Math.round(confidence * 100) / 100;
  }

  /**
   * Clear caches (useful for memory management)
   */
  clearCache(): void {
    this.cache.clear();
    this.suggestionCache.clear();
    logger.info('Address normalizer caches cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { normalizations: number; suggestions: number } {
    return {
      normalizations: this.cache.size,
      suggestions: this.suggestionCache.size
    };
  }
}

// Export singleton instance
export const addressNormalizer = new AddressNormalizer();
