"""
Advanced Analytics Dashboard
Comprehensive trading performance analysis and visualizations
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.analytics import TradingAnalytics
from models.dal import get_db_session
from models.models import Trade
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Advanced Analytics Dashboard")

# Initialize analytics
@st.cache_resource
def get_analytics():
    return TradingAnalytics()

analytics = get_analytics()

# Sidebar filters
st.sidebar.header("📅 Date Filters")

# Quick date ranges
quick_ranges = {
    "Last 7 days": timedelta(days=7),
    "Last 30 days": timedelta(days=30),
    "Last 90 days": timedelta(days=90),
    "Last 6 months": timedelta(days=180),
    "Last year": timedelta(days=365),
    "All time": None
}

selected_range = st.sidebar.selectbox("Quick Date Range", list(quick_ranges.keys()), index=1)

# Custom date range
use_custom = st.sidebar.checkbox("Use Custom Date Range")

if use_custom:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
else:
    if quick_ranges[selected_range]:
        start_datetime = datetime.now() - quick_ranges[selected_range]
        end_datetime = datetime.now()
    else:
        start_datetime = None
        end_datetime = None

# Performance Overview
st.header("🎯 Performance Overview")

with st.spinner("Calculating performance metrics..."):
    summary = analytics.get_trading_summary(start_datetime, end_datetime)

# Key metrics in columns
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Trades", 
        summary['overview']['total_trades'],
        help="Total number of trades executed"
    )

with col2:
    win_rate = summary['overview']['win_rate']
    st.metric(
        "Win Rate", 
        f"{win_rate}%",
        help="Percentage of profitable trades"
    )

with col3:
    total_pnl = summary['pnl_metrics']['total_pnl']
    st.metric(
        "Total P&L", 
        f"${total_pnl:,.2f}",
        delta=f"${summary['pnl_metrics']['avg_trade']:,.2f} avg",
        help="Total profit and loss"
    )

with col4:
    profit_factor = summary['overview']['profit_factor']
    pf_display = f"{profit_factor}" if profit_factor != 'N/A' else 'N/A'
    st.metric(
        "Profit Factor", 
        pf_display,
        help="Ratio of gross profit to gross loss"
    )

with col5:
    max_dd = summary['risk_metrics']['max_drawdown']
    st.metric(
        "Max Drawdown", 
        f"${max_dd:,.2f}",
        delta=f"{summary['risk_metrics']['max_drawdown_pct']:.1f}%",
        help="Maximum peak-to-trough decline"
    )

# Detailed metrics
st.header("📈 Detailed Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 P&L Metrics")
    st.write(f"**Average Win:** ${summary['pnl_metrics']['avg_win']:,.2f}")
    st.write(f"**Average Loss:** ${summary['pnl_metrics']['avg_loss']:,.2f}")
    st.write(f"**Net P&L:** ${summary['pnl_metrics']['net_pnl']:,.2f}")
    st.write(f"**Total Fees:** ${summary['pnl_metrics']['total_fees']:,.2f}")

with col2:
    st.subheader("⚡ Risk Metrics")
    st.write(f"**Average R-Multiple:** {summary['risk_metrics']['avg_r_multiple']:.2f}R")
    st.write(f"**Total R:** {summary['risk_metrics']['total_r']:.2f}R")
    st.write(f"**Sharpe Ratio:** {summary['risk_metrics']['sharpe_ratio']:.2f}")
    st.write(f"**P&L Volatility:** ${summary['behavioral_metrics']['pnl_volatility']:,.2f}")

with col3:
    st.subheader("🧠 Behavioral Metrics")
    st.write(f"**Max Consecutive Wins:** {summary['behavioral_metrics']['max_consecutive_wins']}")
    st.write(f"**Max Consecutive Losses:** {summary['behavioral_metrics']['max_consecutive_losses']}")
    st.write(f"**Trades per Day:** {summary['behavioral_metrics']['trades_per_day']:.2f}")

# Charts Section
st.header("📊 Performance Visualizations")

# P&L Curve
with st.spinner("Generating P&L curve..."):
    pnl_fig = analytics.generate_pnl_curve(start_datetime, end_datetime)
    st.plotly_chart(pnl_fig, use_container_width=True)

# Two column layout for additional charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Setup Performance")
    with st.spinner("Analyzing setup performance..."):
        setup_fig = analytics.generate_setup_comparison()
        st.plotly_chart(setup_fig, use_container_width=True)

with col2:
    st.subheader("📊 R-Multiple Distribution")
    with st.spinner("Generating R-multiple distribution..."):
        r_fig = analytics.generate_r_multiple_distribution()
        st.plotly_chart(r_fig, use_container_width=True)

# Monthly Performance Heatmap
st.subheader("🔥 Monthly Performance Heatmap")
with st.spinner("Generating monthly performance..."):
    monthly_fig = analytics.generate_monthly_performance()
    st.plotly_chart(monthly_fig, use_container_width=True)

# Setup Performance Table
st.header("🎯 Setup Performance Analysis")
with st.spinner("Loading setup data..."):
    setup_data = analytics.get_setup_performance()

if setup_data:
    setup_df = pd.DataFrame(setup_data)
    
    # Format the DataFrame for better display
    setup_df['Total P&L'] = setup_df['total_pnl'].apply(lambda x: f"${x:,.2f}")
    setup_df['Win Rate'] = setup_df['win_rate'].apply(lambda x: f"{x}%")
    setup_df['Avg P&L'] = setup_df['avg_pnl'].apply(lambda x: f"${x:,.2f}")
    setup_df['Avg R-Multiple'] = setup_df['avg_r_multiple'].apply(lambda x: f"{x:.2f}R")
    
    # Display table
    display_df = setup_df[['setup_name', 'total_trades', 'Win Rate', 'Total P&L', 'Avg P&L', 'Avg R-Multiple', 'profit_factor']]
    display_df.columns = ['Setup', 'Trades', 'Win Rate', 'Total P&L', 'Avg P&L', 'Avg R-Multiple', 'Profit Factor']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No setup performance data available. Start trading and assign setups to your trades!")

# Trade Statistics
st.header("📋 Trade Statistics")

if summary['overview']['total_trades'] > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Trade Distribution")
        distribution_data = {
            'Winning Trades': summary['overview']['winning_trades'],
            'Losing Trades': summary['overview']['losing_trades'],
            'Break-even Trades': summary['overview']['break_even_trades']
        }
        
        if sum(distribution_data.values()) > 0:
            distribution_fig = go.Figure(data=[
                go.Pie(
                    labels=list(distribution_data.keys()),
                    values=list(distribution_data.values()),
                    hole=0.4,
                    marker_colors=['#00CC96', '#EF553B', '#FFA15A']
                )
            ])
            distribution_fig.update_layout(
                title="Trade Outcome Distribution",
                showlegend=True,
                height=400
            )
            st.plotly_chart(distribution_fig, use_container_width=True)
    
    with col2:
        st.subheader("💡 Key Insights")
        
        # Generate insights based on performance
        insights = []
        
        if summary['overview']['win_rate'] >= 60:
            insights.append("🎯 Excellent win rate! You're selecting good trades.")
        elif summary['overview']['win_rate'] >= 50:
            insights.append("✅ Good win rate. Focus on improving entry timing.")
        else:
            insights.append("⚠️ Low win rate. Review your setup criteria.")
        
        if summary['overview']['profit_factor'] != 'N/A' and float(summary['overview']['profit_factor']) >= 2:
            insights.append("💰 Strong profit factor indicates good risk management.")
        elif summary['overview']['profit_factor'] != 'N/A' and float(summary['overview']['profit_factor']) >= 1.5:
            insights.append("📈 Decent profit factor. Room for improvement.")
        else:
            insights.append("🔴 Low profit factor. Focus on cutting losses quickly.")
        
        if summary['risk_metrics']['avg_r_multiple'] >= 1:
            insights.append("🚀 Positive average R-multiple shows good risk/reward.")
        else:
            insights.append("⚡ Negative average R-multiple. Tighten stop losses or wider targets.")
        
        if summary['behavioral_metrics']['max_consecutive_losses'] >= 5:
            insights.append("🧠 High consecutive losses suggest emotional trading.")
        
        for insight in insights:
            st.write(insight)
        
        if not insights:
            st.write("📊 Keep trading to generate insights!")

else:
    st.info("No trades found for analysis. Start by adding some trades to see detailed analytics!")

# Export functionality
st.header("📤 Export Data")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Performance Summary"):
        # Convert summary to DataFrame for export
        summary_data = []
        for category, metrics in summary.items():
            if isinstance(metrics, dict):
                for metric, value in metrics.items():
                    summary_data.append({
                        'Category': category.replace('_', ' ').title(),
                        'Metric': metric.replace('_', ' ').title(),
                        'Value': value
                    })
        
        summary_df = pd.DataFrame(summary_data)
        csv = summary_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"trading_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("🎯 Export Setup Performance"):
        if setup_data:
            setup_export_df = pd.DataFrame(setup_data)
            csv = setup_export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"setup_performance_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No setup data to export")

with col3:
    if st.button("📈 Export All Data"):
        # This would export all trades with details
        st.info("Full data export feature coming soon!")

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Use the date filters to analyze performance over specific periods. Regular analysis helps identify patterns and improve trading performance.")
