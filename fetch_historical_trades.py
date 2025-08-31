#!/usr/bin/env python3
"""
Fetch Historical Trades from Delta Exchange API
Comprehensive script to fetch and analyze historical trading data
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

class DeltaHistoricalTradesFetcher:
    """Fetches historical trades from Delta Exchange API"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("📊 Delta Exchange Historical Trades Fetcher")
        print("=" * 60)
        
        if not self.api_key or not self.api_secret or self.api_key.startswith("your-"):
            print("❌ API credentials not properly configured")
            self.enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature for Delta Exchange API"""
        message = method + timestamp + request_path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> dict:
        """Get headers with authentication for API requests"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "MindTrade-AI/1.0"
        }
    
    async def test_authentication(self):
        """Test API authentication first"""
        print("\n🔐 Testing Authentication...")
        print("-" * 40)
        
        try:
            endpoint = "/v2/profile"
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Authentication successful!")
                    print(f"Account ID: {data.get('id', 'N/A')}")
                    print(f"Email: {data.get('email', 'N/A')}")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def fetch_fills_history(self, days_back: int = 30):
        """Fetch fills (trade executions) history"""
        print(f"\n📈 Fetching Fills History ({days_back} days)...")
        print("-" * 50)
        
        try:
            # Calculate date range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            endpoint = "/v2/orders/history/fills"
            
            # Build query parameters
            params = {
                "page_size": 100,
                "start_time": int(start_time.timestamp()),
                "end_time": int(end_time.timestamp())
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            print(f"📅 Date Range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
            print(f"🔗 Endpoint: {full_endpoint}")
            
            headers = self._get_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    fills = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(fills)} fills")
                    
                    if fills:
                        print("\n📋 Sample Fills:")
                        for i, fill in enumerate(fills[:5], 1):
                            self._print_fill_details(fill, i)
                        
                        if len(fills) > 5:
                            print(f"... and {len(fills) - 5} more fills")
                        
                        # Analyze the data
                        self._analyze_fills(fills)
                        
                        return fills
                    else:
                        print("ℹ️ No fills found in the specified period")
                        print("This could mean:")
                        print("• No trading activity")
                        print("• Different date range needed")
                        print("• API permissions issue")
                        return []
                
                elif response.status_code == 401:
                    print("❌ Unauthorized - Check API credentials")
                    print("Response:", response.text)
                    return None
                
                elif response.status_code == 404:
                    print("❌ Endpoint not found - API might have changed")
                    print("Response:", response.text)
                    return None
                
                else:
                    print(f"❌ Unexpected status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            print("❌ Request timeout - API might be slow")
            return None
        except Exception as e:
            print(f"❌ Error fetching fills: {str(e)}")
            return None
    
    async def fetch_orders_history(self, days_back: int = 30):
        """Fetch orders history"""
        print(f"\n📋 Fetching Orders History ({days_back} days)...")
        print("-" * 50)
        
        try:
            endpoint = "/v2/orders/history"
            
            # Try different query parameters
            params = {
                "page_size": 50,
                "state": "closed"  # Only closed orders
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            headers = self._get_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(orders)} orders")
                    
                    if orders:
                        print("\n📋 Sample Orders:")
                        for i, order in enumerate(orders[:3], 1):
                            self._print_order_details(order, i)
                        
                        return orders
                    else:
                        print("ℹ️ No orders found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch orders: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching orders: {str(e)}")
            return None
    
    async def fetch_trades_history(self, days_back: int = 30):
        """Try fetching from trades endpoint"""
        print(f"\n💹 Fetching Trades History ({days_back} days)...")
        print("-" * 50)
        
        try:
            endpoint = "/v2/trades"
            
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    trades = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(trades)} trades")
                    
                    if trades:
                        print("\n📋 Sample Trades:")
                        for i, trade in enumerate(trades[:3], 1):
                            print(f"   {i}. {json.dumps(trade, indent=2)}")
                        
                        return trades
                    else:
                        print("ℹ️ No trades found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch trades: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching trades: {str(e)}")
            return None
    
    def _print_fill_details(self, fill: dict, index: int):
        """Print detailed fill information"""
        product = fill.get("product", {})
        symbol = product.get("symbol", "Unknown")
        side = fill.get("side", "Unknown")
        size = fill.get("size", "0")
        price = fill.get("price", "0")
        commission = fill.get("commission", "0")
        timestamp = fill.get("created_at", 0)
        
        if timestamp:
            fill_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            fill_time = "Unknown"
        
        print(f"   {index}. {symbol} - {side.upper()}")
        print(f"      Size: {size}, Price: {price}")
        print(f"      Commission: {commission}")
        print(f"      Time: {fill_time}")
        print()
    
    def _print_order_details(self, order: dict, index: int):
        """Print detailed order information"""
        product = order.get("product", {})
        symbol = product.get("symbol", "Unknown")
        side = order.get("side", "Unknown")
        size = order.get("size", "0")
        state = order.get("state", "Unknown")
        
        print(f"   {index}. {symbol} - {side.upper()}")
        print(f"      Size: {size}, State: {state}")
        print()
    
    def _analyze_fills(self, fills: list):
        """Analyze the fills data"""
        print("\n📊 Data Analysis:")
        print("-" * 30)
        
        if not fills:
            return
        
        # Count by side
        buy_fills = len([f for f in fills if f.get("side") == "buy"])
        sell_fills = len([f for f in fills if f.get("side") == "sell"])
        
        print(f"📈 Buy fills: {buy_fills}")
        print(f"📉 Sell fills: {sell_fills}")
        
        # Count by symbol
        symbols = {}
        for fill in fills:
            symbol = fill.get("product", {}).get("symbol", "Unknown")
            symbols[symbol] = symbols.get(symbol, 0) + 1
        
        print(f"\n🎯 Most traded symbols:")
        for symbol, count in sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {symbol}: {count} fills")
        
        # Time range
        timestamps = [f.get("created_at", 0) for f in fills if f.get("created_at")]
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            earliest_time = datetime.fromtimestamp(earliest / 1000).strftime("%Y-%m-%d %H:%M")
            latest_time = datetime.fromtimestamp(latest / 1000).strftime("%Y-%m-%d %H:%M")
            print(f"\n📅 Time range: {earliest_time} to {latest_time}")
    
    async def comprehensive_fetch(self):
        """Comprehensive fetch using multiple endpoints"""
        print("\n🚀 Starting Comprehensive Historical Data Fetch")
        print("=" * 60)
        
        if not self.enabled:
            print("❌ API not configured properly")
            return
        
        # Test authentication first
        auth_success = await self.test_authentication()
        if not auth_success:
            print("\n❌ Authentication failed - cannot proceed with data fetching")
            return
        
        results = {}
        
        # Try multiple time periods
        time_periods = [7, 30, 90]
        
        for days in time_periods:
            print(f"\n{'='*20} {days} DAYS PERIOD {'='*20}")
            
            # Try fills endpoint
            fills = await self.fetch_fills_history(days)
            if fills is not None and len(fills) > 0:
                results[f'fills_{days}d'] = fills
                break  # Found data, no need to try longer periods
            
            await asyncio.sleep(1)  # Rate limiting
        
        # Try orders endpoint
        orders = await self.fetch_orders_history(30)
        if orders is not None:
            results['orders'] = orders
        
        # Try trades endpoint
        trades = await self.fetch_trades_history(30)
        if trades is not None:
            results['trades'] = trades
        
        # Summary
        print(f"\n📊 FETCH SUMMARY")
        print("=" * 60)
        
        total_records = 0
        for key, data in results.items():
            count = len(data) if data else 0
            total_records += count
            print(f"✅ {key}: {count} records")
        
        if total_records > 0:
            print(f"\n🎉 Successfully fetched {total_records} total records!")
            
            # Save to file for analysis
            output_file = f"delta_historical_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Data saved to: {output_file}")
            
        else:
            print("⚠️ No historical data found")
            print("\nPossible reasons:")
            print("• No trading activity on your account")
            print("• API permissions insufficient")
            print("• Different endpoint required")
            print("• Account verification needed")
        
        return results

async def main():
    """Main function to fetch historical trades"""
    fetcher = DeltaHistoricalTradesFetcher()
    
    if not fetcher.enabled:
        print("Please configure your Delta Exchange API credentials first:")
        print("python check_delta_config.py")
        return
    
    try:
        await fetcher.comprehensive_fetch()
    except KeyboardInterrupt:
        print("\n⚠️ Fetch interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Delta Exchange Historical Data Fetch")
    asyncio.run(main())
