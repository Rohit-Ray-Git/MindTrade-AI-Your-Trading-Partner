#!/usr/bin/env python3
"""
Fetch Personal Trades from Delta Exchange
Complete solution for getting your trading history from Delta Exchange API
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

class DeltaPersonalTradesFetcher:
    """Fetches personal trading history from Delta Exchange"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("📊 Delta Exchange Personal Trades Fetcher")
        print("=" * 60)
        
        if not self.api_key or not self.api_secret or self.api_key.startswith("your-"):
            print("❌ API credentials not configured properly")
            print("\n💡 To fix this:")
            print("1. Go to https://www.delta.exchange/app/account/api")
            print("2. Create new API keys with 'Read Data' permission")
            print("3. Update your .env file with the new keys")
            self.enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature for Delta Exchange API"""
        # Create the message to sign
        message = f"{method}{timestamp}{request_path}{body}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_auth_headers(self, method: str, request_path: str, body: str = "") -> dict:
        """Get authenticated headers for API requests"""
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
        """Test API authentication"""
        print("\n🔐 Testing API Authentication...")
        print("-" * 40)
        
        try:
            endpoint = "/v2/profile"
            headers = self._get_auth_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Authentication successful!")
                    print(f"User ID: {data.get('id', 'N/A')}")
                    print(f"Email: {data.get('email', 'N/A')}")
                    return True
                    
                elif response.status_code == 401:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    
                    print(f"❌ Authentication failed: {error_code}")
                    print(f"Response: {response.text}")
                    
                    if error_code == "invalid_api_key":
                        print("\n💡 API Key Issues - Try these solutions:")
                        print("1. Generate NEW API keys (old ones might be expired)")
                        print("2. Ensure API key has 'Read Data' permission")
                        print("3. Check if account is fully verified")
                        print("4. Make sure you're using PRODUCTION keys (not testnet)")
                        
                    return False
                    
                else:
                    print(f"❌ Unexpected error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    async def fetch_fills_history(self, days_back: int = 30, page_size: int = 100):
        """Fetch fills (executed trades) history"""
        print(f"\n📈 Fetching Your Trade Fills ({days_back} days)...")
        print("-" * 50)
        
        try:
            # Calculate date range
            end_time = int(time.time())
            start_time = end_time - (days_back * 24 * 60 * 60)
            
            endpoint = "/v2/orders/history/fills"
            
            # Build query parameters
            params = {
                "page_size": page_size,
                "start_time": start_time,
                "end_time": end_time
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            print(f"📅 Date Range: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
            print(f"🔗 Endpoint: {full_endpoint}")
            
            headers = self._get_auth_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle both result array and paginated response
                    if isinstance(data, list):
                        fills = data
                    else:
                        fills = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(fills)} fills")
                    
                    if fills:
                        print("\n📋 Your Recent Trades:")
                        self._analyze_personal_fills(fills)
                        return fills
                    else:
                        print("ℹ️ No fills found in the specified period")
                        print("This could mean:")
                        print("• No trading activity in the date range")
                        print("• Try extending the date range")
                        print("• Check different endpoints")
                        return []
                
                elif response.status_code == 401:
                    print("❌ Unauthorized - Authentication failed")
                    print("Please check your API keys and permissions")
                    return None
                    
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching fills: {str(e)}")
            return None
    
    async def fetch_orders_history(self, days_back: int = 30):
        """Fetch orders history"""
        print(f"\n📋 Fetching Your Orders History ({days_back} days)...")
        print("-" * 50)
        
        try:
            endpoint = "/v2/orders/history"
            
            # Try with different parameters
            params = {
                "page_size": 100,
                "state": "closed"  # Only completed orders
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            headers = self._get_auth_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        orders = data
                    else:
                        orders = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(orders)} orders")
                    
                    if orders:
                        print("\n📋 Your Recent Orders:")
                        for i, order in enumerate(orders[:5], 1):
                            self._print_order_summary(order, i)
                        
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
    
    async def fetch_positions_history(self):
        """Fetch current and historical positions"""
        print(f"\n💼 Fetching Your Positions...")
        print("-" * 50)
        
        try:
            endpoint = "/v2/positions"
            headers = self._get_auth_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        positions = data
                    else:
                        positions = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(positions)} positions")
                    
                    if positions:
                        print("\n💼 Your Current Positions:")
                        for i, position in enumerate(positions[:10], 1):
                            self._print_position_summary(position, i)
                        
                        return positions
                    else:
                        print("ℹ️ No positions found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch positions: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching positions: {str(e)}")
            return None
    
    def _analyze_personal_fills(self, fills: list):
        """Analyze and display personal trading data"""
        if not fills:
            return
        
        # Trading statistics
        total_fills = len(fills)
        buy_fills = len([f for f in fills if f.get("side") == "buy"])
        sell_fills = len([f for f in fills if f.get("side") == "sell"])
        
        print(f"📊 Trading Statistics:")
        print(f"   Total Fills: {total_fills}")
        print(f"   Buy Orders: {buy_fills}")
        print(f"   Sell Orders: {sell_fills}")
        
        # Calculate total volume and fees
        total_volume = 0
        total_fees = 0
        symbols_traded = set()
        
        for fill in fills:
            size = float(fill.get("size", 0))
            price = float(fill.get("price", 0))
            fee = float(fill.get("commission", 0))
            
            total_volume += size * price
            total_fees += fee
            
            product = fill.get("product", {})
            symbol = product.get("symbol", "Unknown")
            symbols_traded.add(symbol)
        
        print(f"   Total Volume: ${total_volume:,.2f}")
        print(f"   Total Fees: ${total_fees:.4f}")
        print(f"   Symbols Traded: {len(symbols_traded)}")
        
        # Show recent fills
        print(f"\n📋 Recent Fills (Latest 5):")
        for i, fill in enumerate(fills[:5], 1):
            self._print_fill_summary(fill, i)
        
        # Show symbol breakdown
        if len(symbols_traded) > 0:
            print(f"\n🎯 Symbols Traded:")
            symbol_counts = {}
            for fill in fills:
                product = fill.get("product", {})
                symbol = product.get("symbol", "Unknown")
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {symbol}: {count} fills")
    
    def _print_fill_summary(self, fill: dict, index: int):
        """Print fill summary"""
        product = fill.get("product", {})
        symbol = product.get("symbol", "Unknown")
        side = fill.get("side", "Unknown")
        size = fill.get("size", "0")
        price = fill.get("price", "0")
        commission = fill.get("commission", "0")
        timestamp = fill.get("created_at")
        
        if timestamp:
            if isinstance(timestamp, (int, float)):
                # Unix timestamp (milliseconds)
                fill_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
            else:
                fill_time = str(timestamp)[:19]
        else:
            fill_time = "Unknown"
        
        print(f"   {index}. {symbol} - {side.upper()}")
        print(f"      Size: {size}, Price: {price}")
        print(f"      Fee: {commission}, Time: {fill_time}")
    
    def _print_order_summary(self, order: dict, index: int):
        """Print order summary"""
        product = order.get("product", {})
        symbol = product.get("symbol", "Unknown")
        side = order.get("side", "Unknown")
        size = order.get("size", "0")
        state = order.get("state", "Unknown")
        order_type = order.get("order_type", "Unknown")
        
        print(f"   {index}. {symbol} - {side.upper()} {order_type}")
        print(f"      Size: {size}, State: {state}")
    
    def _print_position_summary(self, position: dict, index: int):
        """Print position summary"""
        product = position.get("product", {})
        symbol = product.get("symbol", "Unknown")
        size = position.get("size", "0")
        entry_price = position.get("entry_price", "0")
        mark_price = position.get("mark_price", "0")
        unrealized_pnl = position.get("unrealized_pnl", "0")
        
        print(f"   {index}. {symbol}")
        print(f"      Size: {size}, Entry: {entry_price}")
        print(f"      Mark: {mark_price}, PnL: {unrealized_pnl}")
    
    async def comprehensive_personal_data_fetch(self):
        """Comprehensive fetch of all personal trading data"""
        print("\n🚀 Starting Comprehensive Personal Data Fetch")
        print("=" * 60)
        
        if not self.enabled:
            print("❌ API credentials not configured")
            return {}
        
        # Test authentication first
        auth_success = await self.test_authentication()
        if not auth_success:
            print("\n❌ Authentication failed - cannot fetch personal data")
            print("\n🔧 Next Steps:")
            print("1. Generate new API keys on Delta Exchange")
            print("2. Ensure 'Read Data' permission is enabled")
            print("3. Update your .env file with new keys")
            print("4. Restart this script")
            return {}
        
        print(f"\n🎉 Authentication successful! Fetching your trading data...")
        
        results = {}
        
        # Try multiple time periods for fills
        for days in [7, 30, 90]:
            print(f"\n{'='*20} LAST {days} DAYS {'='*20}")
            
            fills = await self.fetch_fills_history(days)
            if fills and len(fills) > 0:
                results[f'fills_{days}d'] = fills
                print(f"✅ Found {len(fills)} fills in last {days} days")
                break
            
            await asyncio.sleep(1)  # Rate limiting
        
        # Fetch orders
        orders = await self.fetch_orders_history(30)
        if orders:
            results['orders'] = orders
        
        # Fetch positions
        positions = await self.fetch_positions_history()
        if positions:
            results['positions'] = positions
        
        # Summary
        print(f"\n📊 PERSONAL DATA SUMMARY")
        print("=" * 60)
        
        total_records = 0
        for key, data in results.items():
            count = len(data) if data else 0
            total_records += count
            print(f"✅ {key}: {count} records")
        
        if total_records > 0:
            print(f"\n🎉 Successfully fetched {total_records} personal trading records!")
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"my_delta_trades_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"💾 Your trading data saved to: {output_file}")
            
            # Integration recommendations
            print(f"\n🔗 Integration with MindTrade AI:")
            if 'fills_7d' in results or 'fills_30d' in results or 'fills_90d' in results:
                print("   ✅ Import fills into MindTrade trade journal")
                print("   ✅ Analyze trading patterns and performance")
                print("   ✅ Generate AI coaching insights")
            
            return results
        
        else:
            print("ℹ️ No personal trading data found")
            print("This could mean:")
            print("• No recent trading activity")
            print("• API permissions need adjustment")
            print("• Account verification required")
            
            return {}

async def main():
    """Main function to fetch personal trades"""
    fetcher = DeltaPersonalTradesFetcher()
    
    if not fetcher.enabled:
        print("\n❌ Please configure Delta Exchange API credentials:")
        print("1. Edit your .env file")
        print("2. Add DELTA_API_KEY=your_actual_api_key")
        print("3. Add DELTA_API_SECRET=your_actual_api_secret")
        return
    
    try:
        await fetcher.comprehensive_personal_data_fetch()
    except KeyboardInterrupt:
        print("\n⚠️ Fetch interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Personal Trades Fetch from Delta Exchange")
    asyncio.run(main())
