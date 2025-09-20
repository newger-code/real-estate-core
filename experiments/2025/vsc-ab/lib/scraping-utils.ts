
import * as cheerio from 'cheerio';
import { proxyManager } from './proxy-config';
import { prisma } from './db';
import crypto from 'crypto-js';
import winston from 'winston';

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
  ]
});

export interface ScrapingResult {
  success: boolean;
  data: any;
  error?: string;
  duration?: number;
}

export interface PropertyData {
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
}

export interface AVMData {
  provider: string;
  estimate: number;
  confidence?: number;
  lowRange?: number;
  highRange?: number;
}

export class ScrapingUtils {
  private static rateLimitMap = new Map<string, number>();
  private static readonly RATE_LIMIT_WINDOW = 60000; // 1 minute
  private static readonly MAX_REQUESTS_PER_WINDOW = 10;

  static async enforceRateLimit(provider: string): Promise<void> {
    const now = Date.now();
    const windowStart = Math.floor(now / this.RATE_LIMIT_WINDOW) * this.RATE_LIMIT_WINDOW;
    const key = `${provider}_${windowStart}`;
    
    const requestCount = this.rateLimitMap.get(key) || 0;
    if (requestCount >= this.MAX_REQUESTS_PER_WINDOW) {
      const waitTime = windowStart + this.RATE_LIMIT_WINDOW - now;
      logger.info(`Rate limit reached for ${provider}, waiting ${waitTime}ms`);
      await this.delay(waitTime);
    }
    
    this.rateLimitMap.set(key, requestCount + 1);
  }

  static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  static generatePropertyHash(address: string, city: string, state: string, zipCode: string): string {
    const propertyString = `${address.toLowerCase()}_${city.toLowerCase()}_${state.toLowerCase()}_${zipCode}`;
    return crypto.MD5(propertyString).toString();
  }

  static parsePrice(priceString: string): number | null {
    if (!priceString) return null;
    
    const cleaned = priceString.replace(/[,$\s]/g, '');
    const match = cleaned.match(/(\d+(?:\.\d+)?)/);
    
    if (match) {
      const value = parseFloat(match[1]);
      // Handle K, M suffixes
      if (priceString.toLowerCase().includes('k')) return value * 1000;
      if (priceString.toLowerCase().includes('m')) return value * 1000000;
      return value;
    }
    
    return null;
  }

  static parseSquareFootage(sqftString: string): number | null {
    if (!sqftString) return null;
    
    const cleaned = sqftString.replace(/[,\s]/g, '');
    const match = cleaned.match(/(\d+)/);
    
    return match ? parseInt(match[1]) : null;
  }

  static parseBedroomsBathrooms(roomString: string): { bedrooms?: number; bathrooms?: number } {
    const result: { bedrooms?: number; bathrooms?: number } = {};
    
    if (!roomString) return result;
    
    // Match patterns like "3 bed, 2 bath" or "3bd/2ba"
    const bedMatch = roomString.match(/(\d+)\s*(?:bed|bd|bedroom)/i);
    const bathMatch = roomString.match(/(\d+(?:\.\d+)?)\s*(?:bath|ba|bathroom)/i);
    
    if (bedMatch) result.bedrooms = parseInt(bedMatch[1]);
    if (bathMatch) result.bathrooms = parseFloat(bathMatch[1]);
    
    return result;
  }

  static async logScrapingAttempt(
    provider: string,
    propertyId: string | null,
    status: 'success' | 'failed' | 'partial',
    startTime: Date,
    endTime: Date = new Date(),
    dataPoints?: number,
    errorMessage?: string,
    proxyUsed?: string
  ): Promise<void> {
    try {
      await prisma.scrapingLog.create({
        data: {
          propertyId,
          provider,
          status,
          startTime,
          endTime,
          duration: endTime.getTime() - startTime.getTime(),
          dataPoints,
          errorMessage,
          proxyUsed
        }
      });
    } catch (error) {
      logger.error('Failed to log scraping attempt:', error);
    }
  }

  static async fetchWithRetry(
    url: string,
    options: any = {},
    maxRetries: number = 3
  ): Promise<string> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        logger.info(`Fetching ${url} (attempt ${attempt}/${maxRetries})`);
        
        const response = await proxyManager.getAxiosInstance().get(url, {
          ...options,
          headers: {
            'User-Agent': this.getRandomUserAgent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            ...options.headers
          }
        });
        
        const html = response.data;
        if (!html || html.length < 100) {
          throw new Error('Received empty or suspiciously small response');
        }
        
        return html;
      } catch (error: any) {
        lastError = error;
        logger.warn(`Attempt ${attempt} failed for ${url}:`, error?.message);
        
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          logger.info(`Waiting ${delay}ms before retry...`);
          await this.delay(delay);
        }
      }
    }
    
    throw new Error(`Failed to fetch ${url} after ${maxRetries} attempts: ${lastError?.message}`);
  }

  static getRandomUserAgent(): string {
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
    ];
    
    return userAgents[Math.floor(Math.random() * userAgents.length)];
  }

  static parseHTML(html: string): cheerio.CheerioAPI {
    return cheerio.load(html);
  }

  static cleanText(text: string): string {
    return text?.trim()?.replace(/\s+/g, ' ')?.replace(/[^\x20-\x7E]/g, '') || '';
  }

  static isValidPrice(price: number | null): boolean {
    return price !== null && price > 0 && price < 50000000; // Reasonable price range
  }

  static async savePropertyData(propertyData: PropertyData): Promise<string> {
    try {
      const property = await prisma.property.upsert({
        where: {
          address_city_state_zipCode: {
            address: propertyData.address,
            city: propertyData.city,
            state: propertyData.state,
            zipCode: propertyData.zipCode
          }
        },
        update: {
          ...propertyData,
          lastUpdated: new Date()
        },
        create: {
          ...propertyData,
          id: this.generatePropertyHash(
            propertyData.address,
            propertyData.city,
            propertyData.state,
            propertyData.zipCode
          )
        }
      });

      return property.id;
    } catch (error) {
      logger.error('Failed to save property data:', error);
      throw error;
    }
  }

  static async saveAVMEstimate(propertyId: string, avmData: AVMData): Promise<void> {
    try {
      await prisma.aVMEstimate.upsert({
        where: {
          propertyId_provider: {
            propertyId,
            provider: avmData.provider
          }
        },
        update: {
          estimate: avmData.estimate,
          confidence: avmData.confidence,
          lowRange: avmData.lowRange,
          highRange: avmData.highRange,
          lastUpdated: new Date()
        },
        create: {
          propertyId,
          provider: avmData.provider,
          estimate: avmData.estimate,
          confidence: avmData.confidence,
          lowRange: avmData.lowRange,
          highRange: avmData.highRange
        }
      });

      logger.info(`Saved AVM estimate for ${propertyId} from ${avmData.provider}: $${avmData.estimate}`);
    } catch (error) {
      logger.error('Failed to save AVM estimate:', error);
      throw error;
    }
  }
}
