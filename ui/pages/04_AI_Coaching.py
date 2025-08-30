"""
AI Coaching & Insights
Advanced AI-powered coaching, pattern analysis, and recommendations
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from utils.ai_integration import GeminiAI
from agents.crew_orchestrator import TradingCrewOrchestrator
from models.dal import TradeDAL, PsychologyDAL, get_db_session
from models.models import Trade, PsychologyNote

# Page config
st.set_page_config(
    page_title="AI Coaching",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.coaching-card {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 5px solid #1f77b4;
}

.insight-card {
    background-color: #e8f4fd;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #00cc96;
}

.warning-card {
    background-color: #fff3cd;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #ffc107;
}

.success-card {
    background-color: #d1edff;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #28a745;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Trading Coach")
st.markdown("Get personalized insights, pattern analysis, and actionable coaching advice powered by advanced AI.")

# Initialize AI components
@st.cache_resource
def get_ai_components():
    return GeminiAI(), TradingCrewOrchestrator()

ai_engine, crew_orchestrator = get_ai_components()

# Sidebar - AI Settings
st.sidebar.header("🎛️ AI Settings")

analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Comprehensive Analysis", "Quick Insights", "Pattern Detection", "Psychology Focus"],
    help="Choose the type of AI analysis you want"
)

lookback_period = st.sidebar.selectbox(
    "Analysis Period",
    ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
    index=1
)

# Convert lookback to datetime
lookback_map = {
    "Last 7 days": timedelta(days=7),
    "Last 30 days": timedelta(days=30),
    "Last 90 days": timedelta(days=90),
    "All time": None
}

start_date = datetime.now() - lookback_map[lookback_period] if lookback_map[lookback_period] else None

# Get data for analysis
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_trading_data(start_date):
    db = get_db_session()
    trade_dal = TradeDAL(db)
    psych_dal = PsychologyDAL(db)
    
    # Get trades
    if start_date:
        trades = trade_dal.get_trades(limit=1000, start_date=start_date)
    else:
        trades = trade_dal.get_trades(limit=1000)
    
    # Get psychology notes
    psychology_notes = psych_dal.get_recent_notes(limit=100)
    
    db.close()
    return trades, psychology_notes

trades, psychology_notes = get_trading_data(start_date)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧠 AI Coaching", "🔍 Pattern Analysis", "📊 Performance Review", "🎯 Action Plan"])

with tab1:
    st.header("🧠 Personalized AI Coaching")
    
    if not trades:
        st.info("No trades found for analysis. Start trading to get AI coaching insights!")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Generate AI Coaching", type="primary"):
                with st.spinner("🤖 AI is analyzing your trading performance..."):
                    # Prepare data for AI analysis
                    trade_data = []
                    for trade in trades[:10]:  # Limit to recent trades
                        trade_data.append({
                            'symbol': trade.symbol,
                            'direction': trade.direction,
                            'pnl': trade.pnl,
                            'r_multiple': trade.r_multiple,
                            'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                            'setup_name': trade.setup.name if trade.setup else 'No Setup'
                        })
                    
                    psychology_data = []
                    for note in psychology_notes[:10]:
                        psychology_data.append({
                            'sentiment_score': getattr(note, 'sentiment_score', 0),
                            'note_text': note.note_text[:100] if hasattr(note, 'note_text') else '',
                            'created_at': note.created_at.isoformat() if hasattr(note, 'created_at') else None
                        })
                    
                    try:
                        if analysis_type == "Comprehensive Analysis":
                            # Use CrewAI for comprehensive analysis
                            coaching_result = crew_orchestrator.analyze_portfolio(trade_data, psychology_data)
                        else:
                            # Use individual AI for quick analysis
                            coaching_result = ai_engine.generate_coaching_advice(trade_data, psychology_data)
                        
                        st.session_state.coaching_result = coaching_result
                    
                    except Exception as e:
                        st.error(f"Error generating coaching advice: {str(e)}")
                        st.session_state.coaching_result = None
        
        with col2:
            st.info(f"📊 **Analysis Scope**\n\n"
                   f"• **Trades:** {len(trades)}\n"
                   f"• **Psychology Notes:** {len(psychology_notes)}\n"
                   f"• **Period:** {lookback_period}\n"
                   f"• **Analysis Type:** {analysis_type}")
        
        # Display coaching results
        if hasattr(st.session_state, 'coaching_result') and st.session_state.coaching_result:
            result = st.session_state.coaching_result
            
            if isinstance(result, str):
                # CrewAI result (text format)
                st.markdown(f'<div class="coaching-card">{result}</div>', unsafe_allow_html=True)
            
            elif isinstance(result, dict):
                # Individual AI result (structured format)
                
                # Overall Assessment
                if 'overall_assessment' in result:
                    st.subheader("📊 Overall Assessment")
                    assessment = result['overall_assessment']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**💪 Strengths:**")
                        for strength in assessment.get('strengths', []):
                            st.write(f"• {strength}")
                    
                    with col2:
                        st.markdown("**🎯 Areas for Improvement:**")
                        for weakness in assessment.get('weaknesses', []):
                            st.write(f"• {weakness}")
                    
                    current_state = assessment.get('current_state', 'fair')
                    if current_state == 'excellent':
                        st.markdown('<div class="success-card">🌟 <strong>Current State:</strong> Excellent! Keep up the great work!</div>', unsafe_allow_html=True)
                    elif current_state == 'good':
                        st.markdown('<div class="insight-card">✅ <strong>Current State:</strong> Good performance with room for optimization.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-card">⚠️ <strong>Current State:</strong> Needs improvement. Focus on the recommendations below.</div>', unsafe_allow_html=True)
                
                # Psychology Coaching
                if 'psychology_coaching' in result:
                    st.subheader("🧠 Psychology Coaching")
                    psych = result['psychology_coaching']
                    
                    with st.expander("🔍 Emotional Patterns", expanded=True):
                        for pattern in psych.get('emotional_patterns', []):
                            st.write(f"• {pattern}")
                    
                    with st.expander("💡 Mindset Advice"):
                        for advice in psych.get('mindset_advice', []):
                            st.write(f"• {advice}")
                    
                    with st.expander("😌 Stress Management"):
                        for tip in psych.get('stress_management', []):
                            st.write(f"• {tip}")
                
                # Technical Coaching
                if 'technical_coaching' in result:
                    st.subheader("⚡ Technical Coaching")
                    tech = result['technical_coaching']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**🎯 Setup Improvements:**")
                        for improvement in tech.get('setup_improvements', []):
                            st.write(f"• {improvement}")
                    
                    with col2:
                        st.markdown("**🛡️ Risk Management:**")
                        for tip in tech.get('risk_management', []):
                            st.write(f"• {tip}")
                    
                    with col3:
                        st.markdown("**⚡ Execution Tips:**")
                        for tip in tech.get('execution_tips', []):
                            st.write(f"• {tip}")
                
                # Motivational Message
                if 'motivational_message' in result:
                    st.subheader("🚀 Motivational Message")
                    st.markdown(f'<div class="success-card">{result["motivational_message"]}</div>', unsafe_allow_html=True)

with tab2:
    st.header("🔍 Pattern Analysis")
    
    if not trades:
        st.info("No trades available for pattern analysis.")
    else:
        if st.button("🔍 Analyze Trading Patterns", type="primary"):
            with st.spinner("🤖 Detecting patterns in your trading..."):
                try:
                    # Prepare trade data for pattern analysis
                    pattern_data = []
                    for trade in trades:
                        pattern_data.append({
                            'symbol': trade.symbol,
                            'direction': trade.direction,
                            'pnl': trade.pnl,
                            'r_multiple': trade.r_multiple,
                            'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                            'setup_name': trade.setup.name if trade.setup else 'No Setup',
                            'fees': trade.fees or 0
                        })
                    
                    patterns = ai_engine.detect_patterns(pattern_data)
                    st.session_state.patterns = patterns
                
                except Exception as e:
                    st.error(f"Error detecting patterns: {str(e)}")
                    st.session_state.patterns = None
        
        if hasattr(st.session_state, 'patterns') and st.session_state.patterns:
            patterns = st.session_state.patterns
            
            # Setup Patterns
            if 'setup_patterns' in patterns and patterns['setup_patterns']:
                st.subheader("🎯 Setup Patterns")
                for pattern in patterns['setup_patterns']:
                    with st.expander(f"📊 {pattern['pattern_name']} (Used {pattern['frequency']} times)"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Win Rate", f"{pattern.get('win_rate', 0):.1f}%")
                        with col2:
                            st.metric("Avg R-Multiple", f"{pattern.get('avg_r_multiple', 0):.2f}R")
                        with col3:
                            st.metric("Frequency", pattern['frequency'])
                        
                        st.write(f"**Description:** {pattern['description']}")
            
            # Behavioral Patterns
            if 'behavioral_patterns' in patterns and patterns['behavioral_patterns']:
                st.subheader("🧠 Behavioral Patterns")
                for pattern in patterns['behavioral_patterns']:
                    impact_color = "success-card" if pattern['impact'] == 'positive' else "warning-card"
                    st.markdown(f"""
                    <div class="{impact_color}">
                        <strong>{pattern['pattern_name']}</strong> (Frequency: {pattern['frequency']})<br>
                        Impact: {pattern['impact'].title()}<br>
                        {pattern['description']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Recommendations
            if 'recommendations' in patterns and patterns['recommendations']:
                st.subheader("💡 Pattern-Based Recommendations")
                for i, rec in enumerate(patterns['recommendations'], 1):
                    st.write(f"{i}. {rec}")

with tab3:
    st.header("📊 AI Performance Review")
    
    if not trades:
        st.info("No trades available for performance review.")
    else:
        # Select specific trade for detailed analysis
        st.subheader("🔍 Single Trade Analysis")
        
        # Create trade options
        trade_options = []
        for trade in trades[:20]:  # Limit to recent 20 trades
            trade_options.append({
                'display': f"{trade.symbol} {trade.direction} - ${trade.pnl:.2f} ({trade.entry_time.strftime('%Y-%m-%d') if trade.entry_time else 'Unknown'})",
                'trade': trade
            })
        
        if trade_options:
            selected_trade_idx = st.selectbox(
                "Select Trade for Analysis",
                range(len(trade_options)),
                format_func=lambda x: trade_options[x]['display']
            )
            
            selected_trade = trade_options[selected_trade_idx]['trade']
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🤖 Analyze This Trade", type="primary"):
                    with st.spinner("🤖 AI is analyzing the selected trade..."):
                        try:
                            trade_data = {
                                'symbol': selected_trade.symbol,
                                'direction': selected_trade.direction,
                                'entry_price': selected_trade.entry_price,
                                'exit_price': selected_trade.exit_price,
                                'quantity': selected_trade.quantity,
                                'pnl': selected_trade.pnl,
                                'r_multiple': selected_trade.r_multiple,
                                'setup_name': selected_trade.setup.name if selected_trade.setup else 'No Setup',
                                'logic': getattr(selected_trade, 'logic', 'No logic provided'),
                                'stop_price': selected_trade.stop_price,
                                'fees': selected_trade.fees or 0
                            }
                            
                            # Use CrewAI for detailed trade analysis
                            analysis_result = crew_orchestrator.analyze_trade(trade_data)
                            st.session_state.trade_analysis = analysis_result
                        
                        except Exception as e:
                            st.error(f"Error analyzing trade: {str(e)}")
                            st.session_state.trade_analysis = None
            
            with col2:
                st.info(f"**Trade Details:**\n\n"
                       f"Symbol: {selected_trade.symbol}\n\n"
                       f"Direction: {selected_trade.direction}\n\n"
                       f"P&L: ${selected_trade.pnl:.2f}\n\n"
                       f"R-Multiple: {selected_trade.r_multiple:.2f}R")
            
            # Display analysis results
            if hasattr(st.session_state, 'trade_analysis') and st.session_state.trade_analysis:
                st.subheader("🤖 AI Trade Analysis")
                st.markdown(f'<div class="coaching-card">{st.session_state.trade_analysis}</div>', unsafe_allow_html=True)

with tab4:
    st.header("🎯 AI-Generated Action Plan")
    
    if hasattr(st.session_state, 'coaching_result') and st.session_state.coaching_result:
        result = st.session_state.coaching_result
        
        if isinstance(result, dict) and 'action_plan' in result:
            action_plan = result['action_plan']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("⚡ Immediate Actions")
                for i, action in enumerate(action_plan.get('immediate_actions', []), 1):
                    checkbox_key = f"immediate_{i}"
                    completed = st.checkbox(f"{action}", key=checkbox_key)
                    if completed:
                        st.success("✅ Completed!")
            
            with col2:
                st.subheader("📅 Weekly Goals")
                for i, goal in enumerate(action_plan.get('weekly_goals', []), 1):
                    checkbox_key = f"weekly_{i}"
                    completed = st.checkbox(f"{goal}", key=checkbox_key)
                    if completed:
                        st.success("✅ Completed!")
            
            with col3:
                st.subheader("📈 Monthly Objectives")
                for i, objective in enumerate(action_plan.get('monthly_objectives', []), 1):
                    checkbox_key = f"monthly_{i}"
                    completed = st.checkbox(f"{objective}", key=checkbox_key)
                    if completed:
                        st.success("✅ Completed!")
        
        else:
            st.info("Generate AI coaching first to see your personalized action plan!")
    
    else:
        st.info("Generate AI coaching analysis to see your personalized action plan!")
    
    # Progress tracking
    st.subheader("📊 Progress Tracking")
    
    # Simple progress metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("This Week's Progress", "75%", delta="5%")
    
    with col2:
        st.metric("Action Items Completed", "12/16", delta="2")
    
    with col3:
        st.metric("Improvement Score", "8.2/10", delta="0.5")

# Footer with tips
st.markdown("---")
st.markdown("""
💡 **AI Coaching Tips:**
- Use the comprehensive analysis for detailed insights
- Review patterns regularly to identify recurring behaviors
- Focus on one improvement area at a time
- Track your progress using the action plan checklist
""")

# Debug information (for development)
with st.expander("🔧 Debug Information", expanded=False):
    st.write(f"**Trades loaded:** {len(trades)}")
    st.write(f"**Psychology notes:** {len(psychology_notes)}")
    st.write(f"**Analysis period:** {lookback_period}")
    st.write(f"**AI Engine enabled:** {ai_engine.enabled}")
    st.write(f"**CrewAI enabled:** {crew_orchestrator.enabled}")
