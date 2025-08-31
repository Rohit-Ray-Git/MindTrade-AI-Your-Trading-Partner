#!/usr/bin/env python3
"""
Delta Exchange Configuration Checker
Quick script to verify API configuration and provide setup guidance
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and has the required variables"""
    print("📁 Checking .env file configuration")
    print("=" * 50)
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Creating sample .env file...")
        
        sample_content = """# =============================================================================
# MindTrade AI - Environment Variables
# =============================================================================

# Google Gemini API Key (REQUIRED for AI features)
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-google-gemini-api-key-here

# Secret Key (generate your own random string)
SECRET_KEY=mindtrade-ai-super-secret-key-change-this-in-production-123456789

# Delta Exchange API (for auto-importing trades)
# Get from: https://www.delta.exchange/app/account/api
DELTA_API_KEY=your-delta-exchange-api-key-here
DELTA_API_SECRET=your-delta-exchange-api-secret-here

# Database
DATABASE_URL=sqlite:///data/mindtrade.db"""
        
        try:
            with open(".env", "w") as f:
                f.write(sample_content)
            print("✅ Sample .env file created")
            print("🔧 Please edit .env and add your actual API keys")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
        
        return False
    else:
        print("✅ .env file found")
        return True

def check_variables():
    """Check environment variables"""
    print("\n🔍 Checking environment variables")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    variables = {
        "GOOGLE_API_KEY": "Google Gemini API Key",
        "SECRET_KEY": "Application Secret Key", 
        "DELTA_API_KEY": "Delta Exchange API Key",
        "DELTA_API_SECRET": "Delta Exchange API Secret"
    }
    
    results = {}
    
    for var, description in variables.items():
        value = os.getenv(var)
        
        if not value:
            print(f"❌ {description}: Not set")
            results[var] = False
        elif value.startswith("your-"):
            print(f"⚠️ {description}: Using placeholder value")
            results[var] = False
        else:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {description}: Set ({masked_value})")
            results[var] = True
    
    return results

def provide_guidance(results):
    """Provide setup guidance based on results"""
    print("\n💡 Setup Guidance")
    print("=" * 50)
    
    if not results.get("GOOGLE_API_KEY"):
        print("\n🤖 Google Gemini API Setup:")
        print("1. Go to: https://makersuite.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Copy the key and replace 'your-google-gemini-api-key-here' in .env")
    
    if not results.get("DELTA_API_KEY") or not results.get("DELTA_API_SECRET"):
        print("\n🔄 Delta Exchange API Setup:")
        print("1. Log in to Delta Exchange: https://www.delta.exchange")
        print("2. Go to Account → API Management")
        print("3. Create a new API key with 'Read' permissions")
        print("4. Copy both the API Key and Secret")
        print("5. Replace the placeholder values in .env:")
        print("   DELTA_API_KEY=your_actual_api_key")
        print("   DELTA_API_SECRET=your_actual_api_secret")
    
    if not results.get("SECRET_KEY"):
        print("\n🔐 Secret Key Setup:")
        print("Replace the placeholder with any random string:")
        print("SECRET_KEY=my-super-secret-random-string-12345")
    
    print("\n🔄 After updating .env:")
    print("1. Save the .env file")
    print("2. Restart the Streamlit application")
    print("3. Run this check script again to verify")

def main():
    """Main configuration checker"""
    print("🧪 Delta Exchange Configuration Checker")
    print("🕐 " + "=" * 48)
    
    # Check .env file exists
    env_exists = check_env_file()
    
    if not env_exists:
        print("\n⚠️ Please edit the .env file and run this script again")
        return
    
    # Check variables
    results = check_variables()
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 50)
    
    total_vars = len(results)
    configured_vars = sum(1 for configured in results.values() if configured)
    
    print(f"Configured: {configured_vars}/{total_vars} variables")
    
    if configured_vars == total_vars:
        print("🎉 All variables configured correctly!")
        print("\n🚀 Ready to use MindTrade AI with full features:")
        print("   ✅ AI Analysis (Gemini)")
        print("   ✅ Delta Exchange Integration") 
        print("   ✅ Secure Application")
    elif results.get("GOOGLE_API_KEY"):
        print("✅ Core AI features available")
        print("⚠️ Delta Exchange integration needs setup")
    else:
        print("⚠️ Please configure your API keys")
    
    # Provide guidance for missing variables
    if configured_vars < total_vars:
        provide_guidance(results)
    
    print("\n🧪 To test Delta Exchange specifically:")
    print("   python test_delta_exchange.py")

if __name__ == "__main__":
    main()
