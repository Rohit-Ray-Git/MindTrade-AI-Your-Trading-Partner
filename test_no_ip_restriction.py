#!/usr/bin/env python3
"""
Test Delta Exchange API without IP restriction
This helps isolate if the issue is IP whitelisting or something else
"""

import os
import asyncio
import json
import hmac
import hashlib
import time
from datetime import datetime
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

class SimpleAPITest:
    """Simple API test to isolate the issue"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("🧪 Simple Delta Exchange API Test")
        print("🎯 Goal: Isolate if the issue is IP whitelisting or API keys")
        print("=" * 60)
        
        if not self.api_key or not self.api_secret:
            print("❌ API credentials not configured")
            self.enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature"""
        message = f"{method}{timestamp}{request_path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> dict:
        """Get headers for API request"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "MindTrade-AI/1.0"
        }
    
    async def test_simple_auth(self):
        """Simple authentication test"""
        print("\n🔑 Testing Basic Authentication...")
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
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    print("✅ SUCCESS! API keys are working!")
                    data = response.json()
                    print(f"Account: {data.get('email', 'N/A')}")
                    return True
                    
                elif response.status_code == 401:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    print(f"❌ Auth failed: {error_code}")
                    return False
                    
                else:
                    print(f"❌ Unexpected status: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    async def get_current_ip(self):
        """Get current IP address"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://ifconfig.me/ip")
                return response.text.strip()
        except:
            return "Unknown"
    
    async def run_test(self):
        """Run the simple test"""
        print("\n🚀 Running Simple API Test")
        print("=" * 40)
        
        if not self.enabled:
            print("❌ API keys not configured")
            return
        
        # Get current IP
        current_ip = await self.get_current_ip()
        print(f"📍 Your current IP: {current_ip}")
        
        # Test authentication
        success = await self.test_simple_auth()
        
        print("\n📊 TEST RESULTS")
        print("=" * 40)
        
        if success:
            print("🎉 SUCCESS! Your API keys are working!")
            print("✅ The issue was likely IP whitelisting")
            print("✅ You can now fetch your personal trades")
            
            # Now try to fetch trades
            print("\n🚀 Attempting to fetch trades...")
            await self.test_fetch_trades()
            
        else:
            print("❌ FAILED: API keys still not working")
            print("💡 This means the issue is NOT IP whitelisting")
            print("\n🔧 Next steps to try:")
            print("1. 🆕 Generate completely new API keys")
            print("2. 🏢 Check account verification status")
            print("3. 🌍 Verify you're using production Delta Exchange (not testnet)")
            print("4. 💬 Contact Delta Exchange support with these details:")
            print(f"   - Error: invalid_api_key persists without IP restriction")
            print(f"   - API Key: {self.api_key[:8]}...")
            print(f"   - Account verification: [check your account status]")
    
    async def test_fetch_trades(self):
        """Test fetching trades if authentication works"""
        print("\n📈 Testing Trade Fetch...")
        print("-" * 30)
        
        try:
            endpoint = "/v2/orders"
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"Orders Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("result", []) if isinstance(data, dict) else data
                    print(f"✅ Found {len(orders)} orders")
                    
                    # Test fills endpoint
                    fills_endpoint = "/v2/orders/history/fills"
                    fills_headers = self._get_headers("GET", fills_endpoint)
                    
                    fills_response = await client.get(
                        f"{self.base_url}{fills_endpoint}",
                        headers=fills_headers
                    )
                    
                    print(f"Fills Status: {fills_response.status_code}")
                    
                    if fills_response.status_code == 200:
                        fills_data = fills_response.json()
                        fills = fills_data.get("result", []) if isinstance(fills_data, dict) else fills_data
                        print(f"✅ Found {len(fills)} trade fills")
                        
                        if len(fills) > 0:
                            print("🎉 SUCCESS! You can fetch your personal trades!")
                            
                            # Save sample data
                            sample_data = {
                                "orders_count": len(orders),
                                "fills_count": len(fills),
                                "sample_fills": fills[:3] if fills else [],
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            with open("delta_test_success.json", "w") as f:
                                json.dump(sample_data, f, indent=2, default=str)
                            
                            print("💾 Sample data saved to: delta_test_success.json")
                        else:
                            print("ℹ️ No trade fills found (you might not have trading history)")
                    else:
                        print(f"⚠️ Fills endpoint failed: {fills_response.status_code}")
                else:
                    print(f"⚠️ Orders endpoint failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error testing trade fetch: {str(e)}")

async def main():
    """Main function"""
    print("🎯 INSTRUCTIONS BEFORE RUNNING:")
    print("=" * 50)
    print("1. Go to: https://www.delta.exchange/app/account/api")
    print("2. Edit your API key")
    print("3. CLEAR the 'Whitelisted IP' field (leave it empty)")
    print("4. Ensure 'Trading' + 'Read Data' permissions are enabled")
    print("5. Save changes")
    print("6. Then run this test")
    print("\nThis will help us determine if the issue is IP whitelisting or API keys")
    
    input("\nPress Enter when you've removed IP restriction...")
    
    tester = SimpleAPITest()
    
    try:
        await tester.run_test()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
