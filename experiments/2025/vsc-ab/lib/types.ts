
// Core data types for the real estate analytics application

export interface PropertyData {
  id: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  latitude?: number;
  longitude?: number;
  propertyType?: string;
  bedrooms?: number;
  bathrooms?: number;
  squareFootage?: number;
  lotSize?: number;
  yearBuilt?: number;
  lastUpdated: Date;
  createdAt: Date;
}

export interface AVMEstimate {
  id: string;
  propertyId: string;
  provider: string;
  estimate: number;
  confidence?: number;
  lowRange?: number;
  highRange?: number;
  lastUpdated: Date;
  createdAt: Date;
}

export interface PropertyPhoto {
  id: string;
  propertyId: string;
  url: string;
  caption?: string;
  photoType?: 'exterior' | 'interior' | 'aerial' | 'street_view';
  order: number;
  createdAt: Date;
}

export interface TaxAssessment {
  id: string;
  propertyId: string;
  assessedValue?: number;
  taxableValue?: number;
  annualTaxes?: number;
  taxYear?: number;
  millageRate?: number;
  exemptions?: any;
  lastUpdated: Date;
}

export interface PropertyHistory {
  id: string;
  propertyId: string;
  eventType: 'sale' | 'listing' | 'price_change' | 'status_change' | 'tax_assessment';
  eventDate: Date;
  price?: number;
  pricePerSqFt?: number;
  status?: string;
  daysOnMarket?: number;
  listingAgent?: string;
  buyerAgent?: string;
  description?: string;
  createdAt: Date;
}

export interface SchoolInfo {
  id: string;
  propertyId: string;
  schoolName: string;
  schoolType: 'elementary' | 'middle' | 'high' | 'private';
  district?: string;
  rating?: number;
  grades?: string;
  distance?: number;
  enrollment?: number;
  testScores?: any;
}

export interface NeighborhoodData {
  id: string;
  propertyId: string;
  walkScore?: number;
  crimeScore?: number;
  medianHouseholdIncome?: number;
  populationDensity?: number;
  averageCommute?: number;
  nearbyAmenities?: any;
  demographics?: any;
  marketTrends?: any;
  lastUpdated: Date;
}

export interface MarketAnalysis {
  id: string;
  propertyId: string;
  averageDaysOnMarket?: number;
  pricePerSqFtTrend?: number;
  inventoryLevel?: 'low' | 'medium' | 'high';
  seasonalTrend?: 'rising' | 'falling' | 'stable';
  competitiveLevel?: 'high' | 'medium' | 'low';
  bestListingMonth?: string;
  predictedPriceChange?: number;
  marketVelocity?: number;
  lastUpdated: Date;
}

export interface ComparableProperty {
  id: string;
  propertyId: string;
  comparableAddress: string;
  comparableCity: string;
  comparableState: string;
  distance?: number;
  squareFootage?: number;
  bedrooms?: number;
  bathrooms?: number;
  lotSize?: number;
  yearBuilt?: number;
  salePrice?: number;
  saleDate?: Date;
  daysOnMarket?: number;
  pricePerSqFt?: number;
  similarityScore?: number;
}

export interface PropertySearch {
  id: string;
  userId?: number;
  propertyId?: string;
  searchQuery: string;
  filters?: any;
  timestamp: Date;
  ipAddress?: string;
}

export interface ScrapingLog {
  id: string;
  propertyId?: string;
  provider: string;
  status: 'success' | 'failed' | 'partial';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  dataPoints?: number;
  errorMessage?: string;
  proxyUsed?: string;
}

// API Response Types
export interface PropertyAnalysisResult {
  propertyId: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  avmEstimates: Array<{
    provider: string;
    estimate: number;
    confidence?: number;
    lowRange?: number;
    highRange?: number;
    lastUpdated: Date;
  }>;
  averageEstimate: number;
  estimateRange: {
    min: number;
    max: number;
  };
  confidence: {
    overall: number;
    byProvider: Record<string, number>;
  };
  scrapingResults: Record<string, any>;
  analysisTimestamp: Date;
}

export interface DashboardAnalytics {
  success: boolean;
  timeframe: string;
  overview: {
    totalProperties: number;
    totalEstimates: number;
    recentSearches: number;
    successRate: number;
    averageEstimate: number;
  };
  providerStats: Array<{
    provider: string;
    count: number;
    averageEstimate: number;
  }>;
  searchTrends: Array<{
    date: string;
    searches: number;
  }>;
  scrapingStats: Array<{
    status: string;
    count: number;
  }>;
  recentActivity: Array<{
    provider: string;
    status: string;
    startTime: Date;
    duration?: number;
    dataPoints?: number;
    errorMessage?: string;
  }>;
  timestamp: Date;
}

// Form Types
export interface PropertySearchForm {
  address: string;
  city: string;
  state: string;
  zipCode: string;
}

// Utility Types
export type AVMProvider = 
  | 'homes_com_corelogic'
  | 'homes_com_collateral'
  | 'homes_com_quantarium'
  | 'homes_com_regeodata'
  | 'homes_com_homesgenie'
  | 'zillow'
  | 'movoto'
  | 'redfin'
  | 'realtor_com';

export type ScrapingStatus = 'success' | 'failed' | 'partial';

export type PropertyType = 'single_family' | 'condo' | 'townhouse' | 'multi_family' | 'land' | 'commercial';

export type SchoolType = 'elementary' | 'middle' | 'high' | 'private';

export type InventoryLevel = 'low' | 'medium' | 'high';

export type MarketTrend = 'rising' | 'falling' | 'stable';

export type CompetitiveLevel = 'high' | 'medium' | 'low';
