#!/usr/bin/env python3
"""
Quick test after IP whitelisting fix
"""

import asyncio
from fetch_personal_trades import DeltaPersonalTradesFetcher

async def quick_test():
    """Quick authentication test"""
    print("🧪 Quick Test After IP Fix")
    print("=" * 40)
    
    fetcher = DeltaPersonalTradesFetcher()
    
    if not fetcher.enabled:
        print("❌ API keys not configured")
        return
    
    # Test authentication only
    auth_success = await fetcher.test_authentication()
    
    if auth_success:
        print("\n🎉 SUCCESS! Authentication is now working!")
        print("✅ Ready to fetch your personal trades")
        
        # Ask if user wants to fetch trades now
        print("\n🚀 Fetching your trading history...")
        await fetcher.comprehensive_personal_data_fetch()
    else:
        print("\n❌ Still having authentication issues")
        print("💡 Try Option 2: Remove IP restriction completely")

if __name__ == "__main__":
    asyncio.run(quick_test())
