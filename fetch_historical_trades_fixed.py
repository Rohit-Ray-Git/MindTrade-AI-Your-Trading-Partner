#!/usr/bin/env python3
"""
Fixed Delta Exchange Historical Trades Fetcher
Based on web search findings and API documentation issues
"""

import os
import asyncio
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

class DeltaHistoricalTradesFetcherFixed:
    """Fixed version of Delta Exchange trades fetcher"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        self.public_url = "https://publicapi.deltaexchange.io"
        
        print("📊 Delta Exchange Historical Trades Fetcher (Fixed)")
        print("=" * 60)
        
        if not self.api_key or not self.api_secret or self.api_key.startswith("your-"):
            print("⚠️ Private API credentials not configured - will use public endpoints")
            self.private_enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.private_enabled = True
    
    async def fetch_public_trades(self, symbol: str = "BTCUSDT", limit: int = 100):
        """Fetch public trade history (no authentication required)"""
        print(f"\n🌐 Fetching Public Trades for {symbol}...")
        print("-" * 50)
        
        try:
            # Use public API endpoint
            url = f"{self.public_url}/v1/trades"
            params = {
                "market": symbol,
                "limit": limit
            }
            
            headers = {
                "User-Agent": "MindTrade-AI/1.0",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                
                print(f"📊 Status Code: {response.status_code}")
                print(f"🔗 URL: {response.url}")
                
                if response.status_code == 200:
                    trades = response.json()
                    
                    print(f"✅ Successfully fetched {len(trades)} public trades")
                    
                    if trades:
                        print("\n📋 Sample Public Trades:")
                        for i, trade in enumerate(trades[:5], 1):
                            price = trade.get("price", "N/A")
                            volume = trade.get("volume", "N/A")
                            created_at = trade.get("created_at", "N/A")
                            print(f"   {i}. Price: {price}, Volume: {volume}, Time: {created_at}")
                        
                        return trades
                    else:
                        print("ℹ️ No public trades found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch public trades: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching public trades: {str(e)}")
            return None
    
    async def fetch_public_candles(self, symbol: str = "BTCUSD", resolution: str = "1h"):
        """Fetch historical candlestick data (public)"""
        print(f"\n📈 Fetching Public Candles for {symbol} ({resolution})...")
        print("-" * 50)
        
        try:
            # Calculate time range (last 7 days)
            end_time = int(time.time())
            start_time = end_time - (7 * 24 * 60 * 60)  # 7 days ago
            
            url = f"{self.base_url}/v2/history/candles"
            params = {
                "resolution": resolution,
                "symbol": symbol,
                "start": start_time,
                "end": end_time
            }
            
            headers = {
                "User-Agent": "MindTrade-AI/1.0",
                "Accept": "application/json"
            }
            
            print(f"📅 Time Range: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    candles = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(candles)} candles")
                    
                    if candles:
                        print("\n📋 Sample Candles (OHLCV):")
                        for i, candle in enumerate(candles[:5], 1):
                            timestamp = candle.get("time", 0)
                            candle_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
                            open_price = candle.get("open", "N/A")
                            high_price = candle.get("high", "N/A")
                            low_price = candle.get("low", "N/A")
                            close_price = candle.get("close", "N/A")
                            volume = candle.get("volume", "N/A")
                            
                            print(f"   {i}. {candle_time} - O:{open_price} H:{high_price} L:{low_price} C:{close_price} V:{volume}")
                        
                        return candles
                    else:
                        print("ℹ️ No candles found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch candles: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching candles: {str(e)}")
            return None
    
    async def fetch_products(self):
        """Fetch available trading products"""
        print(f"\n🛍️ Fetching Available Products...")
        print("-" * 50)
        
        try:
            url = f"{self.base_url}/v2/products"
            
            headers = {
                "User-Agent": "MindTrade-AI/1.0",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("result", [])
                    
                    print(f"✅ Found {len(products)} available products")
                    
                    # Show popular trading pairs
                    popular_symbols = ["BTCUSDT", "ETHUSDT", "BTCUSD", "ETHUSD"]
                    print("\n📋 Popular Trading Pairs:")
                    
                    found_products = []
                    for product in products:
                        symbol = product.get("symbol", "")
                        if symbol in popular_symbols:
                            found_products.append(product)
                            description = product.get("description", "No description")
                            print(f"   ✅ {symbol} - {description}")
                    
                    if not found_products:
                        print("   📋 First 10 available products:")
                        for i, product in enumerate(products[:10], 1):
                            symbol = product.get("symbol", "Unknown")
                            description = product.get("description", "No description")
                            print(f"   {i}. {symbol} - {description}")
                    
                    return products
                
                else:
                    print(f"❌ Failed to fetch products: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching products: {str(e)}")
            return None
    
    def _fixed_signature_generation(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Fixed signature generation based on research findings"""
        # Based on web search findings, ensure proper formatting
        message = f"{method}{timestamp}{request_path}{body}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_fixed_headers(self, method: str, request_path: str, body: str = "") -> dict:
        """Fixed headers based on research findings"""
        # Ensure timestamp is current and properly formatted
        timestamp = str(int(time.time()))
        signature = self._fixed_signature_generation(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "MindTrade-AI/1.0",  # Required based on research
            "Accept": "application/json"
        }
    
    async def test_private_authentication_fixed(self):
        """Test private API with fixed authentication"""
        print(f"\n🔐 Testing Private API (Fixed Method)...")
        print("-" * 50)
        
        if not self.private_enabled:
            print("❌ Private API credentials not configured")
            return False
        
        try:
            endpoint = "/v2/profile"
            headers = self._get_fixed_headers("GET", endpoint)
            
            print(f"🔧 Headers being sent:")
            print(f"   api-key: {headers['api-key'][:8]}...")
            print(f"   timestamp: {headers['timestamp']}")
            print(f"   signature: {headers['signature'][:16]}...")
            print(f"   User-Agent: {headers['User-Agent']}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Private API authentication successful!")
                    print(f"Account ID: {data.get('id', 'N/A')}")
                    print(f"Email: {data.get('email', 'N/A')}")
                    return True
                    
                elif response.status_code == 401:
                    print("❌ Authentication still failing with fixed method")
                    print(f"Response: {response.text}")
                    
                    # Additional debugging
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    
                    print(f"\n🔍 Debugging Information:")
                    print(f"   Error Code: {error_code}")
                    print(f"   Current Time: {int(time.time())}")
                    print(f"   Request Path: {endpoint}")
                    
                    if error_code == "invalid_api_key":
                        print("\n💡 Possible Solutions:")
                        print("   1. Verify API key is copied correctly (no extra spaces)")
                        print("   2. Check if API key is active on Delta Exchange")
                        print("   3. Ensure API key has proper permissions")
                        print("   4. Try generating new API keys")
                    
                    return False
                    
                else:
                    print(f"❌ Unexpected status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def comprehensive_fetch(self):
        """Comprehensive fetch using both public and private endpoints"""
        print("\n🚀 Starting Comprehensive Data Fetch (Fixed Version)")
        print("=" * 60)
        
        results = {}
        
        # 1. Test public endpoints first (always work)
        print("\n" + "="*30 + " PUBLIC DATA " + "="*30)
        
        # Fetch products
        products = await self.fetch_products()
        if products:
            results['products'] = products[:10]  # Save first 10 for reference
        
        # Fetch public trades
        public_trades = await self.fetch_public_trades("BTCUSDT", 50)
        if public_trades:
            results['public_trades'] = public_trades
        
        # Fetch candles
        candles = await self.fetch_public_candles("BTCUSD", "1h")
        if candles:
            results['candles'] = candles
        
        # 2. Test private endpoints if credentials available
        if self.private_enabled:
            print("\n" + "="*30 + " PRIVATE DATA " + "="*30)
            
            auth_success = await self.test_private_authentication_fixed()
            if auth_success:
                print("🎉 Private API working - could fetch personal trade history")
                # Would add private trade fetching here if auth works
            else:
                print("⚠️ Private API not working - using public data only")
        
        # 3. Summary
        print(f"\n📊 FETCH SUMMARY")
        print("=" * 60)
        
        total_records = 0
        for key, data in results.items():
            count = len(data) if data else 0
            total_records += count
            print(f"✅ {key}: {count} records")
        
        if total_records > 0:
            print(f"\n🎉 Successfully fetched {total_records} total records!")
            
            # Save to file
            output_file = f"delta_data_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Data saved to: {output_file}")
            
            # Provide usage recommendations
            print(f"\n💡 Data Usage Recommendations:")
            if 'public_trades' in results:
                print("   📊 Use public trades for market analysis")
            if 'candles' in results:
                print("   📈 Use candle data for price charts and technical analysis")
            if 'products' in results:
                print("   🛍️ Use products list to find available trading pairs")
            
        else:
            print("⚠️ No data fetched - check network connection")
        
        return results

async def main():
    """Main function"""
    fetcher = DeltaHistoricalTradesFetcherFixed()
    
    try:
        await fetcher.comprehensive_fetch()
    except KeyboardInterrupt:
        print("\n⚠️ Fetch interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Fixed Delta Exchange Data Fetch")
    asyncio.run(main())
