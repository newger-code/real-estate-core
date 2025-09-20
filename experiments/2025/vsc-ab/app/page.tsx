
'use client'

import { useState, useEffect } from 'react'
import { Search, BarChart3, Home, TrendingUp, Database, Zap, Shield, Award, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import AddressSearchInput from '@/components/address-search-input'
import PropertyAnalysisResults from '@/components/property-analysis-results'
import DashboardStats from '@/components/dashboard-stats'
import { NormalizedAddress } from '@/lib/address-normalizer'

interface PropertySearchResult {
  success: boolean;
  cached: boolean;
  property: any;
  message: string;
  error?: string;
}

interface ProxyStatus {
  status: 'unknown' | 'connected' | 'disconnected' | 'error';
  info?: any;
}

export default function HomePage() {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<PropertySearchResult | null>(null);
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>({ status: 'unknown' });
  const [selectedAddress, setSelectedAddress] = useState<NormalizedAddress | null>(null);

  // Test proxy connection on component mount
  useEffect(() => {
    const testProxy = async () => {
      try {
        const response = await fetch('/api/proxy/test');
        const data = await response.json();
        
        if (data.success) {
          setProxyStatus({ 
            status: 'connected', 
            info: data.proxy 
          });
          toast.success('Proxy connection established', {
            description: `Connected via ${data.proxy?.zone} with North American geo-targeting`
          });
        } else {
          setProxyStatus({ status: 'disconnected' });
          toast.warning('Proxy connection failed', {
            description: 'Some features may be limited without proxy access'
          });
        }
      } catch (error) {
        setProxyStatus({ status: 'error' });
        console.warn('Proxy test failed:', error);
      }
    };

    testProxy();
  }, []);

  const handleAddressSelected = async (normalizedAddress: NormalizedAddress) => {
    setSelectedAddress(normalizedAddress);
    setIsSearching(true);
    setSearchResult(null);

    try {
      const searchPayload = {
        address: normalizedAddress.components.streetName ? 
          `${normalizedAddress.components.houseNumber} ${normalizedAddress.components.streetName}` : 
          normalizedAddress.original,
        city: normalizedAddress.components.city || '',
        state: normalizedAddress.components.state || '',
        zipCode: normalizedAddress.components.zipCode || ''
      };

      const response = await fetch('/api/property/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(searchPayload)
      });

      const data = await response.json();

      if (data.success) {
        setSearchResult(data);
        toast.success('Property analysis completed!', {
          description: `Found comprehensive data for ${normalizedAddress.normalized}`
        });
      } else {
        setSearchResult(data);
        toast.error('Property search failed', {
          description: data.error || 'Unable to analyze this property'
        });
      }
    } catch (error) {
      console.error('Property search error:', error);
      toast.error('Search failed', {
        description: 'Please try again or contact support if the issue persists'
      });
      setSearchResult({
        success: false,
        cached: false,
        property: null,
        message: 'Search request failed',
        error: String(error)
      });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Section with Enhanced Search */}
      <section className="relative bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-indigo-600/10 to-blue-800/20" />
        
        <div className="relative z-10 container mx-auto px-4 py-16 lg:py-24">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-4xl mx-auto text-center mb-12"
          >
            {/* Status Indicator */}
            <div className="flex items-center justify-center gap-2 mb-6">
              <div className={`w-2 h-2 rounded-full ${
                proxyStatus.status === 'connected' ? 'bg-green-400' :
                proxyStatus.status === 'disconnected' ? 'bg-yellow-400' :
                proxyStatus.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
              }`} />
              <span className="text-sm opacity-75">
                {proxyStatus.status === 'connected' ? 'System Online - North American Geo-Targeting Active' :
                 proxyStatus.status === 'disconnected' ? 'Limited Mode - Some features may be unavailable' :
                 proxyStatus.status === 'error' ? 'System Issues - Contact support if problems persist' :
                 'Initializing system...'}
              </span>
            </div>

            <div className="flex items-center justify-center gap-2 mb-4">
              <Home className="h-10 w-10" />
              <span className="text-2xl font-bold">PropertyScope Analytics</span>
            </div>
            
            <h1 className="text-4xl lg:text-6xl font-bold mb-6 leading-tight">
              Comprehensive Property Intelligence
            </h1>
            
            <p className="text-xl lg:text-2xl opacity-90 mb-8">
              Get instant access to <span className="font-semibold text-yellow-300">9+ AVM estimates</span>, 
              professional investment analysis, and market insights for any US property
            </p>
          </motion.div>

          {/* Enhanced Search Input */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="max-w-3xl mx-auto mb-12"
          >
            <AddressSearchInput
              onAddressSelected={handleAddressSelected}
              className="shadow-2xl"
              placeholder="Enter any US property address (e.g., 1240 Pondview Ave, Akron, OH 44305)"
              disabled={isSearching}
            />
          </motion.div>

          {/* Feature Highlights */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="flex flex-wrap items-center justify-center gap-6 text-sm opacity-90"
          >
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="font-medium">9+ Professional AVM Estimates</span>
            </div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-300" />
              <span className="font-medium">Investment ROI Analysis</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-300" />
              <span className="font-medium">Market Intelligence</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-orange-300" />
              <span className="font-medium">Risk Assessment</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        {/* Search Results */}
        {(isSearching || searchResult) && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-12"
          >
            <div className="max-w-7xl mx-auto">
              {isSearching ? (
                <Card className="border-2 border-blue-200 bg-blue-50/50">
                  <CardContent className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-blue-900 mb-2">
                        Analyzing Property...
                      </h3>
                      <p className="text-blue-700">
                        {selectedAddress ? 
                          `Gathering comprehensive data for ${selectedAddress.normalized}` :
                          'Processing your request...'
                        }
                      </p>
                      <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm text-blue-600">
                        <span className="bg-white/50 px-2 py-1 rounded">Fetching AVM estimates...</span>
                        <span className="bg-white/50 px-2 py-1 rounded">Analyzing market data...</span>
                        <span className="bg-white/50 px-2 py-1 rounded">Calculating investment metrics...</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                searchResult && (
                  <PropertyAnalysisResults 
                    result={searchResult} 
                  />
                )
              )}
            </div>
          </motion.section>
        )}

        {/* Dashboard Stats */}
        {!isSearching && !searchResult && (
          <motion.section 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-12"
          >
            <DashboardStats />
          </motion.section>
        )}

        {/* Platform Features */}
        {!searchResult && (
          <motion.section 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mb-16"
          >
            <div className="text-center mb-12">
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
                Professional Real Estate Analytics
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Access institutional-grade property analysis tools designed for investors, agents, and property enthusiasts
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-blue-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-blue-200 transition-colors">
                    <Database className="h-8 w-8 text-blue-600" />
                  </div>
                  <CardTitle className="text-xl">9+ AVM Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Get comprehensive property valuations from Homes.com (5 providers), Zillow, Movoto, Redfin, and Realtor.com for the most accurate market value assessment.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Homes.com</Badge>
                    <Badge variant="secondary" className="text-xs">Zillow</Badge>
                    <Badge variant="secondary" className="text-xs">Redfin</Badge>
                    <Badge variant="secondary" className="text-xs">Movoto</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-green-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-green-200 transition-colors">
                    <BarChart3 className="h-8 w-8 text-green-600" />
                  </div>
                  <CardTitle className="text-xl">Investment Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Professional ROI calculations, cash flow projections, cap rates, and investment scoring to make data-driven property investment decisions.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Cap Rate</Badge>
                    <Badge variant="secondary" className="text-xs">Cash Flow</Badge>
                    <Badge variant="secondary" className="text-xs">ROI</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-purple-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-purple-200 transition-colors">
                    <TrendingUp className="h-8 w-8 text-purple-600" />
                  </div>
                  <CardTitle className="text-xl">Market Intelligence</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Advanced market timing analysis, neighborhood trends, comparable sales, and predictive insights to optimize your buying and selling decisions.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Trends</Badge>
                    <Badge variant="secondary" className="text-xs">Comps</Badge>
                    <Badge variant="secondary" className="text-xs">Timing</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-orange-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-orange-200 transition-colors">
                    <Shield className="h-8 w-8 text-orange-600" />
                  </div>
                  <CardTitle className="text-xl">Risk Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Comprehensive risk analysis including neighborhood safety, environmental hazards, market volatility, and investment risk scoring.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Safety</Badge>
                    <Badge variant="secondary" className="text-xs">Environment</Badge>
                    <Badge variant="secondary" className="text-xs">Market Risk</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-blue-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-blue-200 transition-colors">
                    <Zap className="h-8 w-8 text-blue-600" />
                  </div>
                  <CardTitle className="text-xl">Smart Automation</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Intelligent address normalization, automated data aggregation, and smart caching for lightning-fast property analysis and accurate results.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Auto-complete</Badge>
                    <Badge variant="secondary" className="text-xs">Data Quality</Badge>
                    <Badge variant="secondary" className="text-xs">Speed</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-green-200">
                <CardHeader className="text-center pb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-green-200 transition-colors">
                    <Award className="h-8 w-8 text-green-600" />
                  </div>
                  <CardTitle className="text-xl">Professional Grade</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-base leading-relaxed">
                    Enterprise-level infrastructure with North American geo-targeting, SSL security, and institutional-quality data sources for reliable results.
                  </CardDescription>
                  <div className="mt-4 flex flex-wrap gap-1 justify-center">
                    <Badge variant="secondary" className="text-xs">Enterprise</Badge>
                    <Badge variant="secondary" className="text-xs">Secure</Badge>
                    <Badge variant="secondary" className="text-xs">Reliable</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </motion.section>
        )}

        {/* System Status Alert */}
        {proxyStatus.status !== 'connected' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="fixed bottom-4 right-4 z-50 max-w-md"
          >
            <Alert className={`border-2 ${
              proxyStatus.status === 'disconnected' ? 'border-yellow-200 bg-yellow-50' :
              'border-red-200 bg-red-50'
            }`}>
              <div className="flex items-start gap-2">
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                  proxyStatus.status === 'disconnected' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <AlertDescription className="text-sm">
                  {proxyStatus.status === 'disconnected' ? 
                    'System running in limited mode. Some advanced features may be unavailable.' :
                    'System connectivity issues detected. Contact support if problems persist.'
                  }
                </AlertDescription>
              </div>
            </Alert>
          </motion.div>
        )}
      </main>
    </div>
  );
}
