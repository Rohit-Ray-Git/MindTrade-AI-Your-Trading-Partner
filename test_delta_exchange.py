#!/usr/bin/env python3
"""
Delta Exchange API Test Script
Independent test to verify Delta Exchange API connectivity and trade fetching
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeltaExchangeAPITester:
    """Standalone Delta Exchange API tester"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("🔍 Delta Exchange API Tester")
        print("=" * 50)
        
        # Check API credentials
        if not self.api_key or not self.api_secret:
            print("❌ API credentials not found in environment variables")
            print("Please set DELTA_API_KEY and DELTA_API_SECRET in your .env file")
            self.enabled = False
        elif self.api_key.startswith("your-") or self.api_secret.startswith("your-"):
            print("❌ API credentials are using placeholder values")
            print("Please replace with your actual Delta Exchange API credentials")
            self.enabled = False
        else:
            print("✅ API credentials found")
            print(f"API Key: {self.api_key[:8]}...")
            print(f"API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature for Delta Exchange API"""
        import hmac
        import hashlib
        
        message = method + timestamp + request_path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> dict:
        """Get headers with authentication for API requests"""
        import time
        
        timestamp = str(int(time.time()))
        signature = self._generate_signature(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json"
        }
    
    async def test_public_endpoint(self):
        """Test public endpoint (no authentication required)"""
        print("\n🌐 Testing Public Endpoint")
        print("-" * 30)
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/products",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("result", [])
                    print(f"✅ Public API working - Found {len(products)} products")
                    
                    # Show a few example products
                    if products:
                        print("📊 Sample products:")
                        for product in products[:3]:
                            print(f"   • {product.get('symbol', 'Unknown')} - {product.get('description', 'No description')}")
                    
                    return True
                else:
                    print(f"❌ Public API failed - Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        
        except Exception as e:
            print(f"❌ Public API test failed: {str(e)}")
            return False
    
    async def test_authentication(self):
        """Test API authentication with account info endpoint"""
        print("\n🔐 Testing Authentication")
        print("-" * 30)
        
        if not self.enabled:
            print("❌ Skipping authentication test - API credentials not configured")
            return False
        
        try:
            import httpx
            
            endpoint = "/v2/profile"
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Authentication successful")
                    print(f"📧 Account Email: {data.get('email', 'Not available')}")
                    print(f"🆔 Account ID: {data.get('id', 'Not available')}")
                    return True
                    
                elif response.status_code == 401:
                    print("❌ Authentication failed - Invalid API credentials")
                    print("Please check your API key and secret")
                    return False
                    
                else:
                    print(f"❌ Authentication test failed - Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")
            return False
    
    async def test_trade_history(self):
        """Test fetching trade history/fills"""
        print("\n📊 Testing Trade History (Fills)")
        print("-" * 30)
        
        if not self.enabled:
            print("❌ Skipping trade history test - API credentials not configured")
            return False
        
        try:
            import httpx
            
            # Test fills endpoint
            endpoint = "/v2/orders/history/fills"
            
            # Query parameters for recent fills
            params = {
                "page_size": 10,
                "start_time": int((datetime.now() - timedelta(days=30)).timestamp())
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            headers = self._get_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    fills = data.get("result", [])
                    
                    print(f"✅ Trade history fetched successfully")
                    print(f"📈 Found {len(fills)} fills in the last 30 days")
                    
                    if fills:
                        print("\n💹 Recent fills:")
                        for i, fill in enumerate(fills[:5], 1):
                            symbol = fill.get("product", {}).get("symbol", "Unknown")
                            side = fill.get("side", "Unknown")
                            size = fill.get("size", "0")
                            price = fill.get("price", "0")
                            timestamp = fill.get("created_at", 0)
                            
                            if timestamp:
                                fill_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
                            else:
                                fill_time = "Unknown"
                            
                            print(f"   {i}. {symbol} {side.upper()} - Size: {size}, Price: {price}, Time: {fill_time}")
                    
                    else:
                        print("ℹ️  No fills found in the last 30 days")
                        print("This could mean:")
                        print("   • No trading activity in the period")
                        print("   • API permissions might be limited")
                        print("   • Try increasing the time range")
                    
                    return True
                    
                elif response.status_code == 401:
                    print("❌ Trade history failed - Authentication error")
                    print("API key might not have the required permissions")
                    return False
                    
                else:
                    print(f"❌ Trade history failed - Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        
        except Exception as e:
            print(f"❌ Trade history test failed: {str(e)}")
            return False
    
    async def test_specific_endpoints(self):
        """Test other specific endpoints"""
        print("\n🔧 Testing Additional Endpoints")
        print("-" * 30)
        
        if not self.enabled:
            print("❌ Skipping additional tests - API credentials not configured")
            return
        
        endpoints_to_test = [
            ("/v2/orders", "Active Orders"),
            ("/v2/positions", "Current Positions"),
            ("/v2/wallet/balances", "Wallet Balances")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                import httpx
                
                headers = self._get_headers("GET", endpoint)
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("result", [])
                        print(f"✅ {description}: {len(result)} items")
                    elif response.status_code == 401:
                        print(f"❌ {description}: Authentication failed")
                    else:
                        print(f"⚠️ {description}: Status {response.status_code}")
            
            except Exception as e:
                print(f"❌ {description}: {str(e)}")
    
    def print_recommendations(self):
        """Print recommendations based on test results"""
        print("\n💡 Recommendations")
        print("=" * 50)
        
        if not self.enabled:
            print("1. ✅ Create a .env file in your project root")
            print("2. ✅ Add your Delta Exchange API credentials:")
            print("   DELTA_API_KEY=your_actual_api_key")
            print("   DELTA_API_SECRET=your_actual_api_secret")
            print("3. ✅ Make sure API key has 'Read' permissions")
            print("4. ✅ Restart the application after updating .env")
        else:
            print("1. ✅ API credentials are configured")
            print("2. ✅ Test the authentication endpoint")
            print("3. ✅ Check API key permissions on Delta Exchange")
            print("4. ✅ Ensure you have some trading history for testing")
        
        print("\n📚 Delta Exchange API Documentation:")
        print("   https://docs.delta.exchange/")
        print("\n🔑 Get API Keys:")
        print("   https://www.delta.exchange/app/account/api")

async def run_all_tests():
    """Run all Delta Exchange API tests"""
    tester = DeltaExchangeAPITester()
    
    print(f"\n🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Test public endpoint (always works)
    results['public'] = await tester.test_public_endpoint()
    
    # Test authentication (requires valid credentials)
    results['auth'] = await tester.test_authentication()
    
    # Test trade history (requires valid credentials and permissions)
    results['trades'] = await tester.test_trade_history()
    
    # Test additional endpoints
    await tester.test_specific_endpoints()
    
    # Summary
    print("\n🏁 Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    test_names = {
        'public': 'Public API',
        'auth': 'Authentication',
        'trades': 'Trade History'
    }
    
    for test_key, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_names[test_key]:15} : {status}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your Delta Exchange API is working correctly.")
    elif results.get('public', False) and results.get('auth', False):
        print("✅ API is working! Trade history might be empty or need different parameters.")
    elif results.get('public', False):
        print("⚠️ API is reachable but authentication failed. Check your credentials.")
    else:
        print("❌ API connection issues. Check your internet connection and API status.")
    
    # Print recommendations
    tester.print_recommendations()
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🚀 Starting Delta Exchange API Test Suite")
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
