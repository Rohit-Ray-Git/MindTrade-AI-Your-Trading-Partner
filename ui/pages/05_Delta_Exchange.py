"""
Delta Exchange Integration
Sync trades automatically from Delta Exchange API
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from utils.delta_exchange import DeltaExchangeAPI, DeltaExchangeSync
from models.dal import TradeDAL, get_db_session
from models.models import Trade

# Page config
st.set_page_config(
    page_title="Delta Exchange",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Delta Exchange Integration")
st.markdown("Automatically sync your trades from Delta Exchange to your trading journal.")

# Initialize Delta Exchange components
@st.cache_resource
def get_delta_components():
    return DeltaExchangeAPI(), DeltaExchangeSync()

delta_api, delta_sync = get_delta_components()

# Status indicators
col1, col2, col3 = st.columns(3)

with col1:
    if delta_api.enabled:
        st.success("✅ API Configured")
    else:
        st.error("❌ API Not Configured")

with col2:
    sync_status = delta_sync.get_sync_status()
    if sync_status['last_sync']:
        last_sync = datetime.fromisoformat(sync_status['last_sync'])
        st.info(f"🕒 Last Sync: {last_sync.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.warning("⏳ Never Synced")

with col3:
    if delta_api.enabled:
        st.info("🔗 Ready to Sync")
    else:
        st.warning("⚠️ Setup Required")

# Configuration Section
if not delta_api.enabled:
    st.header("⚙️ Setup Configuration")
    
    st.markdown("""
    ### 🔑 API Setup Instructions
    
    1. **Log in to Delta Exchange**
       - Go to [Delta Exchange](https://www.delta.exchange)
       - Sign in to your account
    
    2. **Generate API Keys**
       - Navigate to **Account** → **API Management**
       - Click **"Create New API Key"**
       - Set permissions: **Read** (for trade history)
       - Copy your **API Key** and **API Secret**
    
    3. **Configure Environment**
       - Create or edit your `.env` file in the project root:
         ```
         DELTA_API_KEY=your_actual_api_key_here
         DELTA_API_SECRET=your_actual_api_secret_here
         ```
       - **Important:** Replace the placeholder text with your real API credentials
       - Restart the Streamlit application
    
    4. **Test Connection**
       - Return to this page and test the connection
    """)
    
    st.warning("⚠️ **Important:** Keep your API keys secure and never share them publicly.")
    
    # Show current environment status
    import os
    api_key_set = bool(os.getenv("DELTA_API_KEY")) and not os.getenv("DELTA_API_KEY", "").startswith("your-")
    api_secret_set = bool(os.getenv("DELTA_API_SECRET")) and not os.getenv("DELTA_API_SECRET", "").startswith("your-")
    
    st.subheader("🔍 Current Configuration Status")
    st.write(f"**API Key:** {'✅ Set' if api_key_set else '❌ Not set or using placeholder'}")
    st.write(f"**API Secret:** {'✅ Set' if api_secret_set else '❌ Not set or using placeholder'}")
    
    if not api_key_set or not api_secret_set:
        st.error("Please update your `.env` file with real API credentials and restart the application.")

else:
    # API Connection Test
    st.header("🔍 Connection Test")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🧪 Test API Connection", type="primary"):
            with st.spinner("Testing connection..."):
                # Run async function
                async def test_connection():
                    return await delta_api.test_connection()
                
                try:
                    result = asyncio.run(test_connection())
                    st.session_state.connection_test = result
                except Exception as e:
                    st.session_state.connection_test = {
                        "success": False,
                        "error": str(e)
                    }
    
    with col2:
        if hasattr(st.session_state, 'connection_test'):
            result = st.session_state.connection_test
            if result['success']:
                st.success(f"✅ Connection successful!")
                if 'account_id' in result:
                    st.info(f"Account ID: {result['account_id']}")
                if 'email' in result:
                    st.info(f"Email: {result['email']}")
            else:
                st.error(f"❌ Connection failed: {result['error']}")
    
    # Trade Synchronization
    st.header("🔄 Trade Synchronization")
    
    # Sync options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚡ Quick Sync")
        st.markdown("Sync recent trades from the last 24 hours")
        
        if st.button("🚀 Quick Sync (24h)", type="primary"):
            with st.spinner("Syncing recent trades..."):
                async def quick_sync():
                    return await delta_sync.auto_sync(hours_back=24)
                
                try:
                    result = asyncio.run(quick_sync())
                    st.session_state.sync_result = result
                except Exception as e:
                    st.session_state.sync_result = {
                        "success": False,
                        "error": str(e),
                        "imported_count": 0,
                        "skipped_count": 0
                    }
    
    with col2:
        st.subheader("📅 Custom Sync")
        
        # Date range selection
        col2a, col2b = st.columns(2)
        with col2a:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
        with col2b:
            end_date = st.date_input("End Date", value=datetime.now())
        
        if st.button("🔄 Custom Sync"):
            with st.spinner(f"Syncing trades from {start_date} to {end_date}..."):
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                async def custom_sync():
                    return await delta_api.sync_trades(start_datetime, end_datetime)
                
                try:
                    result = asyncio.run(custom_sync())
                    st.session_state.sync_result = result
                except Exception as e:
                    st.session_state.sync_result = {
                        "success": False,
                        "error": str(e),
                        "imported_count": 0,
                        "skipped_count": 0
                    }
    
    # Display sync results
    if hasattr(st.session_state, 'sync_result'):
        result = st.session_state.sync_result
        
        st.subheader("📊 Sync Results")
        
        if result['success']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("✅ Imported", result['imported_count'])
            with col2:
                st.metric("⏭️ Skipped", result['skipped_count'])
            with col3:
                st.metric("📊 Total Fills", result.get('total_fills', 0))
            with col4:
                st.metric("🔄 Total Trades", result.get('total_trades', 0))
            
            if result['imported_count'] > 0:
                st.success(f"🎉 Successfully imported {result['imported_count']} new trades!")
            elif result['skipped_count'] > 0:
                st.info(f"ℹ️ {result['skipped_count']} trades were already in the database.")
            else:
                st.info("No new trades found for the selected period.")
            
            # Show any errors
            if 'errors' in result and result['errors']:
                with st.expander("⚠️ Import Errors", expanded=False):
                    for error in result['errors']:
                        st.warning(error)
        
        else:
            st.error(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
    
    # Historical Sync
    st.subheader("🗂️ Historical Data Sync")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_back = st.selectbox("Sync Period", [7, 30, 90, 180, 365], index=2)
        st.info(f"This will sync the last {days_back} days of trading data.")
    
    with col2:
        if st.button("📈 Full Historical Sync", type="secondary"):
            with st.spinner(f"Syncing last {days_back} days of trades..."):
                async def historical_sync():
                    return await delta_sync.full_sync(days_back=days_back)
                
                try:
                    result = asyncio.run(historical_sync())
                    st.session_state.sync_result = result
                except Exception as e:
                    st.session_state.sync_result = {
                        "success": False,
                        "error": str(e),
                        "imported_count": 0,
                        "skipped_count": 0
                    }
    
    # Recent Trades from Database
    st.header("📋 Recent Synced Trades")
    
    # Get recent trades that were imported from Delta Exchange
    db = get_db_session()
    
    try:
        # Get trades with Delta Exchange source
        recent_trades = db.query(
            Trade.id,
            Trade.symbol,
            Trade.direction,
            Trade.pnl,
            Trade.entry_time,
            Trade.exchange,
            Trade.external_id
        ).filter(
            Trade.exchange == "Delta Exchange"
        ).order_by(
            Trade.entry_time.desc()
        ).limit(20).all()
        
        if recent_trades:
            trades_data = []
            for trade in recent_trades:
                trades_data.append({
                    'ID': trade.id,
                    'Symbol': trade.symbol,
                    'Direction': trade.direction,
                    'P&L': f"${trade.pnl:.2f}" if trade.pnl else "$0.00",
                    'Entry Time': trade.entry_time.strftime('%Y-%m-%d %H:%M') if trade.entry_time else 'Unknown',
                    'Exchange': trade.exchange,
                    'External ID': trade.external_id or 'N/A'
                })
            
            trades_df = pd.DataFrame(trades_data)
            st.dataframe(trades_df, use_container_width=True, hide_index=True)
            
            # Summary stats
            total_delta_trades = len(trades_data)
            total_pnl = sum([float(t['P&L'].replace('$', '')) for t in trades_data])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Delta Trades", total_delta_trades)
            with col2:
                st.metric("Total P&L", f"${total_pnl:.2f}")
        
        else:
            st.info("No trades synced from Delta Exchange yet. Use the sync options above to import your trades.")
    
    except Exception as e:
        st.error(f"Error loading trades: {e}")
    
    finally:
        db.close()
    
    # Auto-sync settings
    st.header("⚙️ Auto-Sync Settings")
    
    st.markdown("""
    **🔄 Automatic Synchronization**
    
    Configure automatic trade synchronization to keep your journal up-to-date:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_sync_enabled = st.checkbox("Enable Auto-Sync", value=False)
        if auto_sync_enabled:
            sync_interval = st.selectbox("Sync Frequency", ["Every hour", "Every 4 hours", "Daily"], index=2)
            st.success("✅ Auto-sync will run in the background")
        else:
            st.info("ℹ️ Manual sync only")
    
    with col2:
        if auto_sync_enabled:
            st.info(f"**Next sync:** {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')}")
            st.info(f"**Frequency:** {sync_interval}")
            
            # Note: In a production environment, you'd implement this with a background task scheduler
            st.warning("⚠️ Auto-sync requires background task scheduler (coming soon)")

# Export/Import functionality
st.header("📤 Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Export Data")
    if st.button("📥 Export Delta Trades"):
        # Export Delta Exchange trades to CSV
        db = get_db_session()
        try:
            delta_trades = db.query(Trade).filter(
                Trade.exchange == "Delta Exchange"
            ).all()
            
            if delta_trades:
                export_data = []
                for trade in delta_trades:
                    export_data.append({
                        'Symbol': trade.symbol,
                        'Direction': trade.direction,
                        'Entry Price': trade.entry_price,
                        'Exit Price': trade.exit_price,
                        'Quantity': trade.quantity,
                        'P&L': trade.pnl,
                        'Fees': trade.fees,
                        'Entry Time': trade.entry_time,
                        'Exit Time': trade.exit_time,
                        'External ID': trade.external_id
                    })
                
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"delta_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No Delta Exchange trades to export")
        finally:
            db.close()

with col2:
    st.subheader("🔄 Sync Status")
    sync_status = delta_sync.get_sync_status()
    
    st.write(f"**API Enabled:** {'✅' if sync_status['api_enabled'] else '❌'}")
    st.write(f"**Credentials:** {'✅' if sync_status['credentials_configured'] else '❌'}")
    
    if sync_status['last_sync']:
        last_sync_dt = datetime.fromisoformat(sync_status['last_sync'])
        time_since = datetime.now() - last_sync_dt
        st.write(f"**Last Sync:** {time_since.days} days ago")
    else:
        st.write("**Last Sync:** Never")

with col3:
    st.subheader("🔧 Troubleshooting")
    
    with st.expander("Common Issues"):
        st.markdown("""
        **🔍 Connection Issues:**
        - Check API keys in .env file
        - Verify internet connection
        - Ensure API permissions are correct
        
        **🔄 Sync Issues:**
        - Check date ranges
        - Verify you have trades in the period
        - Look for error messages
        
        **📊 Missing Trades:**
        - Some fills might be grouped differently
        - Check for partial fills
        - Verify trade completion on Delta Exchange
        """)

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Run sync regularly to keep your journal up-to-date. Enable auto-sync for hands-free operation.")
