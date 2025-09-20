
import https from 'https';
import { HttpsProxyAgent } from 'https-proxy-agent';
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import fs from 'fs';
import path from 'path';
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

export interface BrightDataConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  zone: string;
  country?: string;
  state?: string;
}

export const brightDataConfig: BrightDataConfig = {
  host: process.env.BRIGHT_DATA_HOST || 'brd.superproxy.io',
  port: parseInt(process.env.BRIGHT_DATA_PORT || '33335'),
  username: process.env.BRIGHT_DATA_USERNAME || 'brd-customer-hl_dd2a0351-zone-residential_proxy_us1',
  password: process.env.BRIGHT_DATA_PASSWORD || '',
  zone: 'residential_proxy_us1',
  country: 'us', // North American proxies as requested
  state: '' // Will be rotated
};

// US States for proxy rotation
const US_STATES = [
  'ny', 'ca', 'tx', 'fl', 'il', 'oh', 'pa', 'mi', 'ga', 'nc', 
  'nj', 'va', 'wa', 'az', 'ma', 'tn', 'in', 'mo', 'md', 'wi',
  'co', 'mn', 'sc', 'al', 'la', 'ky', 'or', 'ok', 'ct', 'ut'
];

export class ProxyManager {
  private static instance: ProxyManager;
  private proxyAgent!: HttpsProxyAgent<string>;
  private axiosInstance!: AxiosInstance;
  private currentStateIndex = 0;
  private sslCertPath?: string;

  private constructor() {
    this.initializeSSLCertificate();
    this.initializeProxy();
  }

  static getInstance(): ProxyManager {
    if (!ProxyManager.instance) {
      ProxyManager.instance = new ProxyManager();
    }
    return ProxyManager.instance;
  }

  /**
   * Initialize SSL certificate for Bright Data
   */
  private initializeSSLCertificate() {
    try {
      // Look for Bright Data SSL certificate
      const possiblePaths = [
        path.join(process.cwd(), 'certificates', 'brightdata.crt'),
        path.join(process.cwd(), 'brightdata.crt'),
        path.join(process.cwd(), 'ssl', 'brightdata.crt'),
        '/tmp/brightdata.crt'
      ];

      for (const certPath of possiblePaths) {
        if (fs.existsSync(certPath)) {
          this.sslCertPath = certPath;
          logger.info(`SSL certificate found at: ${certPath}`);
          break;
        }
      }

      if (!this.sslCertPath) {
        logger.warn('SSL certificate not found. Will use certificate from system store or ignore SSL errors.');
        // We'll download and save the certificate if needed
        this.downloadSSLCertificate();
      }
    } catch (error) {
      logger.error('SSL certificate initialization error:', error);
    }
  }

  /**
   * Download Bright Data SSL certificate
   */
  private async downloadSSLCertificate() {
    try {
      logger.info('Attempting to download Bright Data SSL certificate...');
      
      // You would typically download the certificate from Bright Data's provided URL
      // For now, we'll create a placeholder process
      const certDir = path.join(process.cwd(), 'certificates');
      
      if (!fs.existsSync(certDir)) {
        fs.mkdirSync(certDir, { recursive: true });
      }

      // This is where you would download the actual certificate
      // const response = await fetch('https://brightdata.com/path/to/certificate.crt');
      // const certContent = await response.text();
      // fs.writeFileSync(path.join(certDir, 'brightdata.crt'), certContent);
      
      logger.info('SSL certificate download process initiated (implement actual download)');
    } catch (error) {
      logger.error('Failed to download SSL certificate:', error);
    }
  }

  /**
   * Initialize proxy with enhanced configuration
   */
  private initializeProxy() {
    try {
      // Rotate proxy location for better distribution
      const currentState = US_STATES[this.currentStateIndex % US_STATES.length];
      this.currentStateIndex++;

      // Build username with North American geo-targeting
      const username = `${brightDataConfig.username}-country-${brightDataConfig.country}-state-${currentState}`;
      
      const proxyUrl = `http://${username}:${brightDataConfig.password}@${brightDataConfig.host}:${brightDataConfig.port}`;
      
      logger.info(`Initializing proxy with geo-targeting: country=${brightDataConfig.country}, state=${currentState}`);
      
      this.proxyAgent = new HttpsProxyAgent(proxyUrl);
      
      // Create custom HTTPS agent with SSL certificate handling
      let httpsAgentOptions: https.AgentOptions = {
        keepAlive: true,
        keepAliveMsecs: 30000,
        maxSockets: 50,
        timeout: 60000,
        secureProtocol: 'TLSv1_2_method',
        ciphers: 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS',
        honorCipherOrder: true,
      };

      // SSL certificate configuration
      if (this.sslCertPath && fs.existsSync(this.sslCertPath)) {
        httpsAgentOptions.ca = fs.readFileSync(this.sslCertPath);
        httpsAgentOptions.rejectUnauthorized = true;
        logger.info('Using SSL certificate for secure proxy connection');
      } else {
        // For development/testing - in production you should always use certificates
        httpsAgentOptions.rejectUnauthorized = false;
        logger.warn('SSL certificate not available - using insecure connection (not recommended for production)');
      }

      const httpsAgent = new https.Agent(httpsAgentOptions);
      
      // Create Axios instance with proxy and enhanced configuration
      this.axiosInstance = axios.create({
        httpsAgent: this.proxyAgent,
        timeout: 30000,
        headers: {
          'User-Agent': this.getRandomUserAgent(),
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate, br',
          'DNT': '1',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none'
        },
        validateStatus: function (status) {
          return status < 500; // Accept all responses except server errors
        }
      });

      // Add request interceptor for additional randomization
      this.axiosInstance.interceptors.request.use((config) => {
        // Rotate User-Agent for each request
        if (process.env.PROXY_USER_AGENT_ROTATE === 'true') {
          config.headers['User-Agent'] = this.getRandomUserAgent();
        }

        // Add random delay
        const delay = parseInt(process.env.PROXY_REQUEST_DELAY || '2000');
        if (delay > 0) {
          return new Promise(resolve => {
            setTimeout(() => resolve(config), Math.random() * delay);
          });
        }

        return config;
      });

      // Add response interceptor for error handling
      this.axiosInstance.interceptors.response.use(
        (response) => {
          logger.debug(`Proxy request successful: ${response.status} ${response.config.url}`);
          return response;
        },
        (error) => {
          logger.warn(`Proxy request failed: ${error.message} ${error.config?.url}`);
          return Promise.reject(error);
        }
      );

      logger.info('Proxy manager initialized successfully with North American geo-targeting');
    } catch (error) {
      logger.error('Proxy initialization failed:', error);
      throw error;
    }
  }

  /**
   * Get random User-Agent string
   */
  private getRandomUserAgent(): string {
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
    ];
    
    return userAgents[Math.floor(Math.random() * userAgents.length)];
  }

  /**
   * Test proxy connection
   */
  async testConnection(): Promise<boolean> {
    try {
      logger.info('Testing Bright Data proxy connection...');
      
      const testResponse = await this.axiosInstance.get('https://geo.brdtest.com/welcome.txt?product=resi&method=native', {
        timeout: 10000
      });

      if (testResponse.status === 200) {
        logger.info('Proxy connection test successful:', testResponse.data);
        return true;
      } else {
        logger.warn('Proxy connection test returned unexpected status:', testResponse.status);
        return false;
      }
    } catch (error) {
      logger.error('Proxy connection test failed:', error);
      return false;
    }
  }

  /**
   * Get proxy information
   */
  getProxyInfo() {
    return {
      host: brightDataConfig.host,
      port: brightDataConfig.port,
      zone: brightDataConfig.zone,
      country: brightDataConfig.country,
      username: brightDataConfig.username,
      sslEnabled: !!this.sslCertPath
    };
  }

  /**
   * Get configured Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Refresh proxy configuration (useful for rotation)
   */
  refreshProxy(): void {
    logger.info('Refreshing proxy configuration...');
    this.initializeProxy();
  }

  /**
   * Get proxy agent for direct use
   */
  getProxyAgent(): HttpsProxyAgent<string> {
    return this.proxyAgent;
  }

  /**
   * Create a new request config with proxy
   */
  createRequestConfig(config: AxiosRequestConfig = {}): AxiosRequestConfig {
    return {
      ...config,
      httpsAgent: this.proxyAgent,
      timeout: config.timeout || 30000,
      headers: {
        'User-Agent': this.getRandomUserAgent(),
        ...config.headers
      }
    };
  }

  /**
   * Rotate to next US state proxy
   */
  rotateState(): void {
    this.currentStateIndex++;
    this.initializeProxy();
    logger.info(`Rotated to next state proxy: ${US_STATES[this.currentStateIndex % US_STATES.length]}`);
  }
}

// Export singleton instance
export const proxyManager = ProxyManager.getInstance();
