#!/usr/bin/env python3
"""
Delta Exchange API Diagnostic Tool
Comprehensive debugging for API authentication issues
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

class DeltaAPIDiagnostic:
    """Comprehensive diagnostic tool for Delta Exchange API issues"""
    
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        print("🔍 Delta Exchange API Diagnostic Tool")
        print("=" * 60)
    
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
    
    async def test_basic_connectivity(self):
        """Test basic connectivity to Delta Exchange"""
        print("\n🌐 Testing Basic Connectivity...")
        print("-" * 40)
        
        try:
            # Test public endpoint first
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/v2/products")
                
                if response.status_code == 200:
                    print("✅ Basic connectivity to Delta Exchange API works")
                    data = response.json()
                    products = data.get("result", [])
                    print(f"✅ Public API accessible - {len(products)} products available")
                    return True
                else:
                    print(f"❌ Basic connectivity failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Connectivity error: {str(e)}")
            return False
    
    async def test_ip_whitelisting(self):
        """Test if IP whitelisting is the issue"""
        print("\n🔒 Testing IP Whitelisting...")
        print("-" * 40)
        
        try:
            # Get current IP
            async with httpx.AsyncClient(timeout=30.0) as client:
                ip_response = await client.get("https://ifconfig.me/ip")
                current_ip = ip_response.text.strip()
                print(f"📍 Your current IP: {current_ip}")
        except:
            print("⚠️ Could not determine current IP")
            current_ip = "Unknown"
        
        # Test authentication
        try:
            endpoint = "/v2/profile"
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                
                if response.status_code == 401:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    
                    if error_code == "invalid_api_key":
                        print("❌ IP whitelisting might be the issue")
                        print(f"💡 Your IP ({current_ip}) might not be whitelisted")
                        print("🔧 Solutions:")
                        print("   1. Add your current IP to the whitelist")
                        print("   2. Remove IP restriction temporarily")
                        print("   3. Check if you're using VPN/proxy")
                        return False
                elif response.status_code == 200:
                    print("✅ IP whitelisting is working correctly")
                    return True
                    
        except Exception as e:
            print(f"❌ IP test error: {str(e)}")
            return False
    
    async def test_api_key_format(self):
        """Test API key format and basic validation"""
        print("\n🔑 Testing API Key Format...")
        print("-" * 40)
        
        if not self.api_key or not self.api_secret:
            print("❌ API keys not found in environment")
            return False
        
        print(f"✅ API Key length: {len(self.api_key)} characters")
        print(f"✅ API Secret length: {len(self.api_secret)} characters")
        print(f"✅ API Key format: {self.api_key[:8]}...")
        print(f"✅ API Secret format: {self.api_secret[:8]}...")
        
        # Check for common issues
        issues = []
        
        if len(self.api_key) < 16:
            issues.append("API key seems too short")
        
        if len(self.api_secret) < 32:
            issues.append("API secret seems too short")
        
        if self.api_key.startswith("your-") or self.api_secret.startswith("your-"):
            issues.append("Still using placeholder values")
        
        if " " in self.api_key or " " in self.api_secret:
            issues.append("API keys contain spaces")
        
        if issues:
            print("⚠️ Potential issues found:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            print("✅ API key format looks good")
            return True
    
    async def test_signature_generation(self):
        """Test HMAC signature generation"""
        print("\n🔐 Testing Signature Generation...")
        print("-" * 40)
        
        try:
            timestamp = str(int(time.time()))
            endpoint = "/v2/profile"
            signature = self._generate_signature("GET", timestamp, endpoint)
            
            print(f"✅ Timestamp: {timestamp}")
            print(f"✅ Endpoint: {endpoint}")
            print(f"✅ Signature: {signature[:16]}...")
            print(f"✅ Signature length: {len(signature)} characters")
            
            # Test with different message
            test_message = f"GET{timestamp}{endpoint}"
            expected_sig = hmac.new(
                self.api_secret.encode('utf-8'),
                test_message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if signature == expected_sig:
                print("✅ Signature generation is working correctly")
                return True
            else:
                print("❌ Signature generation mismatch")
                return False
                
        except Exception as e:
            print(f"❌ Signature generation error: {str(e)}")
            return False
    
    async def test_different_endpoints(self):
        """Test different API endpoints to isolate the issue"""
        print("\n🎯 Testing Different Endpoints...")
        print("-" * 40)
        
        endpoints_to_test = [
            "/v2/profile",
            "/v2/wallet/balances",
            "/v2/orders/history",
            "/v2/positions"
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                headers = self._get_headers("GET", endpoint)
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                    
                    results[endpoint] = {
                        "status": response.status_code,
                        "success": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        print(f"✅ {endpoint}: Success")
                    elif response.status_code == 401:
                        print(f"❌ {endpoint}: Authentication failed")
                    else:
                        print(f"⚠️ {endpoint}: Status {response.status_code}")
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)}")
                results[endpoint] = {"status": "error", "success": False}
        
        # Analysis
        successful = sum(1 for r in results.values() if r.get("success", False))
        
        if successful > 0:
            print(f"\n✅ {successful}/{len(endpoints_to_test)} endpoints working")
            print("🎉 API keys are valid!")
            return True
        else:
            print(f"\n❌ 0/{len(endpoints_to_test)} endpoints working")
            print("💡 API keys might be invalid or have permission issues")
            return False
    
    async def comprehensive_diagnosis(self):
        """Run comprehensive diagnosis"""
        print("\n🚀 Starting Comprehensive API Diagnosis")
        print("=" * 60)
        
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("API Key Format", self.test_api_key_format),
            ("Signature Generation", self.test_signature_generation),
            ("IP Whitelisting", self.test_ip_whitelisting),
            ("Different Endpoints", self.test_different_endpoints)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name.upper()} {'='*20}")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with error: {str(e)}")
                results[test_name] = False
        
        # Final analysis
        print(f"\n📊 DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        passed_tests = sum(1 for r in results.values() if r)
        total_tests = len(results)
        
        print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
        
        if results.get("Different Endpoints", False):
            print("\n🎉 SUCCESS: Your API keys are working!")
            print("✅ You can fetch your personal trades")
            
        elif results.get("Basic Connectivity", False) and results.get("API Key Format", False):
            print("\n💡 LIKELY ISSUES:")
            
            if not results.get("IP Whitelisting", True):
                print("🔒 IP Whitelisting: Your IP might not be whitelisted")
                print("   Solution: Add your current IP or remove IP restriction")
            
            print("🔑 API Permissions: Check if 'Read Data' permission is enabled")
            print("🏢 Account Status: Ensure account is fully verified")
            print("🌍 Environment: Make sure using production keys (not testnet)")
            
        else:
            print("\n❌ CRITICAL ISSUES FOUND:")
            print("💡 Recommended actions:")
            print("1. Generate completely new API keys")
            print("2. Ensure proper permissions (Read Data)")
            print("3. Check account verification status")
            print("4. Contact Delta Exchange support")
        
        return results

async def main():
    """Main diagnostic function"""
    diagnostic = DeltaAPIDiagnostic()
    
    try:
        await diagnostic.comprehensive_diagnosis()
    except KeyboardInterrupt:
        print("\n⚠️ Diagnosis interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostic error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Delta Exchange API Diagnosis")
    asyncio.run(main())
