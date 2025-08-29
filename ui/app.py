import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Page configuration
st.set_page_config(
    page_title="MindTrade AI - Trading Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("MindTrade AI")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Add Trade", "Trade History", "Analytics", "Psychology", "Settings"]
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Main content
if page == "Dashboard":
    st.markdown('<h1 class="main-header">📈 MindTrade AI Dashboard</h1>', unsafe_allow_html=True)
    
    # API Status
    api_connected = check_api_connection()
    if api_connected:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Not Connected - Please start the API server")
        st.info("Run: docker-compose up api")
        st.stop()
    
    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total P&L",
            value="$0.00",
            delta="0.00%"
        )
    
    with col2:
        st.metric(
            label="Win Rate",
            value="0%",
            delta="0%"
        )
    
    with col3:
        st.metric(
            label="Total Trades",
            value="0",
            delta="0"
        )
    
    with col4:
        st.metric(
            label="Avg R Multiple",
            value="0.00",
            delta="0.00"
        )
    
    # Placeholder charts
    st.subheader("📊 Performance Overview")
    
    # Sample data for demonstration
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    sample_data = pd.DataFrame({
        'date': dates,
        'equity': [10000 + i * 50 + (i % 3) * 100 for i in range(len(dates))],
        'drawdown': [0] * len(dates)
    })
    
    # Equity curve
    fig_equity = px.line(
        sample_data, 
        x='date', 
        y='equity',
        title="Equity Curve",
        labels={'equity': 'Account Value ($)', 'date': 'Date'}
    )
    fig_equity.update_layout(height=400)
    st.plotly_chart(fig_equity, use_container_width=True)

elif page == "Add Trade":
    st.title("➕ Add New Trade")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", placeholder="BTCUSDT")
            direction = st.selectbox("Direction", ["Long", "Short"])
            entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01)
            stop_price = st.number_input("Stop Loss", min_value=0.0, step=0.01)
            exit_price = st.number_input("Exit Price", min_value=0.0, step=0.01)
        
        with col2:
            quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            account_equity = st.number_input("Account Equity", min_value=0.0, step=0.01)
            risk_percent = st.number_input("Risk %", min_value=0.0, max_value=100.0, step=0.1)
            trade_time = st.datetime_input("Trade Time", value=datetime.now())
        
        setup_type = st.selectbox(
            "Setup Type",
            ["Liquidity Trap", "Fake Breakout", "Transition Phase", "Breakout", "Pullback", "Other"]
        )
        
        logic = st.text_area("Trade Logic", placeholder="Describe your trade setup and reasoning...")
        psych_note = st.text_area("Psychology Notes", placeholder="How did you feel? Any emotions or behavioral patterns?")
        
        submitted = st.form_submit_button("Add Trade")
        
        if submitted:
            st.success("Trade added successfully! (Placeholder - API integration pending)")
            st.json({
                "symbol": symbol,
                "direction": direction,
                "entry": entry_price,
                "stop": stop_price,
                "exit": exit_price,
                "quantity": quantity,
                "setup": setup_type,
                "logic": logic,
                "psych_note": psych_note
            })

elif page == "Trade History":
    st.title("📋 Trade History")
    
    # Placeholder table
    sample_trades = pd.DataFrame({
        'Date': ['2024-01-15', '2024-01-14', '2024-01-13'],
        'Symbol': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'Direction': ['Long', 'Short', 'Long'],
        'Entry': [45000, 2800, 95],
        'Exit': [46000, 2750, 98],
        'P&L': [1000, 50, 300],
        'R Multiple': [2.0, 1.0, 1.5],
        'Setup': ['Liquidity Trap', 'Fake Breakout', 'Breakout']
    })
    
    st.dataframe(sample_trades, use_container_width=True)

elif page == "Analytics":
    st.title("📊 Analytics")
    
    # Setup performance
    st.subheader("Setup Performance")
    setup_data = pd.DataFrame({
        'Setup': ['Liquidity Trap', 'Fake Breakout', 'Breakout', 'Pullback'],
        'Win Rate': [75, 60, 80, 65],
        'Avg R': [1.8, 1.2, 2.1, 1.5],
        'Total Trades': [20, 15, 25, 10]
    })
    
    fig_setup = px.bar(
        setup_data,
        x='Setup',
        y='Win Rate',
        title="Win Rate by Setup",
        color='Avg R',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_setup, use_container_width=True)

elif page == "Psychology":
    st.title("🧠 Psychology Analysis")
    
    # Emotion tracking
    st.subheader("Emotional Patterns")
    
    emotions_data = pd.DataFrame({
        'Emotion': ['Confidence', 'Fear', 'Greed', 'Patience', 'FOMO'],
        'Frequency': [15, 8, 12, 20, 5],
        'Impact': [0.8, -0.6, -0.4, 0.9, -0.7]
    })
    
    fig_emotions = px.scatter(
        emotions_data,
        x='Frequency',
        y='Impact',
        size='Frequency',
        color='Emotion',
        title="Emotion Frequency vs Impact on Performance"
    )
    st.plotly_chart(fig_emotions, use_container_width=True)

elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("API Configuration")
    api_url = st.text_input("API Base URL", value=API_BASE_URL)
    
    st.subheader("Delta Exchange Integration")
    delta_enabled = st.checkbox("Enable Delta Exchange Sync", value=True)
    if delta_enabled:
        st.text_input("Delta API Key", type="password")
        st.text_input("Delta API Secret", type="password")
    
    st.subheader("AI Agents")
    ai_enabled = st.checkbox("Enable AI Analysis", value=True)
    if ai_enabled:
        st.selectbox("LLM Provider", ["OpenAI", "Anthropic", "Local"])
        st.text_input("API Key", type="password")
    
    if st.button("Save Settings"):
        st.success("Settings saved! (Placeholder)")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>MindTrade AI v1.0.0 | Built with ❤️ for traders</div>",
    unsafe_allow_html=True
)
