#!/usr/bin/env python3
"""
Historical Trading Analysis Page
AI-powered analysis of imported trading history
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.historical_analyzer import HistoricalTradingAnalyzer
from models.dal import get_db_session

def main():
    st.set_page_config(
        page_title="Historical Analysis - MindTrade AI",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Historical Trading Analysis")
    st.markdown("AI-powered analysis of your complete trading history")
    
    # Initialize analyzer
    if 'historical_analyzer' not in st.session_state:
        st.session_state.historical_analyzer = HistoricalTradingAnalyzer()
    
    # Sidebar controls
    st.sidebar.title("🔧 Analysis Controls")
    
    # Time period selection
    days_back = st.sidebar.selectbox(
        "Analysis Period:",
        [30, 90, 180, 365, 730],
        index=3,
        format_func=lambda x: f"{x} days" if x < 365 else f"{x//365} year{'s' if x//365 > 1 else ''}"
    )
    
    # Analysis type selection
    analysis_type = st.sidebar.radio(
        "Analysis Type:",
        ["📈 Quick Overview", "🔍 Deep Analysis", "🎯 AI Coaching", "📊 Full Report"]
    )
    
    # Run analysis button
    if st.sidebar.button("🚀 Run Analysis", type="primary"):
        run_analysis(days_back, analysis_type)
    
    # Display results based on analysis type
    if analysis_type == "📈 Quick Overview":
        display_quick_overview()
    elif analysis_type == "🔍 Deep Analysis":
        display_deep_analysis()
    elif analysis_type == "🎯 AI Coaching":
        display_ai_coaching()
    elif analysis_type == "📊 Full Report":
        display_full_report()

def run_analysis(days_back: int, analysis_type: str):
    """Run the selected analysis"""
    with st.spinner(f"🤖 Analyzing {days_back} days of trading data..."):
        try:
            analyzer = st.session_state.historical_analyzer
            
            if analysis_type == "📈 Quick Overview":
                # Quick metrics only
                trades = analyzer.get_historical_trades(days_back)
                if trades:
                    metrics = analyzer.calculate_trading_metrics(trades)
                    st.session_state.quick_metrics = metrics
                    st.success(f"✅ Quick analysis complete! Analyzed {len(trades)} trades.")
                else:
                    st.warning("⚠️ No trades found for the selected period.")
            
            elif analysis_type == "🔍 Deep Analysis":
                # Full analysis without AI
                trades = analyzer.get_historical_trades(days_back)
                if trades:
                    metrics = analyzer.calculate_trading_metrics(trades)
                    style_report = analyzer.generate_trading_style_report(trades)
                    st.session_state.deep_analysis = {
                        'metrics': metrics,
                        'style_report': style_report,
                        'trades_count': len(trades)
                    }
                    st.success(f"✅ Deep analysis complete! Analyzed {len(trades)} trades.")
                else:
                    st.warning("⚠️ No trades found for the selected period.")
            
            elif analysis_type == "🎯 AI Coaching":
                # AI coaching analysis
                result = analyzer.run_complete_analysis(days_back)
                if 'error' not in result:
                    st.session_state.ai_coaching = result
                    st.success(f"✅ AI coaching analysis complete! Analyzed {result['analysis_summary']['total_trades_analyzed']} trades.")
                else:
                    st.error(f"❌ Analysis failed: {result['error']}")
            
            elif analysis_type == "📊 Full Report":
                # Complete analysis with report generation
                result = analyzer.run_complete_analysis(days_back)
                if 'error' not in result:
                    st.session_state.full_report = result
                    st.success(f"✅ Full report generated! Analyzed {result['analysis_summary']['total_trades_analyzed']} trades.")
                    st.info(f"📄 Report saved: {result.get('report_file', 'N/A')}")
                else:
                    st.error(f"❌ Analysis failed: {result['error']}")
                    
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")

def display_quick_overview():
    """Display quick overview metrics"""
    st.header("📈 Quick Trading Overview")
    
    if 'quick_metrics' not in st.session_state:
        st.info("👆 Click 'Run Analysis' to generate quick overview")
        return
    
    metrics = st.session_state.quick_metrics
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total P&L", f"${metrics['summary']['total_pnl']:,.2f}")
    
    with col2:
        st.metric("Win Rate", f"{metrics['summary']['win_rate']:.1f}%")
    
    with col3:
        st.metric("Total Trades", metrics['summary']['total_trades'])
    
    with col4:
        pf = metrics['summary']['profit_factor']
        st.metric("Profit Factor", f"{pf:.2f}" if pf != 'N/A' else "N/A")
    
    # Performance breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Performance Breakdown")
        perf = metrics['performance']
        
        st.metric("Winning Trades", perf['winning_trades'])
        st.metric("Average Win", f"${perf['avg_win']:,.2f}")
        st.metric("Largest Win", f"${perf['largest_win']:,.2f}")
    
    with col2:
        st.subheader("📉 Loss Analysis")
        st.metric("Losing Trades", perf['losing_trades'])
        st.metric("Average Loss", f"${perf['avg_loss']:,.2f}")
        st.metric("Largest Loss", f"${perf['largest_loss']:,.2f}")
    
    # Direction analysis
    if 'direction_analysis' in metrics:
        st.subheader("📈 Direction Analysis")
        direction = metrics['direction_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Long Trades", direction['long_trades'])
            st.metric("Long P&L", f"${direction['long_pnl']:,.2f}")
            st.metric("Long Win Rate", f"{direction['long_win_rate']:.1f}%")
        
        with col2:
            st.metric("Short Trades", direction['short_trades'])
            st.metric("Short P&L", f"${direction['short_pnl']:,.2f}")
            st.metric("Short Win Rate", f"{direction['short_win_rate']:.1f}%")

def display_deep_analysis():
    """Display deep analysis results"""
    st.header("🔍 Deep Trading Analysis")
    
    if 'deep_analysis' not in st.session_state:
        st.info("👆 Click 'Run Analysis' to generate deep analysis")
        return
    
    analysis = st.session_state.deep_analysis
    metrics = analysis['metrics']
    style_report = analysis['style_report']
    
    # Trading style analysis
    st.subheader("🎯 Trading Style Analysis")
    
    if 'trading_style' in style_report:
        style = style_report['trading_style']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Trading Style", style['frequency_style'])
            st.metric("Risk Tolerance", style['risk_tolerance'])
        
        with col2:
            st.metric("Direction Bias", style['direction_bias'])
            st.metric("Symbol Concentration", style['symbol_concentration'])
        
        with col3:
            st.metric("Avg Trades/Day", f"{style['avg_trades_per_day']:.1f}")
            st.metric("Win Rate Consistency", style['win_rate_consistency'])
    
    # Behavioral insights
    if 'behavioral_insights' in style_report:
        st.subheader("🧠 Behavioral Insights")
        behavioral = style_report['behavioral_insights']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overtrading", behavioral['overtrading_indicator'])
        
        with col2:
            st.metric("Risk Management", behavioral['risk_management_quality'])
        
        with col3:
            st.metric("Discipline Level", behavioral['discipline_level'])
    
    # Risk management analysis
    if 'risk_management' in metrics:
        st.subheader("🛡️ Risk Management Analysis")
        risk = metrics['risk_management']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg R-Multiple", f"{risk['avg_r_multiple']:.2f}")
            st.metric("Positive R Trades", risk['positive_r_trades'])
        
        with col2:
            st.metric("Avg Positive R", f"{risk['avg_positive_r']:.2f}")
            st.metric("Negative R Trades", risk['negative_r_trades'])
        
        with col3:
            st.metric("Avg Negative R", f"{risk['avg_negative_r']:.2f}")
    
    # Time analysis
    if 'time_analysis' in metrics and metrics['time_analysis']['hourly_performance']:
        st.subheader("⏰ Time-Based Analysis")
        
        # Hourly performance chart
        hourly_data = metrics['time_analysis']['hourly_performance']
        if hourly_data:
            hours = list(hourly_data.keys())
            pnl_values = list(hourly_data.values())
            
            fig = px.bar(
                x=hours, 
                y=pnl_values,
                title="Hourly P&L Performance",
                labels={'x': 'Hour of Day', 'y': 'P&L ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)

def display_ai_coaching():
    """Display AI coaching insights"""
    st.header("🎯 AI Trading Coach")
    
    if 'ai_coaching' not in st.session_state:
        st.info("👆 Click 'Run Analysis' to get AI coaching insights")
        return
    
    coaching = st.session_state.ai_coaching
    
    # Trading style summary
    if 'trading_style' in coaching:
        st.subheader("🎯 Your Trading Profile")
        style = coaching['trading_style']['trading_style']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Style", style['frequency_style'])
            st.metric("Risk Level", style['risk_tolerance'])
        
        with col2:
            st.metric("Direction", style['direction_bias'])
            st.metric("Concentration", style['symbol_concentration'])
        
        with col3:
            st.metric("Consistency", style['win_rate_consistency'])
    
    # AI coaching insights
    if 'coaching_insights' in coaching:
        st.subheader("🤖 AI Coaching Insights")
        
        insights = coaching['coaching_insights']
        
        if 'coaching_insights' in insights:
            st.write(insights['coaching_insights'])
        
        # Action items
        if 'action_items' in insights and insights['action_items']:
            st.subheader("🎯 Action Items")
            for i, item in enumerate(insights['action_items'], 1):
                st.write(f"{i}. {item}")
    
    # Performance metrics
    if 'metrics' in coaching:
        st.subheader("📊 Performance Summary")
        metrics = coaching['metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total P&L", f"${metrics['summary']['total_pnl']:,.2f}")
        
        with col2:
            st.metric("Win Rate", f"{metrics['summary']['win_rate']:.1f}%")
        
        with col3:
            st.metric("Profit Factor", f"{metrics['summary']['profit_factor']:.2f}")
        
        with col4:
            st.metric("Total Trades", metrics['summary']['total_trades'])

def display_full_report():
    """Display full analysis report"""
    st.header("📊 Complete Trading Analysis Report")
    
    if 'full_report' not in st.session_state:
        st.info("👆 Click 'Run Analysis' to generate full report")
        return
    
    report = st.session_state.full_report
    
    # Report summary
    st.subheader("📋 Report Summary")
    summary = report['analysis_summary']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Trades Analyzed", summary['total_trades_analyzed'])
    
    with col2:
        st.metric("Analysis Period", f"{summary['analysis_period_days']} days")
    
    with col3:
        st.metric("Report Generated", summary['analysis_timestamp'][:10])
    
    # Download report
    if 'report_file' in report and report['report_file']:
        with open(report['report_file'], 'r') as f:
            report_data = f.read()
        
        st.download_button(
            label="📥 Download Full Report (JSON)",
            data=report_data,
            file_name=report['report_file'],
            mime="application/json"
        )
    
    # Display all sections
    tabs = st.tabs(["📈 Performance", "🎯 Style Analysis", "🤖 AI Insights", "📊 Detailed Metrics"])
    
    with tabs[0]:
        display_performance_tab(report)
    
    with tabs[1]:
        display_style_tab(report)
    
    with tabs[2]:
        display_ai_tab(report)
    
    with tabs[3]:
        display_metrics_tab(report)

def display_performance_tab(report):
    """Display performance tab"""
    metrics = report.get('metrics', {})
    
    if 'summary' in metrics:
        st.subheader("💰 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total P&L", f"${metrics['summary']['total_pnl']:,.2f}")
        
        with col2:
            st.metric("Win Rate", f"{metrics['summary']['win_rate']:.1f}%")
        
        with col3:
            st.metric("Profit Factor", f"{metrics['summary']['profit_factor']:.2f}")
        
        with col4:
            st.metric("Total Trades", metrics['summary']['total_trades'])
    
    if 'performance' in metrics:
        st.subheader("📊 Performance Breakdown")
        perf = metrics['performance']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Winning Trades", perf['winning_trades'])
            st.metric("Average Win", f"${perf['avg_win']:,.2f}")
            st.metric("Largest Win", f"${perf['largest_win']:,.2f}")
        
        with col2:
            st.metric("Losing Trades", perf['losing_trades'])
            st.metric("Average Loss", f"${perf['avg_loss']:,.2f}")
            st.metric("Largest Loss", f"${perf['largest_loss']:,.2f}")

def display_style_tab(report):
    """Display style analysis tab"""
    style_report = report.get('trading_style', {})
    
    if 'trading_style' in style_report:
        st.subheader("🎯 Trading Style Analysis")
        style = style_report['trading_style']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Frequency Style", style['frequency_style'])
            st.metric("Risk Tolerance", style['risk_tolerance'])
            st.metric("Direction Bias", style['direction_bias'])
        
        with col2:
            st.metric("Symbol Concentration", style['symbol_concentration'])
            st.metric("Win Rate Consistency", style['win_rate_consistency'])
            st.metric("Avg Trades/Day", f"{style['avg_trades_per_day']:.1f}")
    
    if 'behavioral_insights' in style_report:
        st.subheader("🧠 Behavioral Insights")
        behavioral = style_report['behavioral_insights']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overtrading", behavioral['overtrading_indicator'])
        
        with col2:
            st.metric("Risk Management", behavioral['risk_management_quality'])
        
        with col3:
            st.metric("Discipline Level", behavioral['discipline_level'])

def display_ai_tab(report):
    """Display AI insights tab"""
    coaching = report.get('coaching_insights', {})
    
    if 'coaching_insights' in coaching:
        st.subheader("🤖 AI Coaching Insights")
        st.write(coaching['coaching_insights'])
    
    if 'action_items' in coaching and coaching['action_items']:
        st.subheader("🎯 Action Items")
        for i, item in enumerate(coaching['action_items'], 1):
            st.write(f"{i}. {item}")

def display_metrics_tab(report):
    """Display detailed metrics tab"""
    metrics = report.get('metrics', {})
    
    # Risk management
    if 'risk_management' in metrics:
        st.subheader("🛡️ Risk Management")
        risk = metrics['risk_management']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg R-Multiple", f"{risk['avg_r_multiple']:.2f}")
            st.metric("Positive R Trades", risk['positive_r_trades'])
        
        with col2:
            st.metric("Avg Positive R", f"{risk['avg_positive_r']:.2f}")
            st.metric("Negative R Trades", risk['negative_r_trades'])
        
        with col3:
            st.metric("Avg Negative R", f"{risk['avg_negative_r']:.2f}")
    
    # Direction analysis
    if 'direction_analysis' in metrics:
        st.subheader("📈 Direction Analysis")
        direction = metrics['direction_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Long Trades", direction['long_trades'])
            st.metric("Long P&L", f"${direction['long_pnl']:,.2f}")
            st.metric("Long Win Rate", f"{direction['long_win_rate']:.1f}%")
        
        with col2:
            st.metric("Short Trades", direction['short_trades'])
            st.metric("Short P&L", f"${direction['short_pnl']:,.2f}")
            st.metric("Short Win Rate", f"{direction['short_win_rate']:.1f}%")

if __name__ == "__main__":
    main()
