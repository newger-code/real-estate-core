
import { HomesComScraper } from './avm-scrapers/homes-com-scraper';
import { ZillowScraper } from './avm-scrapers/zillow-scraper';
import { MovotoScraper } from './avm-scrapers/movoto-scraper';
import { RedfinScraper } from './avm-scrapers/redfin-scraper';
import { RealtorComScraper } from './avm-scrapers/realtor-com-scraper';
import { ScrapingUtils, ScrapingResult } from './scraping-utils';
import { prisma } from './db';
import winston from 'winston';
import pLimit from 'p-limit';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

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
  scrapingResults: Record<string, ScrapingResult>;
  analysisTimestamp: Date;
}

export class AVMAggregator {
  private static readonly SCRAPERS = [
    { name: 'homes_com', scraper: HomesComScraper },
    { name: 'zillow', scraper: ZillowScraper },
    { name: 'movoto', scraper: MovotoScraper },
    { name: 'redfin', scraper: RedfinScraper },
    { name: 'realtor_com', scraper: RealtorComScraper }
  ];
  
  private static readonly CONCURRENT_SCRAPERS = 2; // Limit concurrent requests to avoid rate limiting
  private static readonly RETRY_ATTEMPTS = 2;
  
  static async analyzeProperty(
    address: string,
    city: string,
    state: string,
    zipCode: string
  ): Promise<PropertyAnalysisResult> {
    const analysisStartTime = Date.now();
    const scrapingResults: Record<string, ScrapingResult> = {};
    
    logger.info(`Starting comprehensive AVM analysis for: ${address}, ${city}, ${state} ${zipCode}`);
    
    // Use p-limit to control concurrency
    const limit = pLimit(this.CONCURRENT_SCRAPERS);
    
    // Create scraping tasks
    const scrapingTasks = this.SCRAPERS.map(({ name, scraper }) =>
      limit(async () => {
        logger.info(`Starting ${name} scraper...`);
        
        let result: ScrapingResult;
        let attempts = 0;
        
        do {
          attempts++;
          try {
            result = await scraper.scrapeAVM(address, city, state, zipCode);
            
            if (result.success) {
              logger.info(`${name} scraping completed successfully`);
              break;
            } else if (attempts < this.RETRY_ATTEMPTS) {
              logger.warn(`${name} scraping failed (attempt ${attempts}), retrying...`);
              await ScrapingUtils.delay(2000 * attempts); // Progressive delay
            }
          } catch (error: any) {
            logger.error(`${name} scraping error (attempt ${attempts}):`, error?.message);
            result = {
              success: false,
              data: null,
              error: error?.message,
              duration: 0
            };
          }
        } while (attempts < this.RETRY_ATTEMPTS && !result!.success);
        
        scrapingResults[name] = result!;
        return result!;
      })
    );
    
    // Execute all scraping tasks concurrently
    await Promise.allSettled(scrapingTasks);
    
    // Get property ID from first successful scraper
    let propertyId: string | null = null;
    for (const result of Object.values(scrapingResults)) {
      if (result.success && result.data?.property) {
        const propertyHash = ScrapingUtils.generatePropertyHash(address, city, state, zipCode);
        propertyId = propertyHash;
        break;
      }
    }
    
    if (!propertyId) {
      throw new Error('Failed to identify property from any scraping source');
    }
    
    // Fetch all AVM estimates from database
    const avmEstimates = await this.fetchAVMEstimates(propertyId);
    
    // Calculate analysis metrics
    const analysis = this.calculateAnalysisMetrics(avmEstimates);
    
    const totalDuration = Date.now() - analysisStartTime;
    
    logger.info(`AVM analysis completed in ${totalDuration}ms. Found ${avmEstimates.length} estimates with average: $${analysis.averageEstimate}`);
    
    return {
      propertyId,
      address,
      city,
      state,
      zipCode,
      avmEstimates,
      averageEstimate: analysis.averageEstimate,
      estimateRange: analysis.estimateRange,
      confidence: analysis.confidence,
      scrapingResults,
      analysisTimestamp: new Date()
    };
  }
  
  private static async fetchAVMEstimates(propertyId: string) {
    try {
      const estimates = await prisma.aVMEstimate.findMany({
        where: { propertyId },
        orderBy: { lastUpdated: 'desc' }
      });
      
      return estimates.map(est => ({
        provider: est.provider,
        estimate: est.estimate,
        confidence: est.confidence ?? undefined,
        lowRange: est.lowRange ?? undefined,
        highRange: est.highRange ?? undefined,
        lastUpdated: est.lastUpdated
      }));
    } catch (error: any) {
      logger.error('Error fetching AVM estimates:', error?.message);
      return [];
    }
  }
  
  private static calculateAnalysisMetrics(estimates: any[]) {
    if (estimates.length === 0) {
      return {
        averageEstimate: 0,
        estimateRange: { min: 0, max: 0 },
        confidence: { overall: 0, byProvider: {} }
      };
    }
    
    const validEstimates = estimates.filter(est => ScrapingUtils.isValidPrice(est.estimate));
    
    if (validEstimates.length === 0) {
      return {
        averageEstimate: 0,
        estimateRange: { min: 0, max: 0 },
        confidence: { overall: 0, byProvider: {} }
      };
    }
    
    // Calculate average estimate
    const averageEstimate = validEstimates.reduce((sum, est) => sum + est.estimate, 0) / validEstimates.length;
    
    // Calculate estimate range
    const estimateValues = validEstimates.map(est => est.estimate);
    const estimateRange = {
      min: Math.min(...estimateValues),
      max: Math.max(...estimateValues)
    };
    
    // Calculate confidence metrics
    const confidenceByProvider: Record<string, number> = {};
    let totalConfidence = 0;
    let confidenceCount = 0;
    
    for (const est of validEstimates) {
      if (est.confidence) {
        confidenceByProvider[est.provider] = est.confidence;
        totalConfidence += est.confidence;
        confidenceCount++;
      } else {
        // Assign default confidence based on provider reliability
        const defaultConfidence = this.getDefaultConfidence(est.provider);
        confidenceByProvider[est.provider] = defaultConfidence;
        totalConfidence += defaultConfidence;
        confidenceCount++;
      }
    }
    
    const overallConfidence = confidenceCount > 0 ? totalConfidence / confidenceCount : 0;
    
    // Adjust overall confidence based on estimate consistency
    const standardDeviation = this.calculateStandardDeviation(estimateValues);
    const coefficientOfVariation = standardDeviation / averageEstimate;
    
    // Lower confidence if estimates vary too much
    const consistencyMultiplier = Math.max(0.5, 1 - coefficientOfVariation);
    const adjustedConfidence = overallConfidence * consistencyMultiplier;
    
    return {
      averageEstimate: Math.round(averageEstimate),
      estimateRange,
      confidence: {
        overall: Math.round(adjustedConfidence),
        byProvider: confidenceByProvider
      }
    };
  }
  
  private static getDefaultConfidence(provider: string): number {
    // Default confidence levels based on provider reliability
    const defaultConfidences: Record<string, number> = {
      'homes_com_corelogic': 85,
      'homes_com_collateral': 80,
      'homes_com_quantarium': 75,
      'homes_com_regeodata': 70,
      'homes_com_homesgenie': 65,
      'zillow': 80,
      'redfin': 85,
      'realtor_com': 75,
      'movoto': 70
    };
    
    return defaultConfidences[provider] || 65;
  }
  
  private static calculateStandardDeviation(values: number[]): number {
    if (values.length <= 1) return 0;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDifferences = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDifferences.reduce((sum, val) => sum + val, 0) / values.length;
    
    return Math.sqrt(variance);
  }
  
  static async getPropertyAnalysis(propertyId: string): Promise<PropertyAnalysisResult | null> {
    try {
      const property = await prisma.property.findUnique({
        where: { id: propertyId },
        include: {
          avmEstimates: {
            orderBy: { lastUpdated: 'desc' }
          }
        }
      });
      
      if (!property) {
        return null;
      }
      
      const avmEstimates = property.avmEstimates.map(est => ({
        provider: est.provider,
        estimate: est.estimate,
        confidence: est.confidence ?? undefined,
        lowRange: est.lowRange ?? undefined,
        highRange: est.highRange ?? undefined,
        lastUpdated: est.lastUpdated
      }));
      
      const analysis = this.calculateAnalysisMetrics(avmEstimates);
      
      return {
        propertyId: property.id,
        address: property.address,
        city: property.city,
        state: property.state,
        zipCode: property.zipCode,
        avmEstimates,
        averageEstimate: analysis.averageEstimate,
        estimateRange: analysis.estimateRange,
        confidence: analysis.confidence,
        scrapingResults: {},
        analysisTimestamp: new Date()
      };
    } catch (error: any) {
      logger.error('Error getting property analysis:', error?.message);
      return null;
    }
  }
}
