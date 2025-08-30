import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our modules
from models.database import init_db
from models.dal import TradeDAL, PsychologyDAL, SetupDAL, AnalyticsDAL, get_db_session
from utils.ai_integration import GeminiAI
from orchestrator.ai_orchestrator import AIOrchestrator

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
    .ai-analysis {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    try:
        init_db()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

# Initialize AI Orchestrator
@st.cache_resource
def init_ai_orchestrator():
    return AIOrchestrator()

# Initialize components
db_initialized = init_database()
ai_orchestrator = init_ai_orchestrator()

# Sidebar
st.sidebar.title("MindTrade AI")
st.sidebar.markdown("---")

# AI Status
if ai_orchestrator.enabled:
    st.sidebar.success("🤖 AI Orchestrator Enabled (Gemini 2.5 Flash)")
    st.sidebar.info("✅ All Agents Active")
else:
    st.sidebar.warning("⚠️ AI Orchestrator Disabled - Add GOOGLE_API_KEY to enable")
    
    # Show individual agent status
    status = ai_orchestrator.get_orchestrator_status()
    if not status['api_key_configured']:
        st.sidebar.error("❌ API Key Missing")
    else:
        st.sidebar.warning("⚠️ Some agents disabled")

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Add Trade", "Trade History", "Analytics", "Psychology", "Market Analysis", "Settings"]
)

# Get database session
def get_db():
    return get_db_session()

# Main content
if page == "Dashboard":
    st.markdown('<h1 class="main-header">📈 MindTrade AI Dashboard</h1>', unsafe_allow_html=True)
    
    if not db_initialized:
        st.error("Database not initialized. Please check the logs.")
        st.stop()
    
    # Get analytics
    with get_db() as db:
        analytics_dal = AnalyticsDAL(db)
        summary = analytics_dal.get_trading_summary()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pnl_color = "positive" if summary['total_pnl'] >= 0 else "negative"
        st.metric(
            label="Total P&L",
            value=f"${summary['total_pnl']:.2f}",
            delta=f"{summary['total_pnl']:.2f}",
            delta_color="normal" if summary['total_pnl'] >= 0 else "inverse"
        )
    
    with col2:
        st.metric(
            label="Win Rate",
            value=f"{summary['win_rate']:.1f}%",
            delta=f"{summary['win_rate']:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Total Trades",
            value=summary['total_trades'],
            delta=summary['total_trades']
        )
    
    with col4:
        st.metric(
            label="Avg R Multiple",
            value=f"{summary['avg_r_multiple']:.2f}",
            delta=f"{summary['avg_r_multiple']:.2f}"
        )
    
    # Performance charts
    st.subheader("📊 Performance Overview")
    
    # Get recent trades for equity curve
    with get_db() as db:
        trade_dal = TradeDAL(db)
        recent_trades = trade_dal.get_trades(limit=50)
    
    if recent_trades:
        # Create equity curve data
        equity_data = []
        cumulative_pnl = 0
        for trade in reversed(recent_trades):  # Oldest first
            cumulative_pnl += trade.pnl
            equity_data.append({
                'date': trade.trade_time,
                'equity': 10000 + cumulative_pnl,  # Starting with 10k
                'pnl': cumulative_pnl
            })
        
        if equity_data:
            df_equity = pd.DataFrame(equity_data)
            
            # Equity curve
            fig_equity = px.line(
                df_equity, 
                x='date', 
                y='equity',
                title="Equity Curve",
                labels={'equity': 'Account Value ($)', 'date': 'Date'}
            )
            fig_equity.update_layout(height=400)
            st.plotly_chart(fig_equity, use_container_width=True)
    
    # AI Coaching Section
    if ai.enabled:
        st.subheader("🤖 AI Coaching Insights")
        
        if st.button("Generate AI Coaching Advice"):
            with st.spinner("Generating personalized coaching advice..."):
                with get_db() as db:
                    trade_dal = TradeDAL(db)
                    psychology_dal = PsychologyDAL(db)
                    
                    recent_trades_data = []
                    for trade in trade_dal.get_trades(limit=10):
                        recent_trades_data.append({
                            'symbol': trade.symbol,
                            'pnl': trade.pnl,
                            'r_multiple': trade.r_multiple,
                            'setup_name': trade.setup.name if trade.setup else 'Unknown'
                        })
                    
                    psychology_notes_data = []
                    for trade in trade_dal.get_trades(limit=10):
                        notes = psychology_dal.get_psychology_notes(trade.id)
                        for note in notes:
                            psychology_notes_data.append({
                                'sentiment_score': note.sentiment_score or 0,
                                'fear_score': note.fear_score or 0,
                                'greed_score': note.greed_score or 0
                            })
                    
                    coaching_advice = ai.generate_coaching_advice(recent_trades_data, psychology_notes_data)
                    
                    # Display coaching advice
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Overall Assessment**")
                        st.write(f"**Current State:** {coaching_advice['overall_assessment']['current_state']}")
                        st.write("**Strengths:**")
                        for strength in coaching_advice['overall_assessment']['strengths']:
                            st.write(f"• {strength}")
                        st.write("**Areas for Improvement:**")
                        for weakness in coaching_advice['overall_assessment']['weaknesses']:
                            st.write(f"• {weakness}")
                    
                    with col2:
                        st.markdown("**Action Plan**")
                        st.write("**Immediate Actions:**")
                        for action in coaching_advice['action_plan']['immediate_actions']:
                            st.write(f"• {action}")
                    
                    st.markdown("**💬 Motivational Message**")
                    st.info(coaching_advice['motivational_message'])

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
        
        # Get setups from database
        with get_db() as db:
            setup_dal = SetupDAL(db)
            setups = setup_dal.get_setups()
            setup_options = [setup.name for setup in setups]
        
        setup_type = st.selectbox("Setup Type", setup_options)
        
        logic = st.text_area("Trade Logic", placeholder="Describe your trade setup and reasoning...")
        psych_note = st.text_area("Psychology Notes", placeholder="How did you feel? Any emotions or behavioral patterns?")
        
        # Image upload section
        st.subheader("📸 Trade Screenshot (Optional)")
        uploaded_image = st.file_uploader(
            "Upload chart screenshot", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload a screenshot of your trade setup or chart analysis"
        )
        
        submitted = st.form_submit_button("Add Trade")
        
        if submitted:
            if not symbol or not entry_price or not exit_price:
                st.error("Please fill in all required fields (Symbol, Entry Price, Exit Price)")
            else:
                try:
                    with get_db() as db:
                        trade_dal = TradeDAL(db)
                        
                        # Get setup ID
                        setup_id = None
                        for setup in setups:
                            if setup.name == setup_type:
                                setup_id = setup.id
                                break
                        
                        # Create trade data
                        trade_data = {
                            'symbol': symbol,
                            'direction': direction,
                            'entry_price': entry_price,
                            'stop_price': stop_price,
                            'exit_price': exit_price,
                            'quantity': quantity,
                            'account_equity': account_equity,
                            'risk_percent': risk_percent,
                            'trade_time': trade_time,
                            'logic': logic,
                            'notes': psych_note,
                            'setup_id': setup_id
                        }
                        
                        # Create trade
                        trade = trade_dal.create_trade(trade_data)
                        
                        # Save image if uploaded
                        image_path = ""
                        if uploaded_image is not None:
                            image_bytes = uploaded_image.read()
                            image_path = ai.save_image(image_bytes, trade.id, "trade_screenshot")
                        
                        # AI Analysis
                        if ai.enabled:
                            st.subheader("🤖 AI Analysis")
                            with st.spinner("Analyzing trade with AI..."):
                                # Prepare trade data for AI
                                ai_trade_data = {
                                    'symbol': trade.symbol,
                                    'direction': trade.direction,
                                    'entry_price': trade.entry_price,
                                    'stop_price': trade.stop_price,
                                    'exit_price': trade.exit_price,
                                    'pnl': trade.pnl,
                                    'r_multiple': trade.r_multiple,
                                    'setup_name': setup_type,
                                    'logic': logic
                                }
                                
                                analysis = ai.analyze_trade_with_image(ai_trade_data, image_path)
                                
                                # Display analysis
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Trade Quality", f"{analysis['trade_quality_score']:.2f}")
                                    st.metric("Risk Management", f"{analysis['risk_management_score']:.2f}")
                                
                                with col2:
                                    st.metric("Execution Score", f"{analysis['execution_score']:.2f}")
                                    st.write(f"**Setup Quality:** {analysis['setup_analysis']['setup_quality']}")
                                
                                with col3:
                                    st.write("**Key Learnings:**")
                                    for learning in analysis['key_learnings']:
                                        st.write(f"• {learning}")
                                
                                if 'chart_analysis' in analysis:
                                    st.markdown("**📊 Chart Analysis**")
                                    st.write(f"**Market Structure:** {analysis['chart_analysis']['market_structure']}")
                                    st.write(f"**Risk/Reward:** {analysis['chart_analysis']['risk_reward_ratio']}")
                        
                        st.success(f"✅ Trade added successfully! ID: {trade.id}")
                        
                        # Show trade summary
                        st.json({
                            "symbol": trade.symbol,
                            "direction": trade.direction,
                            "entry": trade.entry_price,
                            "stop": trade.stop_price,
                            "exit": trade.exit_price,
                            "quantity": trade.quantity,
                            "pnl": trade.pnl,
                            "r_multiple": trade.r_multiple,
                            "setup": setup_type,
                            "logic": logic,
                            "psych_note": psych_note,
                            "image_saved": bool(image_path)
                        })
                        
                except Exception as e:
                    st.error(f"Error adding trade: {e}")

elif page == "Trade History":
    st.title("📋 Trade History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol_filter = st.text_input("Filter by Symbol", placeholder="BTCUSDT")
    
    with col2:
        setup_filter = st.selectbox("Filter by Setup", ["All"] + [setup.name for setup in setups])
    
    with col3:
        date_range = st.date_input("Date Range", value=(datetime.now() - timedelta(days=30), datetime.now()))
    
    # Get trades
    with get_db() as db:
        trade_dal = TradeDAL(db)
        trades = trade_dal.get_trades(limit=100)
    
    if trades:
        # Convert to DataFrame
        trade_data = []
        for trade in trades:
            trade_data.append({
                'ID': trade.id,
                'Date': trade.trade_time.strftime('%Y-%m-%d %H:%M'),
                'Symbol': trade.symbol,
                'Direction': trade.direction,
                'Entry': f"${trade.entry_price:.2f}",
                'Exit': f"${trade.exit_price:.2f}",
                'P&L': f"${trade.pnl:.2f}",
                'R Multiple': f"{trade.r_multiple:.2f}",
                'Setup': trade.setup.name if trade.setup else 'Unknown',
                'Quantity': trade.quantity
            })
        
        df_trades = pd.DataFrame(trade_data)
        
        # Apply filters
        if symbol_filter:
            df_trades = df_trades[df_trades['Symbol'].str.contains(symbol_filter, case=False)]
        
        if setup_filter != "All":
            df_trades = df_trades[df_trades['Setup'] == setup_filter]
        
        st.dataframe(df_trades, use_container_width=True)
        
        # Export option
        csv = df_trades.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No trades found. Add your first trade!")

elif page == "Analytics":
    st.title("📊 Analytics")
    
    # Get analytics data
    with get_db() as db:
        analytics_dal = AnalyticsDAL(db)
        summary = analytics_dal.get_trading_summary()
        setup_performance = analytics_dal.get_setup_performance()
    
    # Setup performance
    if setup_performance:
        st.subheader("Setup Performance")
        
        setup_df = pd.DataFrame(setup_performance)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_setup = px.bar(
                setup_df,
                x='setup_name',
                y='win_rate',
                title="Win Rate by Setup",
                color='avg_r_multiple',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_setup, use_container_width=True)
        
        with col2:
            fig_r_multiple = px.bar(
                setup_df,
                x='setup_name',
                y='avg_r_multiple',
                title="Average R-Multiple by Setup",
                color='total_pnl',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_r_multiple, use_container_width=True)
        
        # Setup performance table
        st.subheader("Detailed Setup Performance")
        st.dataframe(setup_df, use_container_width=True)
    
    # AI Pattern Analysis
    if ai.enabled:
        st.subheader("🤖 AI Pattern Analysis")
        
        if st.button("Analyze Trading Patterns"):
            with st.spinner("Analyzing patterns with AI..."):
                with get_db() as db:
                    trade_dal = TradeDAL(db)
                    all_trades = trade_dal.get_trades(limit=50)
                    
                    trades_data = []
                    for trade in all_trades:
                        trades_data.append({
                            'symbol': trade.symbol,
                            'direction': trade.direction,
                            'pnl': trade.pnl,
                            'r_multiple': trade.r_multiple,
                            'setup': trade.setup.name if trade.setup else 'Unknown',
                            'trade_time': trade.trade_time.strftime('%Y-%m-%d %H:%M')
                        })
                    
                    patterns = ai.detect_patterns(trades_data)
                    
                    # Display patterns
                    if patterns['setup_patterns']:
                        st.markdown("**Setup Patterns**")
                        for pattern in patterns['setup_patterns']:
                            st.write(f"• **{pattern['pattern_name']}**: {pattern['description']} (Win Rate: {pattern['win_rate']:.1f}%)")
                    
                    if patterns['behavioral_patterns']:
                        st.markdown("**Behavioral Patterns**")
                        for pattern in patterns['behavioral_patterns']:
                            impact_color = "🟢" if pattern['impact'] == 'positive' else "🔴"
                            st.write(f"{impact_color} **{pattern['pattern_name']}**: {pattern['description']}")

elif page == "Psychology":
    st.title("🧠 Psychology Analysis")
    
    # Get psychology notes
    with get_db() as db:
        psychology_dal = PsychologyDAL(db)
        trade_dal = TradeDAL(db)
        
        # Get all psychology notes
        all_notes = []
        trades = trade_dal.get_trades(limit=100)
        for trade in trades:
            notes = psychology_dal.get_psychology_notes(trade.id)
            for note in notes:
                all_notes.append({
                    'trade_id': trade.id,
                    'symbol': trade.symbol,
                    'note_text': note.note_text,
                    'sentiment_score': note.sentiment_score or 0,
                    'fear_score': note.fear_score or 0,
                    'greed_score': note.greed_score or 0,
                    'patience_score': note.patience_score or 0,
                    'fomo_score': note.fomo_score or 0,
                    'revenge_score': note.revenge_score or 0,
                    'created_at': note.created_at
                })
    
    if all_notes:
        # Emotion tracking
        st.subheader("Emotional Patterns")
        
        emotions_df = pd.DataFrame(all_notes)
        
        # Calculate average emotions
        avg_emotions = {
            'Sentiment': emotions_df['sentiment_score'].mean(),
            'Fear': emotions_df['fear_score'].mean(),
            'Greed': emotions_df['greed_score'].mean(),
            'Patience': emotions_df['patience_score'].mean(),
            'FOMO': emotions_df['fomo_score'].mean(),
            'Revenge': emotions_df['revenge_score'].mean()
        }
        
        # Display emotion metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Sentiment", f"{avg_emotions['Sentiment']:.2f}")
            st.metric("Average Fear", f"{avg_emotions['Fear']:.2f}")
        
        with col2:
            st.metric("Average Greed", f"{avg_emotions['Greed']:.2f}")
            st.metric("Average Patience", f"{avg_emotions['Patience']:.2f}")
        
        with col3:
            st.metric("Average FOMO", f"{avg_emotions['FOMO']:.2f}")
            st.metric("Average Revenge", f"{avg_emotions['Revenge']:.2f}")
        
        # Emotion scatter plot
        fig_emotions = px.scatter(
            emotions_df,
            x='sentiment_score',
            y='fear_score',
            size='greed_score',
            color='patience_score',
            hover_data=['symbol', 'note_text'],
            title="Emotion Distribution"
        )
        st.plotly_chart(fig_emotions, use_container_width=True)
        
        # Recent psychology notes
        st.subheader("Recent Psychology Notes")
        recent_notes = sorted(all_notes, key=lambda x: x['created_at'], reverse=True)[:10]
        
        for note in recent_notes:
            with st.expander(f"{note['symbol']} - {note['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Note:** {note['note_text']}")
                st.write(f"**Sentiment:** {note['sentiment_score']:.2f}")
                st.write(f"**Fear:** {note['fear_score']:.2f} | **Greed:** {note['greed_score']:.2f} | **Patience:** {note['patience_score']:.2f}")
    else:
        st.info("No psychology notes found. Add notes to your trades to see analysis here.")

elif page == "Market Analysis":
    st.title("📈 Market Analysis")
    
    st.subheader("Upload Market Screenshot for AI Analysis")
    
    uploaded_market_image = st.file_uploader(
        "Upload market screenshot", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a screenshot of market charts for AI analysis"
    )
    
    context = st.text_area("Market Context", placeholder="Describe the current market conditions, timeframe, or any specific context...")
    
    if uploaded_market_image is not None:
        # Display uploaded image
        st.image(uploaded_market_image, caption="Uploaded Market Screenshot", use_column_width=True)
        
        if st.button("Analyze Market with AI"):
            if ai.enabled:
                with st.spinner("Analyzing market with AI..."):
                    # Save image temporarily
                    image_bytes = uploaded_market_image.read()
                    temp_path = f"temp_market_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    
                    with open(temp_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    try:
                        # Analyze with AI
                        analysis = ai.analyze_market_screenshot(temp_path, context)
                        
                        # Display results
                        st.subheader("🤖 AI Market Analysis")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Market Structure**")
                            st.write(f"**Structure:** {analysis['market_analysis']['market_structure']}")
                            st.write(f"**Timeframe:** {analysis['market_analysis']['timeframe']}")
                            st.write(f"**Momentum:** {analysis['market_analysis']['momentum']}")
                            
                            st.markdown("**Key Levels**")
                            for level in analysis['market_analysis']['key_levels']:
                                st.write(f"• {level}")
                        
                        with col2:
                            st.markdown("**Risk Assessment**")
                            st.write(f"**Volatility:** {analysis['risk_assessment']['market_volatility']}")
                            st.write(f"**Risk Level:** {analysis['risk_assessment']['risk_level']}")
                            st.write(f"**Setup Quality:** {analysis['risk_assessment']['setup_quality']}")
                        
                        # Potential setups
                        if analysis['potential_setups']:
                            st.markdown("**Potential Setups**")
                            for setup in analysis['potential_setups']:
                                with st.expander(f"{setup['setup_type']} (Confidence: {setup['confidence']:.1%})"):
                                    st.write(f"**Entry Zone:** {setup['entry_zone']}")
                                    st.write(f"**Stop Loss:** {setup['stop_loss']}")
                                    st.write(f"**Target:** {setup['target']}")
                                    st.write(f"**Risk/Reward:** {setup['risk_reward']}")
                                    st.write(f"**Reasoning:** {setup['reasoning']}")
                        
                        # Recommendations
                        if analysis['recommendations']:
                            st.markdown("**Recommendations**")
                            for rec in analysis['recommendations']:
                                st.write(f"• {rec}")
                        
                        # Key observations
                        if analysis['key_observations']:
                            st.markdown("**Key Observations**")
                            for obs in analysis['key_observations']:
                                st.write(f"• {obs}")
                    
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            else:
                st.error("AI is not enabled. Please add your Google API key in settings.")

elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("AI Configuration")
    
    # Google API Key
    current_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input(
        "Google API Key", 
        value=current_api_key, 
        type="password",
        help="Enter your Google Gemini API key to enable AI features"
    )
    
    if api_key != current_api_key:
        if st.button("Save API Key"):
            # In a real app, you'd save this to a secure configuration
            st.success("API key updated! Please restart the application for changes to take effect.")
    
    st.subheader("Database Information")
    st.info(f"Database: SQLite (data/mindtrade.db)")
    
    if st.button("Reset Database"):
        if st.checkbox("I understand this will delete all data"):
            try:
                from models.database import reset_db
                reset_db()
                st.success("Database reset successfully!")
            except Exception as e:
                st.error(f"Error resetting database: {e}")
    
    st.subheader("Export/Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export All Data"):
            # Export functionality would go here
            st.info("Export functionality coming soon!")
    
    with col2:
        uploaded_file = st.file_uploader("Import Data", type=['json', 'csv'])
        if uploaded_file is not None:
            st.info("Import functionality coming soon!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>MindTrade AI v1.0.0 | Built with ❤️ for traders</div>",
    unsafe_allow_html=True
)
