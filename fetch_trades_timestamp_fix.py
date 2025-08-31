#!/usr/bin/env python3
"""
Delta Exchange API with Timestamp Synchronization Fix
Addresses the 5-second server time requirement
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

class DeltaAPITimestampFixed:
    """Delta Exchange API with proper timestamp synchronization"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        self.server_time_offset = 0  # Will be calculated
        
        print("🔧 Delta Exchange API - Timestamp Synchronization Fix")
        print("=" * 60)
        
        if not self.api_key or not self.api_secret:
            print("❌ API credentials not configured")
            self.enabled = False
        else:
            print(f"✅ API Key: {self.api_key[:8]}...")
            print(f"✅ API Secret: {self.api_secret[:8]}...")
            self.enabled = True
    
    async def get_server_time(self):
        """Get server time to synchronize timestamps"""
        print("\n⏰ Synchronizing with Delta Exchange server time...")
        
        try:
            # Use public endpoint to get server time
            async with httpx.AsyncClient(timeout=30.0) as client:
                local_time_before = time.time()
                response = await client.get(f"{self.base_url}/v2/products")
                local_time_after = time.time()
                
                if response.status_code == 200:
                    # Get server time from response headers
                    server_time_header = response.headers.get('date')
                    if server_time_header:
                        # Parse server time
                        from email.utils import parsedate_to_datetime
                        server_time = parsedate_to_datetime(server_time_header).timestamp()
                        local_time_avg = (local_time_before + local_time_after) / 2
                        
                        self.server_time_offset = server_time - local_time_avg
                        
                        print(f"✅ Server time synchronized")
                        print(f"   Local time: {datetime.fromtimestamp(local_time_avg)}")
                        print(f"   Server time: {datetime.fromtimestamp(server_time)}")
                        print(f"   Offset: {self.server_time_offset:.3f} seconds")
                        
                        return True
                    else:
                        print("⚠️ No date header in response, using local time")
                        return True
                else:
                    print(f"❌ Failed to get server time: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error getting server time: {str(e)}")
            print("⚠️ Proceeding with local time")
            return True
    
    def get_synchronized_timestamp(self):
        """Get timestamp synchronized with server"""
        local_time = time.time()
        synchronized_time = local_time + self.server_time_offset
        return str(int(synchronized_time))
    
    def _generate_signature_fixed(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate signature with proper format"""
        # According to research: method + timestamp + requestPath + queryParams + body
        message = f"{method}{timestamp}{request_path}{body}"
        
        print(f"🔐 Signature Debug:")
        print(f"   Method: {method}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Path: {request_path}")
        print(f"   Message: {message}")
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"   Signature: {signature[:16]}...")
        
        return signature
    
    def _get_headers_fixed(self, method: str, request_path: str, body: str = "") -> dict:
        """Get headers with synchronized timestamp"""
        timestamp = self.get_synchronized_timestamp()
        signature = self._generate_signature_fixed(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "MindTrade-AI/1.0",
            "Accept": "application/json"
        }
    
    async def test_authentication_fixed(self):
        """Test authentication with timestamp fix"""
        print("\n🔐 Testing Authentication (Timestamp Fixed)...")
        print("-" * 50)
        
        try:
            # First synchronize time
            await self.get_server_time()
            
            endpoint = "/v2/profile"
            headers = self._get_headers_fixed("GET", endpoint)
            
            print(f"\n📡 Making authenticated request...")
            print(f"   Endpoint: {endpoint}")
            print(f"   Timestamp: {headers['timestamp']}")
            print(f"   API Key: {headers['api-key'][:8]}...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
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
                        print("\n🔍 Advanced Troubleshooting:")
                        print("1. 🕐 Timestamp synchronization (just attempted)")
                        print("2. 🔒 IP whitelisting - check exact IP match")
                        print("3. 🔑 API key regeneration needed")
                        print("4. 🏢 Account verification status")
                        print("5. 🌍 Production vs Testnet environment")
                        
                        # Try without IP restriction
                        print("\n💡 Suggestion: Temporarily remove IP restriction")
                        print("   Go to API settings and clear the IP whitelist field")
                        
                    return False
                    
                else:
                    print(f"❌ Unexpected error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    async def test_without_ip_restriction(self):
        """Test with suggestion to remove IP restriction"""
        print("\n🔓 Alternative: Test Without IP Restriction")
        print("-" * 50)
        print("If authentication still fails, try this:")
        print("1. Go to: https://www.delta.exchange/app/account/api")
        print("2. Edit your API key")
        print("3. Clear the 'Whitelisted IP' field (leave it empty)")
        print("4. Keep Trading + Read Data permissions")
        print("5. Save changes")
        print("6. Run this script again")
        print("\nThis will allow API access from any IP (less secure but helps isolate the issue)")
    
    async def comprehensive_fix_attempt(self):
        """Comprehensive fix attempt"""
        print("\n🚀 Starting Comprehensive Fix Attempt")
        print("=" * 60)
        
        if not self.enabled:
            print("❌ API credentials not configured")
            return False
        
        # Attempt authentication with all fixes
        auth_success = await self.test_authentication_fixed()
        
        if auth_success:
            print("\n🎉 SUCCESS! All issues resolved!")
            return True
        else:
            print("\n❌ Authentication still failing")
            await self.test_without_ip_restriction()
            
            print("\n🔧 Additional Steps to Try:")
            print("1. Generate completely new API keys")
            print("2. Use different network/internet connection")
            print("3. Check account verification status")
            print("4. Contact Delta Exchange support with these details:")
            print(f"   - API Key: {self.api_key[:8]}...")
            print(f"   - Your IP: 103.164.200.114")
            print(f"   - Error: invalid_api_key")
            print(f"   - Timestamp: {self.get_synchronized_timestamp()}")
            
            return False

async def main():
    """Main function"""
    fixer = DeltaAPITimestampFixed()
    
    if not fixer.enabled:
        print("❌ Please configure API credentials in .env file")
        return
    
    try:
        await fixer.comprehensive_fix_attempt()
    except KeyboardInterrupt:
        print("\n⚠️ Fix attempt interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Delta Exchange Timestamp Fix")
    asyncio.run(main())
