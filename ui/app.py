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
/* Professional Color Scheme */
:root {
    --primary-color: #1e3a8a;
    --secondary-color: #3b82f6;
    --accent-color: #06b6d4;
    --success-color: #059669;
    --warning-color: #d97706;
    --danger-color: #dc2626;
    --light-bg: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
}

/* Main Header */
.main-header {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    padding: 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(30, 58, 138, 0.15);
    text-align: center;
}

.main-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2.5rem;
    font-weight: 700;
}

.main-header p {
    margin: 0;
    font-size: 1.1rem;
    opacity: 0.95;
}

/* Metric Cards */
.metric-card {
    background: var(--card-bg);
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid var(--border-color);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin: 0.5rem 0;
    transition: all 0.3s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
}

.metric-card h3 {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 0.5rem 0;
}

.metric-card h2 {
    color: var(--text-primary);
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}

/* Trade Cards */
.trade-card {
    background: var(--card-bg);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    margin: 0.75rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.trade-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Info Cards */
.info-card {
    background: linear-gradient(135deg, #f0f9ff 0%, var(--card-bg) 100%);
    border: 1px solid #bae6fd;
    border-radius: 16px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Status Indicators */
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-online { background-color: var(--success-color); }
.status-offline { background-color: var(--danger-color); }
.status-warning { background-color: var(--warning-color); }

/* Navigation Styling */
.nav-link {
    color: var(--text-primary);
    text-decoration: none;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin: 0.25rem 0;
    display: block;
    transition: all 0.3s ease;
    font-weight: 500;
}

.nav-link:hover {
    background-color: var(--light-bg);
    color: var(--primary-color);
    transform: translateX(4px);
}

/* Section Headers */
.section-header {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border-color);
}

/* Performance Grid */
.performance-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 1.5rem 0;
}

/* Success/Error Messages */
.success-message {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border: 1px solid #a7f3d0;
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: var(--success-color);
}

.error-message {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border: 1px solid #fca5a5;
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: var(--danger-color);
}

/* Responsive Design */
@media (max-width: 768px) {
    .metric-card {
        padding: 1.5rem;
    }
    
    .metric-card h2 {
        font-size: 1.5rem;
    }
    
    .main-header {
        padding: 2rem;
    }
    
    .main-header h1 {
        font-size: 2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 MindTrade AI</h1>
    <p>Advanced AI-powered trading journal with multi-agent analysis, pattern recognition, and personalized coaching</p>
    <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 1rem;">
        <strong>Complete System:</strong> Analytics Dashboard • AI Coaching • Delta Exchange Integration • Psychology Tracking
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h2 style="color: #1e3a8a; margin: 0;">🧠 MindTrade AI</h2>
    <p style="color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;">Your AI Trading Partner</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Page Navigation
st.sidebar.markdown('<h3 style="color: #1e3a8a; font-size: 1rem;">📍 Navigation</h3>', unsafe_allow_html=True)

# Create navigation buttons that redirect to pages
nav_options = {
    "🏠 Dashboard": "ui/app.py",
    "📊 CSV Import": "pages/06_CSV_Import.py",
    "📈 Historical Analysis": "pages/07_Historical_Analysis.py",
    "🧠 Psychology Import": "pages/08_Psychology_Import.py",
    "🔧 Trade Enhancer": "pages/09_Trade_Enhancer.py",
    "🔄 Dynamic CSV Import": "pages/10_Dynamic_CSV_Import.py",
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
st.sidebar.markdown('<h3 style="color: #1e3a8a; font-size: 1rem;">📊 Quick Stats</h3>', unsafe_allow_html=True)

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
        st.markdown('<h2 class="section-header">📈 Performance Overview</h2>', unsafe_allow_html=True)
        
        # Key metrics in enhanced cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Total Trades</h3>
                <h2>{summary['total_trades']:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            win_rate_color = "#059669" if summary['win_rate'] >= 60 else "#d97706" if summary['win_rate'] >= 50 else "#dc2626"
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎯 Win Rate</h3>
                <h2 style="color: {win_rate_color}">{summary['win_rate']:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pnl_color = "#059669" if summary['total_pnl'] >= 0 else "#dc2626"
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 Total P&L</h3>
                <h2 style="color: {pnl_color}">${summary['total_pnl']:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_pnl_color = "#059669" if summary['avg_pnl_per_trade'] >= 0 else "#dc2626"
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Avg per Trade</h3>
                <h2 style="color: {avg_pnl_color}">${summary['avg_pnl_per_trade']:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            r_color = "#059669" if summary.get('avg_r_multiple', 0) > 0 else "#dc2626"
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 R-Multiple</h3>
                <h2 style="color: {r_color}">{summary.get('avg_r_multiple', 0):.2f}R</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent Performance
        st.markdown('<h2 class="section-header">📊 Recent Performance</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🔥 This Week</h3>
            """, unsafe_allow_html=True)
            week_summary = analytics_dal.get_trading_summary(
                start_date=datetime.now() - timedelta(days=7)
            )
            
            st.metric("Trades", week_summary['total_trades'])
            st.metric("P&L", f"${week_summary['total_pnl']:,.2f}")
            st.metric("Win Rate", f"{week_summary['win_rate']:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>📅 This Month</h3>
            """, unsafe_allow_html=True)
            month_summary = analytics_dal.get_trading_summary(
                start_date=datetime.now() - timedelta(days=30)
            )
            
            st.metric("Trades", month_summary['total_trades'])
            st.metric("P&L", f"${month_summary['total_pnl']:,.2f}")
            st.metric("Win Rate", f"{month_summary['win_rate']:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Recent trades with enhanced display
        st.markdown('<h2 class="section-header">📋 Recent Trades</h2>', unsafe_allow_html=True)
        recent_trades = trade_dal.get_trades(limit=10)
        
        if recent_trades:
            for i, trade in enumerate(recent_trades[:5]):  # Show top 5 with cards
                pnl_emoji = "🟢" if trade.pnl and trade.pnl > 0 else "🔴" if trade.pnl and trade.pnl < 0 else "⚪"
                pnl_color = "#059669" if trade.pnl and trade.pnl > 0 else "#dc2626" if trade.pnl and trade.pnl < 0 else "#64748b"
                
                st.markdown(f"""
                <div class="trade-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: 1.1rem;">{pnl_emoji} {trade.symbol} {trade.direction}</strong><br>
                            <small style="color: #64748b;">{trade.entry_time.strftime('%Y-%m-%d %H:%M') if trade.entry_time else 'Unknown'}</small>
                        </div>
                        <div style="text-align: right;">
                            <strong style="color: {pnl_color}; font-size: 1.2rem;">${trade.pnl:,.2f}</strong><br>
                            <small style="color: #64748b;">{trade.r_multiple:.2f}R</small>
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
        st.markdown('<h2 class="section-header">⚡ Quick Actions</h2>', unsafe_allow_html=True)
        
        # Create a grid of action buttons
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📊 Import CSV", type="primary", use_container_width=True):
                st.info("Navigate to 'CSV Import' page using the sidebar to import your historical trading data")
        
        with col2:
            if st.button("📝 Add Trade", use_container_width=True):
                st.info("Navigate to 'Add Trade' page using the sidebar")
        
        with col3:
            if st.button("📈 Historical Analysis", use_container_width=True):
                st.info("Navigate to 'Historical Analysis' page using the sidebar")
        
        with col4:
            if st.button("📊 View Analytics", use_container_width=True):
                st.info("Navigate to 'Analytics Dashboard' page using the sidebar")
        
        with col5:
            if st.button("🤖 AI Coaching", use_container_width=True):
                st.info("Navigate to 'AI Coaching' page using the sidebar")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        # Welcome screen for new users
        st.markdown("""
        <div class="info-card">
            <h2 style="color: #1e3a8a; margin-bottom: 1rem;">🎉 Welcome to MindTrade AI!</h2>
            <p style="font-size: 1.1rem; color: #374151;">Your intelligent trading companion is ready to help you improve your trading performance.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<h2 class="section-header">🚀 Getting Started</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>1️⃣ Add Your First Trade</h3>
                <p style="color: #64748b; margin: 1rem 0;">Start by logging your trades to begin tracking performance.</p>
            """, unsafe_allow_html=True)
            if st.button("📝 Add Trade", type="primary", use_container_width=True):
                st.info("Navigate to 'Add Trade' page using the sidebar")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>2️⃣ Connect Delta Exchange</h3>
                <p style="color: #64748b; margin: 1rem 0;">Automatically sync trades from your exchange.</p>
            """, unsafe_allow_html=True)
            if st.button("🔄 Setup Delta Exchange", use_container_width=True):
                st.info("Navigate to 'Delta Exchange' page using the sidebar")
            st.markdown("</div>", unsafe_allow_html=True)
        
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
    st.markdown(f"""
    <div class="error-message">
        <strong>⚠️ Error loading dashboard data:</strong> {str(e)}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="success-message">
        <strong>💡 Tip:</strong> Please check your database configuration and try again.
    </div>
    """, unsafe_allow_html=True)

# Enhanced Sidebar Status
st.sidebar.markdown("---")
st.sidebar.markdown('<h3 style="color: #1e3a8a; font-size: 1rem;">🔌 System Status</h3>', unsafe_allow_html=True)

# Status indicators with colors
status_items = [
    ("AI Engine", "🟢" if ai_engine.enabled else "🔴"),
    ("Database", "🟢"),
    ("Analytics", "🟢"),
    ("Delta API", "🟡"),  # Will be green when configured
    ("UI", "🟢")
]

for item, status in status_items:
    st.sidebar.markdown(f"<div style='padding: 0.25rem 0;'>{status} {item}</div>", unsafe_allow_html=True)

# System info
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <p style="color: #1e3a8a; font-weight: 600; margin: 0;">🧠 MindTrade AI v2.0</p>
    <p style="color: #64748b; font-size: 0.8rem; margin: 0.5rem 0;">Your AI-powered trading companion</p>
</div>
""", unsafe_allow_html=True)

if ai_engine.enabled:
    st.sidebar.markdown("""
    <div class="success-message" style="margin: 0.5rem 0;">
        ✅ AI Ready
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div class="error-message" style="margin: 0.5rem 0;">
        ⚠️ Configure AI
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 1rem 0;">
    Built with ❤️ using Streamlit & Google Gemini
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-radius: 12px; margin-top: 2rem;'>
    <strong style="color: #1e3a8a; font-size: 1.1rem;">MindTrade AI</strong> - Elevating Trading Performance Through Artificial Intelligence<br>
    <small style="color: #64748b; margin-top: 0.5rem; display: block;">🚀 Complete analytics • 🤖 AI coaching • 📊 Performance tracking • 🧠 Psychology insights</small>
</div>
""", unsafe_allow_html=True)