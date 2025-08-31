#!/usr/bin/env python3
"""
Delta Exchange API Key Checker
Quick verification of your API key setup
"""

import os
from dotenv import load_dotenv

def check_api_keys():
    """Check API key configuration"""
    print("🔍 Delta Exchange API Key Checker")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("DELTA_API_KEY")
    api_secret = os.getenv("DELTA_API_SECRET")
    
    print("\n📋 Current Configuration:")
    print("-" * 30)
    
    if not api_key:
        print("❌ DELTA_API_KEY: Not found in .env file")
    elif api_key.startswith("your-"):
        print(f"⚠️ DELTA_API_KEY: Still using placeholder ({api_key})")
    else:
        print(f"✅ DELTA_API_KEY: Configured ({api_key[:8]}...)")
    
    if not api_secret:
        print("❌ DELTA_API_SECRET: Not found in .env file")
    elif api_secret.startswith("your-"):
        print(f"⚠️ DELTA_API_SECRET: Still using placeholder ({api_secret[:8]}...)")
    else:
        print(f"✅ DELTA_API_SECRET: Configured ({api_secret[:8]}...)")
    
    print("\n🎯 Status Assessment:")
    print("-" * 30)
    
    if not api_key or not api_secret:
        print("❌ API keys not configured")
        print("📝 Action needed: Add API keys to .env file")
        
    elif api_key.startswith("your-") or api_secret.startswith("your-"):
        print("⚠️ Using placeholder API keys")
        print("📝 Action needed: Replace with real API keys from Delta Exchange")
        
    else:
        print("✅ API keys are configured")
        print("🔧 Status: Ready to test authentication")
        print("📝 If authentication fails, keys might be invalid/expired")
    
    print("\n💡 Next Steps:")
    print("-" * 30)
    
    if not api_key or not api_secret or api_key.startswith("your-") or api_secret.startswith("your-"):
        print("1. 🔑 Go to https://www.delta.exchange/app/account/api")
        print("2. 🆕 Create NEW API keys with 'Read Data' permission")
        print("3. 📝 Copy the keys to your .env file:")
        print("   DELTA_API_KEY=your_actual_api_key")
        print("   DELTA_API_SECRET=your_actual_api_secret")
        print("4. 🔄 Run this checker again")
        print("5. 🚀 Run: python fetch_personal_trades.py")
    else:
        print("1. 🚀 Run: python fetch_personal_trades.py")
        print("2. 🔍 If authentication fails:")
        print("   - Generate NEW API keys (current ones might be expired)")
        print("   - Ensure 'Read Data' permission is enabled")
        print("   - Check account verification status")
        print("   - Delete old API keys before creating new ones")
    
    print("\n📚 Full Setup Guide: See DELTA_API_SETUP_GUIDE.md")

if __name__ == "__main__":
    check_api_keys()
