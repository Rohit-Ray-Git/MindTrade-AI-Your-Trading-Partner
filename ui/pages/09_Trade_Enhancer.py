"""
Trade Enhancer Page
Manually enhance imported trades with detailed logic, psychology, and images
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
from models.dal import TradeDAL, PsychologyDAL, SetupDAL, get_db_session
from utils.ai_integration import GeminiAI

# Page config
st.set_page_config(
    page_title="Trade Enhancer",
    page_icon="🔧",
    layout="wide"
)

# Initialize
init_db()
ai_engine = GeminiAI()

st.title("🔧 Trade Enhancer")

st.markdown("""
### 📝 Enhance Your Imported Trades

This page allows you to manually enhance your imported trades with:
- **Detailed trading logic and reasoning**
- **Psychology notes and emotional context**
- **Chart screenshots and visual analysis**
- **Proper trading setups and classifications**
- **Risk management notes**
""")

# Get database session
db = get_db_session()
trade_dal = TradeDAL(db)
psych_dal = PsychologyDAL(db)
setup_dal = SetupDAL(db)

# Get all trades
trades = trade_dal.get_trades(limit=1000)

if not trades:
    st.warning("⚠️ No trades found in database. Please import your CSV data first!")
    st.info("Go to '📊 CSV Import' page to upload your trading data.")
else:
    st.success(f"📊 Found {len(trades)} trades in database")
    
    # Filter options
    st.subheader("🔍 Filter Trades")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_filter = st.selectbox(
            "Filter by Source",
            ["All"] + list(set([trade.source for trade in trades if trade.source]))
        )
    
    with col2:
        symbol_filter = st.selectbox(
            "Filter by Symbol",
            ["All"] + list(set([trade.symbol for trade in trades if trade.symbol]))
        )
    
    with col3:
        enhanced_filter = st.selectbox(
            "Filter by Enhancement Status",
            ["All", "Enhanced", "Not Enhanced"]
        )
    
    # Apply filters
    filtered_trades = trades
    if source_filter != "All":
        filtered_trades = [t for t in filtered_trades if t.source == source_filter]
    if symbol_filter != "All":
        filtered_trades = [t for t in filtered_trades if t.symbol == symbol_filter]
    if enhanced_filter == "Enhanced":
        filtered_trades = [t for t in filtered_trades if t.logic and len(t.logic) > 50]
    elif enhanced_filter == "Not Enhanced":
        filtered_trades = [t for t in filtered_trades if not t.logic or len(t.logic) <= 50]
    
    st.info(f"📋 Showing {len(filtered_trades)} trades")
    
    # Trade selection
    if filtered_trades:
        st.subheader("📝 Select Trade to Enhance")
        
        # Create a simple trade selector
        trade_options = []
        for trade in filtered_trades:
            logic_status = "✅" if trade.logic and len(trade.logic) > 50 else "❌"
            pnl_color = "🟢" if trade.pnl and trade.pnl > 0 else "🔴" if trade.pnl and trade.pnl < 0 else "⚪"
            option_text = f"{logic_status} {pnl_color} {trade.symbol} {trade.direction} - {trade.trade_time.strftime('%Y-%m-%d %H:%M')} (P&L: ${trade.pnl:.2f})"
            trade_options.append((option_text, trade.id))
        
        selected_trade_text = st.selectbox(
            "Choose a trade to enhance:",
            [opt[0] for opt in trade_options],
            index=0
        )
        
        selected_trade_id = trade_options[trade_options.index((selected_trade_text, None))][1] if selected_trade_text else None
        
        if selected_trade_id:
            selected_trade = next((t for t in filtered_trades if t.id == selected_trade_id), None)
            
            if selected_trade:
                st.markdown("---")
                st.subheader(f"🔧 Enhancing Trade: {selected_trade.symbol} {selected_trade.direction}")
                
                # Trade details display
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Trade Details:**")
                    st.write(f"**Symbol:** {selected_trade.symbol}")
                    st.write(f"**Direction:** {selected_trade.direction}")
                    st.write(f"**Entry Price:** ${selected_trade.entry_price:.4f}")
                    st.write(f"**Exit Price:** ${selected_trade.exit_price:.4f}")
                    st.write(f"**Quantity:** {selected_trade.quantity}")
                    st.write(f"**P&L:** ${selected_trade.pnl:.2f}")
                    st.write(f"**R-Multiple:** {selected_trade.r_multiple:.2f}")
                
                with col2:
                    st.markdown("**📅 Trade Information:**")
                    st.write(f"**Entry Time:** {selected_trade.entry_time.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Exit Time:** {selected_trade.exit_time.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Source:** {selected_trade.source}")
                    st.write(f"**Fees:** ${selected_trade.fees:.2f}")
                    st.write(f"**Stop Price:** ${selected_trade.stop_price:.4f}" if selected_trade.stop_price else "**Stop Price:** Not set")
                
                # Enhancement form
                st.markdown("---")
                st.subheader("✍️ Add Trading Details")
                
                with st.form(f"enhance_trade_{selected_trade.id}"):
                    # Get available setups
                    setups = setup_dal.get_setups()
                    setup_options = {setup.name: setup.id for setup in setups}
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Trading logic
                        current_logic = selected_trade.logic or ""
                        enhanced_logic = st.text_area(
                            "📝 Trading Logic & Reasoning",
                            value=current_logic,
                            placeholder="Describe your trading logic, entry reasoning, market analysis, setup identification, and exit strategy...",
                            height=150
                        )
                        
                        # Risk management
                        risk_notes = st.text_area(
                            "🛡️ Risk Management Notes",
                            placeholder="Describe your risk management approach, position sizing, stop loss reasoning, and risk/reward analysis...",
                            height=100
                        )
                    
                    with col2:
                        # Setup selection
                        current_setup = selected_trade.setup_id
                        current_setup_name = "None"
                        if current_setup:
                            current_setup_obj = setup_dal.get_setup(current_setup)
                            if current_setup_obj:
                                current_setup_name = current_setup_obj.name
                        
                        selected_setup = st.selectbox(
                            "📋 Trading Setup",
                            ["None"] + list(setup_options.keys()),
                            index=["None"] + list(setup_options.keys()).index(current_setup_name)
                        )
                        
                        # Market context
                        market_context = st.text_area(
                            "🌍 Market Context",
                            placeholder="Describe the overall market conditions, volatility, news events, or other contextual factors...",
                            height=100
                        )
                    
                    # Chart screenshot upload
                    st.markdown("**📸 Chart Screenshot:**")
                    uploaded_image = st.file_uploader(
                        "Upload chart screenshot for this trade",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"image_{selected_trade.id}",
                        help="Upload a screenshot of the chart setup, entry/exit points, or technical analysis"
                    )
                    
                    # Psychology notes
                    st.markdown("**🧠 Psychology Notes:**")
                    psychology_notes = st.text_area(
                        "Psychology & Emotional Context",
                        placeholder="Describe your emotional state, confidence level, mindset, and psychological factors during this trade...",
                        height=100
                    )
                    
                    # Tags
                    tags = st.text_input(
                        "🏷️ Tags (comma-separated)",
                        placeholder="breakout, trend-following, patient, confident, etc."
                    )
                    
                    # Submit button
                    submitted = st.form_submit_button("💾 Save Enhanced Trade", type="primary")
                    
                    if submitted:
                        try:
                            # Update trade with enhanced information
                            update_data = {
                                'logic': enhanced_logic,
                                'notes': f"{risk_notes}\n\nMarket Context: {market_context}\n\nPsychology: {psychology_notes}\n\nTags: {tags}",
                                'setup_id': setup_options.get(selected_setup) if selected_setup != "None" else None
                            }
                            
                            # Update the trade
                            updated_trade = trade_dal.update_trade(selected_trade.id, update_data)
                            
                            if updated_trade:
                                st.success("✅ Trade enhanced successfully!")
                                
                                # Save image if uploaded
                                if uploaded_image and ai_engine.enabled:
                                    image_bytes = uploaded_image.read()
                                    image_path = ai_engine.save_image(image_bytes, selected_trade.id, "trade_chart")
                                    st.info(f"📸 Chart screenshot saved: {image_path}")
                                
                                # Create psychology note if provided
                                if psychology_notes:
                                    try:
                                        # Parse tags
                                        tag_list = [tag.strip().lower() for tag in tags.split(',')] if tags else []
                                        
                                        # Create psychology note
                                        psych_data = {
                                            'trade_id': selected_trade.id,
                                            'note_text': psychology_notes,
                                            'confidence_score': 0.7,  # Default, can be enhanced
                                            'self_tags': tag_list,
                                            'created_at': selected_trade.trade_time
                                        }
                                        
                                        psych_dal.create_psychology_note(psych_data)
                                        st.success("✅ Psychology note added!")
                                        
                                    except Exception as e:
                                        st.warning(f"⚠️ Could not add psychology note: {str(e)}")
                                
                                # AI Analysis
                                if ai_engine.enabled and enhanced_logic:
                                    st.subheader("🤖 AI Analysis")
                                    with st.spinner("Analyzing enhanced trade..."):
                                        analysis_text = f"Trade Logic: {enhanced_logic}\nPsychology: {psychology_notes}\nRisk Management: {risk_notes}"
                                        
                                        analysis = ai_engine.analyze_trade_with_image(analysis_text)
                                        
                                        if analysis:
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Trade Quality", f"{analysis.get('trade_quality_score', 0):.1f}/1.0")
                                            with col2:
                                                st.metric("Risk Management", f"{analysis.get('risk_management_score', 0):.1f}/1.0")
                                            with col3:
                                                st.metric("Psychology Score", f"{analysis.get('execution_score', 0):.1f}/1.0")
                                            
                                            if 'improvement_suggestions' in analysis:
                                                st.subheader("💡 AI Suggestions")
                                                for suggestion in analysis['improvement_suggestions']:
                                                    st.write(f"• {suggestion}")
                            
                        except Exception as e:
                            st.error(f"❌ Error enhancing trade: {str(e)}")
                
                # Show current trade details
                st.markdown("---")
                st.subheader("📋 Current Trade Details")
                
                if selected_trade.logic:
                    with st.expander("📝 Current Trading Logic"):
                        st.write(selected_trade.logic)
                
                if selected_trade.notes:
                    with st.expander("📋 Current Notes"):
                        st.write(selected_trade.notes)
                
                # Show related psychology notes
                psych_notes = psych_dal.get_psychology_notes(selected_trade.id)
                if psych_notes:
                    with st.expander("🧠 Psychology Notes"):
                        for note in psych_notes:
                            st.write(f"**{note.created_at.strftime('%Y-%m-%d %H:%M')}:** {note.note_text}")
                            if note.self_tags:
                                st.write(f"**Tags:** {', '.join(note.self_tags)}")

# Setup management
st.markdown("---")
st.subheader("📋 Manage Trading Setups")

with st.expander("Create New Setup"):
    with st.form("create_setup"):
        setup_name = st.text_input("Setup Name", placeholder="e.g., Breakout Setup, Trend Following, etc.")
        setup_description = st.text_area("Setup Description", placeholder="Describe the setup criteria, entry conditions, and risk management rules...")
        
        if st.form_submit_button("➕ Create Setup"):
            if setup_name:
                try:
                    new_setup = setup_dal.create_setup(setup_name, setup_description)
                    st.success(f"✅ Created setup: {new_setup.name}")
                except Exception as e:
                    st.error(f"❌ Error creating setup: {str(e)}")

# Show existing setups
setups = setup_dal.get_setups()
if setups:
    st.markdown("**📋 Existing Setups:**")
    for setup in setups:
        with st.expander(f"📋 {setup.name}"):
            st.write(setup.description or "No description provided")
            st.write(f"**ID:** {setup.id}")

db.close()
