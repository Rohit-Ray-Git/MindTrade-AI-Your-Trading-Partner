"""
Add Trade Page
Manual trade entry with AI analysis
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from models.database import init_db
from models.dal import TradeDAL, SetupDAL, get_db_session
from utils.ai_integration import GeminiAI

# Page config
st.set_page_config(
    page_title="Add Trade",
    page_icon="📝",
    layout="wide"
)

# Initialize
init_db()
ai_engine = GeminiAI()

st.title("📝 Add New Trade")

# Get setups for dropdown
db = get_db_session()
setup_dal = SetupDAL(db)
setups = setup_dal.get_all_setups()
setup_options = {setup.name: setup.id for setup in setups}

with st.form("add_trade_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.text_input("Symbol", placeholder="BTCUSDT")
        direction = st.selectbox("Direction", ["LONG", "SHORT"])
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.4f")
        exit_price = st.number_input("Exit Price", min_value=0.0, format="%.4f")
        quantity = st.number_input("Quantity", min_value=0.0, format="%.6f")
    
    with col2:
        stop_price = st.number_input("Stop Loss", min_value=0.0, format="%.4f")
        target_price = st.number_input("Target Price", min_value=0.0, format="%.4f")
        fees = st.number_input("Fees", min_value=0.0, format="%.2f")
        setup_name = st.selectbox("Setup", ["None"] + list(setup_options.keys()))
        
    entry_time = st.datetime_input("Entry Time", value=datetime.now())
    exit_time = st.datetime_input("Exit Time", value=datetime.now())
    
    logic = st.text_area("Trade Logic", placeholder="Describe your reasoning for this trade...")
    
    # Image upload
    uploaded_image = st.file_uploader(
        "Upload chart screenshot (optional)", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a screenshot of your trade setup"
    )
    
    submitted = st.form_submit_button("💾 Add Trade", type="primary")
    
    if submitted:
        if symbol and direction and entry_price and exit_price and quantity:
            trade_dal = TradeDAL(db)
            
            trade_data = {
                'symbol': symbol.upper(),
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'stop_price': stop_price if stop_price > 0 else None,
                'target_price': target_price if target_price > 0 else None,
                'fees': fees,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'logic': logic,
                'setup_id': setup_options.get(setup_name) if setup_name != "None" else None
            }
            
            try:
                trade = trade_dal.create_trade(trade_data)
                st.success(f"✅ Trade added successfully! P&L: ${trade.pnl:.2f}")
                
                # Save image if uploaded
                if uploaded_image and ai_engine.enabled:
                    image_bytes = uploaded_image.read()
                    image_path = ai_engine.save_image(image_bytes, trade.id, "trade_screenshot")
                    st.info(f"📸 Screenshot saved: {image_path}")
                
                # AI Analysis
                if ai_engine.enabled:
                    with st.spinner("🤖 AI is analyzing your trade..."):
                        analysis = ai_engine.analyze_trade_with_image(trade_data)
                        
                        if analysis:
                            st.subheader("🤖 AI Trade Analysis")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Trade Quality", f"{analysis.get('trade_quality_score', 0):.1f}/1.0")
                            with col2:
                                st.metric("Risk Management", f"{analysis.get('risk_management_score', 0):.1f}/1.0")
                            with col3:
                                st.metric("Execution", f"{analysis.get('execution_score', 0):.1f}/1.0")
                            
                            if 'improvement_suggestions' in analysis:
                                st.subheader("💡 AI Suggestions")
                                for suggestion in analysis['improvement_suggestions']:
                                    st.write(f"• {suggestion}")
            
            except Exception as e:
                st.error(f"Error adding trade: {e}")
        else:
            st.error("Please fill in all required fields (Symbol, Direction, Entry Price, Exit Price, Quantity)")

db.close()
