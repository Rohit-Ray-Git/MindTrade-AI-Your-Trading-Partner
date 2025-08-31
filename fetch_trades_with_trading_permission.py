#!/usr/bin/env python3
"""
Fetch Personal Trades with Trading Permission
Updated based on official Delta Exchange customer service guidance
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

class DeltaTradesWithTradingPermission:
    """Fetch personal trades using Trading permission (official guidance)"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("📊 Delta Exchange Personal Trades Fetcher")
        print("🎯 Using TRADING permission (Official Customer Service Guidance)")
        print("=" * 70)
        
        if not self.api_key or not self.api_secret:
            print("❌ API credentials not configured")
            self.enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature for Delta Exchange API"""
        message = f"{method}{timestamp}{request_path}{body}"
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
    
    async def test_authentication_with_trading_permission(self):
        """Test API authentication with Trading permission"""
        print("\n🔐 Testing Authentication (Trading Permission Required)...")
        print("-" * 60)
        
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
                    print("✅ Authentication successful with Trading permission!")
                    print(f"User ID: {data.get('id', 'N/A')}")
                    print(f"Email: {data.get('email', 'N/A')}")
                    return True
                    
                elif response.status_code == 401:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    
                    print(f"❌ Authentication failed: {error_code}")
                    print(f"Response: {response.text}")
                    
                    print("\n💡 Based on Customer Service Guidance:")
                    print("1. ✅ Enable 'Trading' permission (REQUIRED)")
                    print("2. ✅ Keep 'Read Data' permission enabled")
                    print("3. ✅ Add your IP to whitelist: 103.164.200.114")
                    print("4. 🔄 Save changes and try again")
                    
                    return False
                    
                else:
                    print(f"❌ Unexpected error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    async def fetch_orders_endpoint(self):
        """Fetch from /orders endpoint (as recommended by customer service)"""
        print(f"\n📋 Fetching from /orders endpoint (Customer Service Recommended)...")
        print("-" * 60)
        
        try:
            endpoint = "/v2/orders"
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
                        orders = data
                    else:
                        orders = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(orders)} orders")
                    
                    if orders:
                        print("\n📋 Your Recent Orders:")
                        for i, order in enumerate(orders[:5], 1):
                            self._print_order_details(order, i)
                        
                        return orders
                    else:
                        print("ℹ️ No orders found")
                        return []
                
                else:
                    print(f"❌ Failed to fetch orders: {response.status_code}")
                    print(f"Response: {response.text}")
                    
                    if response.status_code == 401:
                        print("\n💡 Still getting 401? Check these:")
                        print("   ✅ Trading permission enabled?")
                        print("   ✅ IP whitelisted correctly?")
                        print("   🔄 Try regenerating API keys")
                    
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching orders: {str(e)}")
            return None
    
    async def fetch_order_history_fills(self, days_back: int = 30):
        """Fetch from /orders/history/fills endpoint"""
        print(f"\n📈 Fetching Trade Fills (Last {days_back} days)...")
        print("-" * 60)
        
        try:
            # Calculate date range
            end_time = int(time.time())
            start_time = end_time - (days_back * 24 * 60 * 60)
            
            endpoint = "/v2/orders/history/fills"
            params = {
                "page_size": 100,
                "start_time": start_time,
                "end_time": end_time
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
                        fills = data
                    else:
                        fills = data.get("result", [])
                    
                    print(f"✅ Successfully fetched {len(fills)} trade fills")
                    
                    if fills:
                        print("\n📈 Your Recent Trade Fills:")
                        self._analyze_fills(fills)
                        return fills
                    else:
                        print("ℹ️ No trade fills found in the specified period")
                        return []
                
                else:
                    print(f"❌ Failed to fetch fills: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error fetching fills: {str(e)}")
            return None
    
    async def fetch_positions(self):
        """Fetch positions data"""
        print(f"\n💼 Fetching Your Positions...")
        print("-" * 60)
        
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
                        for i, position in enumerate(positions[:5], 1):
                            self._print_position_details(position, i)
                        
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
    
    def _print_order_details(self, order: dict, index: int):
        """Print order details"""
        product = order.get("product", {})
        symbol = product.get("symbol", "Unknown")
        side = order.get("side", "Unknown")
        size = order.get("size", "0")
        state = order.get("state", "Unknown")
        order_type = order.get("order_type", "Unknown")
        created_at = order.get("created_at", "Unknown")
        
        print(f"   {index}. {symbol} - {side.upper()} {order_type}")
        print(f"      Size: {size}, State: {state}")
        print(f"      Created: {created_at}")
    
    def _print_position_details(self, position: dict, index: int):
        """Print position details"""
        product = position.get("product", {})
        symbol = product.get("symbol", "Unknown")
        size = position.get("size", "0")
        entry_price = position.get("entry_price", "0")
        mark_price = position.get("mark_price", "0")
        unrealized_pnl = position.get("unrealized_pnl", "0")
        
        print(f"   {index}. {symbol}")
        print(f"      Size: {size}, Entry: {entry_price}")
        print(f"      Mark: {mark_price}, PnL: {unrealized_pnl}")
    
    def _analyze_fills(self, fills: list):
        """Analyze trade fills"""
        if not fills:
            return
        
        total_fills = len(fills)
        buy_fills = len([f for f in fills if f.get("side") == "buy"])
        sell_fills = len([f for f in fills if f.get("side") == "sell"])
        
        print(f"📊 Trading Statistics:")
        print(f"   Total Fills: {total_fills}")
        print(f"   Buy Orders: {buy_fills}")
        print(f"   Sell Orders: {sell_fills}")
        
        # Show sample fills
        print(f"\n📋 Sample Fills:")
        for i, fill in enumerate(fills[:3], 1):
            product = fill.get("product", {})
            symbol = product.get("symbol", "Unknown")
            side = fill.get("side", "Unknown")
            size = fill.get("size", "0")
            price = fill.get("price", "0")
            commission = fill.get("commission", "0")
            
            print(f"   {i}. {symbol} - {side.upper()}")
            print(f"      Size: {size}, Price: {price}, Fee: {commission}")
    
    async def fetch_all_personal_data_with_trading_permission(self):
        """Comprehensive fetch using Trading permission"""
        print("\n🚀 Fetching All Personal Data (Trading Permission)")
        print("=" * 70)
        
        if not self.enabled:
            print("❌ API credentials not configured")
            return {}
        
        # Test authentication first
        auth_success = await self.test_authentication_with_trading_permission()
        if not auth_success:
            print("\n❌ Authentication failed")
            print("\n🔧 Required Actions:")
            print("1. Go to: https://www.delta.exchange/app/account/api")
            print("2. Edit your API key")
            print("3. ✅ Enable 'Trading' permission")
            print("4. ✅ Keep 'Read Data' permission")
            print("5. ✅ Add IP whitelist: 103.164.200.114")
            print("6. 💾 Save changes")
            print("7. 🔄 Run this script again")
            return {}
        
        print(f"\n🎉 Authentication successful with Trading permission!")
        
        results = {}
        
        # Fetch using recommended endpoints
        print(f"\n{'='*25} FETCHING PERSONAL TRADES {'='*25}")
        
        # 1. Orders endpoint (recommended by customer service)
        orders = await self.fetch_orders_endpoint()
        if orders:
            results['orders'] = orders
        
        # 2. Order history fills
        fills = await self.fetch_order_history_fills(30)
        if fills:
            results['fills'] = fills
        
        # 3. Positions
        positions = await self.fetch_positions()
        if positions:
            results['positions'] = positions
        
        # Summary
        print(f"\n📊 FETCH SUMMARY")
        print("=" * 70)
        
        total_records = 0
        for key, data in results.items():
            count = len(data) if data else 0
            total_records += count
            print(f"✅ {key}: {count} records")
        
        if total_records > 0:
            print(f"\n🎉 Successfully fetched {total_records} personal trading records!")
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"my_delta_trades_trading_permission_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"💾 Your complete trading data saved to: {output_file}")
            print(f"🔗 Ready for MindTrade AI integration!")
            
            return results
        
        else:
            print("ℹ️ No personal trading data found")
            print("This could mean:")
            print("• No recent trading activity")
            print("• Different date range needed")
            print("• API permissions still need adjustment")
            
            return {}

async def main():
    """Main function"""
    fetcher = DeltaTradesWithTradingPermission()
    
    if not fetcher.enabled:
        print("\n❌ Please configure Delta Exchange API credentials in .env file")
        return
    
    try:
        await fetcher.fetch_all_personal_data_with_trading_permission()
    except KeyboardInterrupt:
        print("\n⚠️ Fetch interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Personal Trades Fetch (Trading Permission Required)")
    asyncio.run(main())
