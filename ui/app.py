"""
MindTrade AI - Advanced Trading Journal
Main Streamlit Application with Enhanced Navigation
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import our modules
from models.database import init_db
from models.dal import TradeDAL, PsychologyDAL, SetupDAL, AnalyticsDAL, get_db_session
from utils.ai_integration import GeminiAI
from utils.analytics import TradingAnalytics

# Page configuration
st.set_page_config(
    page_title="MindTrade AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Initialize components
@st.cache_resource
def get_components():
    return GeminiAI(), TradingAnalytics()

ai_engine, analytics_engine = get_components()

# Custom CSS for enhanced styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.metric-card {
    background: linear-gradient(145deg, #f0f2f6, #ffffff);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #667eea;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin: 0.5rem 0;
}

.trade-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.info-card {
    background: linear-gradient(145deg, #d1ecf1, #ffffff);
    border: 1px solid #bee5eb;
    border-radius: 10px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.status-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 5px;
}

.status-online { background-color: #28a745; }
.status-offline { background-color: #dc3545; }
.status-warning { background-color: #ffc107; }

/* Page navigation styling */
.nav-link {
    color: #495057;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    margin: 0.2rem 0;
    display: block;
    transition: background-color 0.3s;
}

.nav-link:hover {
    background-color: #e9ecef;
    color: #667eea;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 MindTrade AI - Your Trading Partner</h1>
    <p>Advanced AI-powered trading journal with multi-agent analysis, pattern recognition, and personalized coaching.</p>
    <p>🚀 <strong>Complete System:</strong> Analytics Dashboard | AI Coaching | Delta Exchange Integration | Psychology Tracking</p>
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
st.sidebar.title("🧠 MindTrade AI")
st.sidebar.markdown("---")

# Page Navigation
st.sidebar.subheader("📍 Navigation")

# Create navigation buttons that redirect to pages
nav_options = {
    "🏠 Dashboard": "ui/app.py",
    "📊 CSV Import": "pages/06_CSV_Import.py",
    "📝 Add Trade": "pages/01_Add_Trade.py", 
    "🧠 Psychology Journal": "pages/02_Psychology_Journal.py",
    "📊 Analytics Dashboard": "pages/03_Analytics_Dashboard.py",
    "🤖 AI Coaching": "pages/04_AI_Coaching.py",
    "🔄 Delta Exchange": "pages/05_Delta_Exchange.py"
}

# Current page indicator
current_page = "🏠 Dashboard"  # Default for main app

# Display navigation links
for page_name, page_path in nav_options.items():
    if page_name == current_page:
        st.sidebar.markdown(f"**➤ {page_name}**")
    else:
        if st.sidebar.button(page_name, key=f"nav_{page_name}"):
            if page_name != "🏠 Dashboard":
                st.info(f"Navigate to {page_name} using the sidebar menu or click the page file directly")

# Quick Stats in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Quick Stats")

try:
    db = get_db_session()
    trade_dal = TradeDAL(db)
    recent_trades = trade_dal.get_trades(limit=1000)

    if recent_trades:
        total_trades = len(recent_trades)
        total_pnl = sum(trade.pnl for trade in recent_trades if trade.pnl)
        winning_trades = len([t for t in recent_trades if t.pnl and t.pnl > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        st.sidebar.metric("Trades", total_trades)
        st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")
        st.sidebar.metric("Total P&L", f"${total_pnl:.2f}")
    else:
        st.sidebar.info("No trades yet")
    
    db.close()
except Exception as e:
    st.sidebar.error("Stats unavailable")

# Dashboard Content
st.title("📊 Trading Dashboard")

# Get database session and analytics
try:
    db = get_db_session()
    trade_dal = TradeDAL(db)
    analytics_dal = AnalyticsDAL(db)
    
    # Get performance summary
    summary = analytics_dal.get_trading_summary()
    
    if summary['total_trades'] > 0:
        st.subheader("📈 Performance Overview")
        
        # Key metrics in enhanced cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Total Trades</h3>
                <h2>{summary['total_trades']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            win_rate_color = "#28a745" if summary['win_rate'] >= 60 else "#ffc107" if summary['win_rate'] >= 50 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎯 Win Rate</h3>
                <h2 style="color: {win_rate_color}">{summary['win_rate']:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pnl_color = "#28a745" if summary['total_pnl'] >= 0 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 Total P&L</h3>
                <h2 style="color: {pnl_color}">${summary['total_pnl']:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_pnl_color = "#28a745" if summary['avg_pnl_per_trade'] >= 0 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Avg per Trade</h3>
                <h2 style="color: {avg_pnl_color}">${summary['avg_pnl_per_trade']:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 R-Multiple</h3>
                <h2>{summary.get('avg_r_multiple', 0):.2f}R</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent Performance
        st.subheader("📊 Recent Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔥 This Week")
            week_summary = analytics_dal.get_trading_summary(
                start_date=datetime.now() - timedelta(days=7)
            )
            
            st.write(f"**Trades:** {week_summary['total_trades']}")
            st.write(f"**P&L:** ${week_summary['total_pnl']:.2f}")
            st.write(f"**Win Rate:** {week_summary['win_rate']:.1f}%")
        
        with col2:
            st.markdown("### 📅 This Month")
            month_summary = analytics_dal.get_trading_summary(
                start_date=datetime.now() - timedelta(days=30)
            )
            
            st.write(f"**Trades:** {month_summary['total_trades']}")
            st.write(f"**P&L:** ${month_summary['total_pnl']:.2f}")
            st.write(f"**Win Rate:** {month_summary['win_rate']:.1f}%")
        
        # Recent trades with enhanced display
        st.subheader("📋 Recent Trades")
        recent_trades = trade_dal.get_trades(limit=10)
        
        if recent_trades:
            for i, trade in enumerate(recent_trades[:5]):  # Show top 5 with cards
                pnl_emoji = "🟢" if trade.pnl and trade.pnl > 0 else "🔴" if trade.pnl and trade.pnl < 0 else "⚪"
                
                st.markdown(f"""
                <div class="trade-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{pnl_emoji} {trade.symbol} {trade.direction}</strong><br>
                            <small>{trade.entry_time.strftime('%Y-%m-%d %H:%M') if trade.entry_time else 'Unknown'}</small>
                        </div>
                        <div style="text-align: right;">
                            <strong style="color: {'#28a745' if trade.pnl and trade.pnl > 0 else '#dc3545' if trade.pnl and trade.pnl < 0 else '#6c757d'}">${trade.pnl:.2f}</strong><br>
                            <small>{trade.r_multiple:.2f}R</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(recent_trades) > 5:
                with st.expander(f"Show {len(recent_trades) - 5} more trades"):
                    trades_data = []
                    for trade in recent_trades[5:]:
                        trades_data.append({
                            'Symbol': trade.symbol,
                            'Direction': trade.direction,
                            'P&L': f"${trade.pnl:.2f}" if trade.pnl else "$0.00",
                            'R-Multiple': f"{trade.r_multiple:.2f}R" if trade.r_multiple else "0.00R",
                            'Date': trade.entry_time.strftime('%Y-%m-%d') if trade.entry_time else 'Unknown'
                        })
                    
                    trades_df = pd.DataFrame(trades_data)
                    st.dataframe(trades_df, use_container_width=True, hide_index=True)
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Import CSV", type="primary"):
                st.info("Navigate to 'CSV Import' page using the sidebar to import your historical trading data")
        
        with col2:
            if st.button("📝 Add Trade"):
                st.info("Navigate to 'Add Trade' page using the sidebar")
        
        with col3:
            if st.button("📊 View Analytics"):
                st.info("Navigate to 'Analytics Dashboard' page using the sidebar")
        
        with col4:
            if st.button("🤖 AI Coaching"):
                st.info("Navigate to 'AI Coaching' page using the sidebar")
    
    else:
        # Welcome screen for new users
        st.markdown("""
        <div class="info-card">
            <h2>🎉 Welcome to MindTrade AI!</h2>
            <p>Your intelligent trading companion is ready to help you improve your trading performance.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🚀 Getting Started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 1️⃣ Add Your First Trade
            Start by logging your trades to begin tracking performance.
            """)
            if st.button("📝 Add Trade", type="primary"):
                st.info("Navigate to 'Add Trade' page using the sidebar")
        
        with col2:
            st.markdown("""
            ### 2️⃣ Connect Delta Exchange
            Automatically sync trades from your exchange.
            """)
            if st.button("🔄 Setup Delta Exchange"):
                st.info("Navigate to 'Delta Exchange' page using the sidebar")
        
        st.markdown("""
        ### 🎯 What MindTrade AI Can Do:
        
        - **📊 Advanced Analytics**: Comprehensive performance tracking with P&L curves, drawdown analysis, and setup performance
        - **🤖 AI-Powered Insights**: Multi-agent AI system provides personalized coaching and pattern recognition
        - **🧠 Psychology Tracking**: Monitor your emotional state and trading psychology with AI analysis
        - **🔄 Auto-Sync**: Connect to Delta Exchange for automatic trade importing
        - **📈 Visual Analytics**: Beautiful charts and visualizations to understand your performance
        - **🎯 Setup Analysis**: Track which trading setups work best for you
        - **💡 Pattern Recognition**: AI identifies recurring patterns in your trading behavior
        - **📱 Modern Interface**: Clean, intuitive design optimized for traders
        """)
        
        # Feature showcase
        st.subheader("✨ Key Features")
        
        feature_col1, feature_col2, feature_col3 = st.columns(3)
        
        with feature_col1:
            st.markdown("""
            **🤖 AI Coaching**
            - Personal trading coach
            - Pattern recognition
            - Psychology analysis
            - Improvement suggestions
            """)
        
        with feature_col2:
            st.markdown("""
            **📊 Advanced Analytics**
            - P&L curves & drawdown
            - Setup performance tracking
            - Win rate optimization
            - Risk metrics analysis
            """)
        
        with feature_col3:
            st.markdown("""
            **🔄 Auto Integration**
            - Delta Exchange sync
            - Screenshot analysis
            - Multi-timeframe data
            - Real-time updates
            """)
    
    db.close()

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.info("Please check your database configuration and try again.")

# Enhanced Sidebar Status
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 System Status")

# Status indicators with colors
status_items = [
    ("AI Engine", "🟢" if ai_engine.enabled else "🔴"),
    ("Database", "🟢"),
    ("Analytics", "🟢"),
    ("Delta API", "🟡"),  # Will be green when configured
    ("UI", "🟢")
]

for item, status in status_items:
    st.sidebar.markdown(f"{status} {item}")

# System info
st.sidebar.markdown("---")
st.sidebar.markdown("**🧠 MindTrade AI v2.0**")
st.sidebar.markdown("*Your AI-powered trading companion*")

if ai_engine.enabled:
    st.sidebar.success("✅ AI Ready")
else:
    st.sidebar.warning("⚠️ Configure AI")

st.sidebar.caption("Built with ❤️ using Streamlit & Google Gemini")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <strong>MindTrade AI</strong> - Elevating Trading Performance Through Artificial Intelligence<br>
    <small>🚀 Complete analytics • 🤖 AI coaching • 📊 Performance tracking • 🧠 Psychology insights</small>
</div>
""", unsafe_allow_html=True)