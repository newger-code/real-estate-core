"""
Bright Data Proxy Configuration
Enhanced proxy management with rotation and testing capabilities
"""

import requests
import random
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from utils.common import setup_logger

@dataclass
class ProxyConfig:
    """Proxy configuration data class"""
    username: str
    password: str
    host: str
    port: int
    protocol: str = "http"
    
    @property
    def proxy_url(self) -> str:
        """Get formatted proxy URL"""
        return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
    
    @property
    def proxy_dict(self) -> Dict[str, str]:
        """Get proxy dictionary for requests/playwright"""
        proxy_url = self.proxy_url
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    @property
    def playwright_proxy(self) -> Dict[str, str]:
        """Get proxy config for Playwright"""
        return {
            "server": f"{self.protocol}://{self.host}:{self.port}",
            "username": self.username,
            "password": self.password
        }

class BrightDataProxyManager:
    """
    Bright Data proxy manager with rotation and health checking
    """
    
    def __init__(self):
        self.logger = setup_logger("proxy_manager")
        
        # Primary Bright Data proxy configuration
        self.primary_proxy = ProxyConfig(
            username="brd-customer-hl_dd2a0351-zone-residential_proxy_us1",
            password="nu5r3s60i5cd",
            host="brd.superproxy.io",
            port=33335
        )
        
        # Additional proxy endpoints for rotation (if available)
        self.proxy_pool = [self.primary_proxy]
        
        # Health check settings
        self.test_url = "http://httpbin.org/ip"
        self.timeout = 10
        
    def get_primary_proxy(self) -> ProxyConfig:
        """Get primary proxy configuration"""
        return self.primary_proxy
    
    def get_random_proxy(self) -> ProxyConfig:
        """Get random proxy from pool"""
        return random.choice(self.proxy_pool)
    
    async def test_proxy_connectivity(self, proxy: ProxyConfig = None) -> Tuple[bool, str, Optional[str]]:
        """
        Test proxy connectivity and return (success, message, ip_address)
        """
        if proxy is None:
            proxy = self.primary_proxy
            
        try:
            self.logger.info(f"Testing proxy connectivity: {proxy.host}:{proxy.port}")
            
            # Test with requests (disable SSL verification for proxy testing)
            response = requests.get(
                self.test_url,
                proxies=proxy.proxy_dict,
                timeout=self.timeout,
                verify=False
            )
            
            if response.status_code == 200:
                # Parse JSON response from httpbin
                try:
                    import json
                    data = json.loads(response.text)
                    ip_address = data.get('origin', 'unknown')
                except:
                    ip_address = response.text.strip()
                self.logger.info(f"✅ Proxy test successful - IP: {ip_address}")
                return True, f"Proxy working - IP: {ip_address}", ip_address
            else:
                error_msg = f"HTTP {response.status_code}"
                self.logger.error(f"❌ Proxy test failed: {error_msg}")
                return False, error_msg, None
                
        except requests.exceptions.ProxyError as e:
            error_msg = f"Proxy connection error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg, None
        except requests.exceptions.Timeout:
            error_msg = "Proxy connection timeout"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg, None
    
    async def test_all_proxies(self) -> Dict[str, Tuple[bool, str, Optional[str]]]:
        """Test all proxies in pool"""
        results = {}
        
        for i, proxy in enumerate(self.proxy_pool):
            proxy_name = f"proxy_{i+1}_{proxy.host}:{proxy.port}"
            results[proxy_name] = await self.test_proxy_connectivity(proxy)
            
        return results
    
    def get_working_proxy(self) -> Optional[ProxyConfig]:
        """Get first working proxy (synchronous version for quick access)"""
        try:
            # Quick test of primary proxy
            response = requests.get(
                self.test_url,
                proxies=self.primary_proxy.proxy_dict,
                timeout=5,
                verify=False
            )
            if response.status_code == 200:
                return self.primary_proxy
        except:
            pass
            
        return None
    
    def add_proxy(self, username: str, password: str, host: str, port: int):
        """Add additional proxy to pool"""
        proxy = ProxyConfig(username, password, host, port)
        self.proxy_pool.append(proxy)
        self.logger.info(f"Added proxy to pool: {host}:{port}")
    
    def get_proxy_stats(self) -> Dict[str, any]:
        """Get proxy pool statistics"""
        return {
            "total_proxies": len(self.proxy_pool),
            "primary_proxy": f"{self.primary_proxy.host}:{self.primary_proxy.port}",
            "proxy_pool": [f"{p.host}:{p.port}" for p in self.proxy_pool]
        }

# Global proxy manager instance
proxy_manager = BrightDataProxyManager()

# Convenience functions for easy access
def get_proxy_config() -> ProxyConfig:
    """Get primary proxy configuration"""
    return proxy_manager.get_primary_proxy()

def get_proxy_dict() -> Dict[str, str]:
    """Get proxy dictionary for requests"""
    return proxy_manager.get_primary_proxy().proxy_dict

def get_playwright_proxy() -> Dict[str, str]:
    """Get proxy config for Playwright"""
    return proxy_manager.get_primary_proxy().playwright_proxy

async def test_proxy() -> Tuple[bool, str, Optional[str]]:
    """Quick proxy test"""
    return await proxy_manager.test_proxy_connectivity()

if __name__ == "__main__":
    # Test script
    import asyncio
    
    async def main():
        print("Testing Bright Data Proxy Configuration")
        print("=" * 50)
        
        # Test primary proxy
        success, message, ip = await proxy_manager.test_proxy_connectivity()
        print(f"Primary Proxy Test: {message}")
        
        # Show proxy stats
        stats = proxy_manager.get_proxy_stats()
        print(f"\nProxy Stats: {stats}")
        
        if success:
            print(f"\n✅ Proxy is working! External IP: {ip}")
        else:
            print(f"\n❌ Proxy test failed: {message}")
    
    asyncio.run(main())
