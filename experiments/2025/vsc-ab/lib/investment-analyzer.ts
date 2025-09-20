
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

export interface PropertyInvestmentData {
  purchasePrice: number;
  downPaymentPercent: number;
  interestRate: number;
  loanTermYears: number;
  monthlyRent: number;
  propertyTaxes: number;
  insurance: number;
  maintenancePercent: number;
  vacancyPercent: number;
  managementPercent: number;
  closingCostsPercent: number;
  rehab: number;
  appreciationRate: number;
  rentGrowthRate: number;
}

export interface InvestmentAnalysisResult {
  // Basic Metrics
  monthlyMortgage: number;
  monthlyTotalExpenses: number;
  monthlyCashFlow: number;
  annualCashFlow: number;
  
  // Investment Returns
  capRate: number;
  cashOnCashReturn: number;
  totalReturn: number;
  
  // Advanced Metrics
  grossRentMultiplier: number;
  debtServiceCoverageRatio: number;
  returnOnInvestment: number;
  
  // Projections (10 years)
  projections: {
    year: number;
    propertyValue: number;
    monthlyRent: number;
    equity: number;
    cumulativeCashFlow: number;
    totalReturn: number;
  }[];
  
  // Risk Assessment
  riskScore: number;
  riskFactors: string[];
  
  // Investment Score
  investmentScore: number;
  recommendation: 'Strong Buy' | 'Buy' | 'Hold' | 'Avoid';
}

export class InvestmentAnalyzer {
  
  /**
   * Perform comprehensive investment analysis
   */
  static analyzeInvestment(data: PropertyInvestmentData): InvestmentAnalysisResult {
    try {
      logger.info('Starting investment analysis...');
      
      // Basic calculations
      const downPayment = data.purchasePrice * (data.downPaymentPercent / 100);
      const loanAmount = data.purchasePrice - downPayment;
      const closingCosts = data.purchasePrice * (data.closingCostsPercent / 100);
      const totalInitialInvestment = downPayment + closingCosts + data.rehab;
      
      // Monthly mortgage payment
      const monthlyRate = data.interestRate / 100 / 12;
      const numPayments = data.loanTermYears * 12;
      const monthlyMortgage = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                             (Math.pow(1 + monthlyRate, numPayments) - 1);
      
      // Monthly expenses
      const monthlyPropertyTax = data.propertyTaxes / 12;
      const monthlyInsurance = data.insurance / 12;
      const monthlyMaintenance = data.monthlyRent * (data.maintenancePercent / 100);
      const monthlyManagement = data.monthlyRent * (data.managementPercent / 100);
      const monthlyTotalExpenses = monthlyMortgage + monthlyPropertyTax + monthlyInsurance + 
                                  monthlyMaintenance + monthlyManagement;
      
      // Cash flow calculations
      const effectiveMonthlyRent = data.monthlyRent * (1 - data.vacancyPercent / 100);
      const monthlyCashFlow = effectiveMonthlyRent - monthlyTotalExpenses;
      const annualCashFlow = monthlyCashFlow * 12;
      
      // Investment metrics
      const netOperatingIncome = (effectiveMonthlyRent * 12) - 
                                (data.propertyTaxes + data.insurance + (monthlyMaintenance * 12) + (monthlyManagement * 12));
      const capRate = (netOperatingIncome / data.purchasePrice) * 100;
      const cashOnCashReturn = (annualCashFlow / totalInitialInvestment) * 100;
      
      // Advanced metrics
      const grossRentMultiplier = data.purchasePrice / (data.monthlyRent * 12);
      const debtServiceCoverageRatio = netOperatingIncome / (monthlyMortgage * 12);
      const totalReturn = this.calculateTotalReturn(data, totalInitialInvestment);
      const returnOnInvestment = ((annualCashFlow + (data.purchasePrice * data.appreciationRate / 100)) / 
                                 totalInitialInvestment) * 100;
      
      // 10-year projections
      const projections = this.calculateProjections(data, totalInitialInvestment);
      
      // Risk assessment
      const riskAssessment = this.assessRisk(data, {
        capRate,
        cashOnCashReturn,
        debtServiceCoverageRatio,
        monthlyCashFlow
      });
      
      // Investment scoring
      const investmentScore = this.calculateInvestmentScore({
        capRate,
        cashOnCashReturn,
        monthlyCashFlow,
        debtServiceCoverageRatio,
        riskScore: riskAssessment.riskScore
      });
      
      const recommendation = this.getRecommendation(investmentScore);
      
      const result: InvestmentAnalysisResult = {
        monthlyMortgage,
        monthlyTotalExpenses,
        monthlyCashFlow,
        annualCashFlow,
        capRate,
        cashOnCashReturn,
        totalReturn,
        grossRentMultiplier,
        debtServiceCoverageRatio,
        returnOnInvestment,
        projections,
        riskScore: riskAssessment.riskScore,
        riskFactors: riskAssessment.riskFactors,
        investmentScore,
        recommendation
      };
      
      logger.info(`Investment analysis completed. Score: ${investmentScore}, Recommendation: ${recommendation}`);
      return result;
      
    } catch (error) {
      logger.error('Investment analysis failed:', error);
      throw new Error('Failed to perform investment analysis');
    }
  }
  
  /**
   * Calculate total return including appreciation and cash flow
   */
  private static calculateTotalReturn(data: PropertyInvestmentData, initialInvestment: number): number {
    const annualAppreciation = data.purchasePrice * (data.appreciationRate / 100);
    const annualCashFlow = data.monthlyRent * 12 * (1 - data.vacancyPercent / 100) - 
                          (data.propertyTaxes + data.insurance + 
                           data.monthlyRent * 12 * (data.maintenancePercent + data.managementPercent) / 100);
    
    return ((annualAppreciation + annualCashFlow) / initialInvestment) * 100;
  }
  
  /**
   * Calculate 10-year projections
   */
  private static calculateProjections(data: PropertyInvestmentData, initialInvestment: number) {
    const projections = [];
    let currentPropertyValue = data.purchasePrice;
    let currentRent = data.monthlyRent;
    let remainingLoanBalance = data.purchasePrice - (data.purchasePrice * data.downPaymentPercent / 100);
    let cumulativeCashFlow = 0;
    
    const monthlyMortgage = this.calculateMonthlyMortgage(data);
    
    for (let year = 1; year <= 10; year++) {
      // Property appreciation
      currentPropertyValue *= (1 + data.appreciationRate / 100);
      
      // Rent growth
      currentRent *= (1 + data.rentGrowthRate / 100);
      
      // Loan balance reduction (simplified)
      const annualPrincipalPayment = monthlyMortgage * 12 * 0.3; // Rough estimate
      remainingLoanBalance = Math.max(0, remainingLoanBalance - annualPrincipalPayment);
      
      // Annual cash flow
      const effectiveRent = currentRent * 12 * (1 - data.vacancyPercent / 100);
      const expenses = data.propertyTaxes + data.insurance + 
                      effectiveRent * (data.maintenancePercent + data.managementPercent) / 100 +
                      monthlyMortgage * 12;
      const yearCashFlow = effectiveRent - expenses;
      cumulativeCashFlow += yearCashFlow;
      
      // Equity
      const equity = currentPropertyValue - remainingLoanBalance;
      
      // Total return
      const totalReturn = ((cumulativeCashFlow + equity - initialInvestment) / initialInvestment) * 100;
      
      projections.push({
        year,
        propertyValue: Math.round(currentPropertyValue),
        monthlyRent: Math.round(currentRent),
        equity: Math.round(equity),
        cumulativeCashFlow: Math.round(cumulativeCashFlow),
        totalReturn: Math.round(totalReturn * 100) / 100
      });
    }
    
    return projections;
  }
  
  /**
   * Calculate monthly mortgage payment
   */
  private static calculateMonthlyMortgage(data: PropertyInvestmentData): number {
    const loanAmount = data.purchasePrice * (1 - data.downPaymentPercent / 100);
    const monthlyRate = data.interestRate / 100 / 12;
    const numPayments = data.loanTermYears * 12;
    
    return loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
           (Math.pow(1 + monthlyRate, numPayments) - 1);
  }
  
  /**
   * Assess investment risks
   */
  private static assessRisk(data: PropertyInvestmentData, metrics: any): { riskScore: number; riskFactors: string[] } {
    let riskScore = 0;
    const riskFactors: string[] = [];
    
    // Cap rate risk
    if (metrics.capRate < 4) {
      riskScore += 20;
      riskFactors.push('Low cap rate indicates higher risk or overpriced property');
    } else if (metrics.capRate > 12) {
      riskScore += 15;
      riskFactors.push('Very high cap rate may indicate problematic area or property issues');
    }
    
    // Cash flow risk
    if (metrics.monthlyCashFlow < 0) {
      riskScore += 30;
      riskFactors.push('Negative cash flow requires ongoing capital injection');
    } else if (metrics.monthlyCashFlow < 100) {
      riskScore += 15;
      riskFactors.push('Low cash flow provides little buffer for expenses');
    }
    
    // Debt service coverage
    if (metrics.debtServiceCoverageRatio < 1.2) {
      riskScore += 25;
      riskFactors.push('Low debt service coverage ratio increases default risk');
    }
    
    // Market risks
    if (data.appreciationRate > 8) {
      riskScore += 10;
      riskFactors.push('High appreciation assumptions may be unrealistic');
    }
    
    // Vacancy risk
    if (data.vacancyPercent > 15) {
      riskScore += 15;
      riskFactors.push('High vacancy rate indicates market or property issues');
    }
    
    // Leverage risk
    if (data.downPaymentPercent < 20) {
      riskScore += 10;
      riskFactors.push('High leverage increases financial risk');
    }
    
    return { riskScore: Math.min(riskScore, 100), riskFactors };
  }
  
  /**
   * Calculate overall investment score
   */
  private static calculateInvestmentScore(metrics: any): number {
    let score = 100;
    
    // Cap rate scoring
    if (metrics.capRate >= 8) score += 20;
    else if (metrics.capRate >= 6) score += 10;
    else if (metrics.capRate < 4) score -= 20;
    
    // Cash on cash return scoring
    if (metrics.cashOnCashReturn >= 12) score += 15;
    else if (metrics.cashOnCashReturn >= 8) score += 10;
    else if (metrics.cashOnCashReturn < 0) score -= 30;
    
    // Cash flow scoring
    if (metrics.monthlyCashFlow >= 500) score += 15;
    else if (metrics.monthlyCashFlow >= 200) score += 10;
    else if (metrics.monthlyCashFlow < 0) score -= 25;
    
    // DSCR scoring
    if (metrics.debtServiceCoverageRatio >= 1.5) score += 10;
    else if (metrics.debtServiceCoverageRatio < 1.2) score -= 20;
    
    // Risk adjustment
    score -= (metrics.riskScore * 0.5);
    
    return Math.max(0, Math.min(100, Math.round(score)));
  }
  
  /**
   * Get investment recommendation based on score
   */
  private static getRecommendation(score: number): 'Strong Buy' | 'Buy' | 'Hold' | 'Avoid' {
    if (score >= 80) return 'Strong Buy';
    if (score >= 65) return 'Buy';
    if (score >= 45) return 'Hold';
    return 'Avoid';
  }
}
