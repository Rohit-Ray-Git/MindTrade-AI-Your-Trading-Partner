#!/usr/bin/env python3
"""
CSV Import Page for Historical Trading Data
Import and analyze complete trading history from CSV files
"""

import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.csv_importer import DeltaCSVImporter
from models.dal import TradeDAL
from utils.ai_integration import GeminiAI

def main():
    st.set_page_config(
        page_title="CSV Import - MindTrade AI",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Historical Data Import")
    st.markdown("Import your complete trading history from CSV files")
    
    # Sidebar navigation
    st.sidebar.title("📋 Import Steps")
    step = st.sidebar.radio(
        "Choose Step:",
        ["📥 Upload CSV", "📊 Analysis Results", "🤖 AI Assessment"]
    )
    
    if step == "📥 Upload CSV":
        csv_upload_section()
    elif step == "📊 Analysis Results":
        analysis_results_section()
    elif step == "🤖 AI Assessment":
        ai_assessment_section()

def csv_upload_section():
    """CSV upload and import section"""
    st.header("📥 Upload Trading History CSV")
    
    # Instructions
    with st.expander("📋 How to Export CSV from Delta Exchange", expanded=True):
        st.markdown("""
        **Steps to download your trading history:**
        
        1. **Login to Delta Exchange**
           - Go to https://www.delta.exchange/
           - Login to your account
        
        2. **Navigate to Trade History**
           - Go to **Account** → **Trade History**
           - Or directly: https://www.delta.exchange/app/orders/history
        
        3. **Export Data**
           - Select date range (recommend: All time)
           - Click **"Export"** or **"Download CSV"**
           - Save the CSV file to your computer
        
        4. **Upload Here**
           - Use the file uploader below
           - System will automatically detect format
        
        **Supported CSV formats:**
        - Trade fills/executions
        - Order history
        - Position history
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload your Delta Exchange trading history CSV file"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Save uploaded file temporarily
        temp_csv_path = f"temp_{uploaded_file.name}"
        with open(temp_csv_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Preview CSV
        st.subheader("👀 CSV Preview")
        try:
            df_preview = pd.read_csv(temp_csv_path, nrows=5)
            st.dataframe(df_preview)
            
            st.info(f"📊 File contains {len(pd.read_csv(temp_csv_path))} rows and {len(df_preview.columns)} columns")
            
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
            return
        
        # Import button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Import & Analyze Data", type="primary", use_container_width=True):
                import_and_analyze_csv(temp_csv_path)
        
        # Cleanup
        if os.path.exists(temp_csv_path):
            try:
                os.remove(temp_csv_path)
            except:
                pass

def import_and_analyze_csv(csv_file_path: str):
    """Import and analyze CSV data"""
    with st.spinner("🔄 Importing and analyzing your trading history..."):
        try:
            # Initialize importer
            importer = DeltaCSVImporter()
            
            # Process CSV
            result = importer.process_csv_file(csv_file_path)
            
            if result['success']:
                st.success(f"🎉 Successfully imported {result['imported_trades']} trades!")
                
                # Store results in session state
                st.session_state['import_result'] = result
                st.session_state['analysis_data'] = result['analysis']
                
                # Display summary
                display_import_summary(result)
                
                # Show next steps
                st.info("📊 Switch to 'Analysis Results' tab to view detailed analysis")
                
            else:
                st.error(f"❌ Import failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error during import: {str(e)}")

def display_import_summary(result: dict):
    """Display import summary"""
    st.subheader("📊 Import Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Trades Imported", result['imported_trades'])
    
    with col2:
        st.metric("📋 Total Rows", result['total_rows'])
    
    with col3:
        success_rate = (result['imported_trades'] / result['total_rows']) * 100
        st.metric("✅ Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        st.metric("📄 Report Generated", "✅" if result.get('report_file') else "❌")
    
    # Quick analysis preview
    analysis = result.get('analysis', {})
    
    if 'performance_analysis' in analysis:
        perf = analysis['performance_analysis']
        
        st.subheader("🎯 Quick Performance Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Total P&L", f"${perf.get('total_pnl', 0):,.2f}")
        
        with col2:
            st.metric("🎯 Win Rate", f"{perf.get('win_rate', 0):.1f}%")
        
        with col3:
            st.metric("📊 Profit Factor", f"{perf.get('profit_factor', 0):.2f}")

def analysis_results_section():
    """Display detailed analysis results"""
    st.header("📊 Detailed Trading Analysis")
    
    # Check if we have analysis data
    if 'analysis_data' not in st.session_state:
        st.warning("📥 No analysis data found. Please import a CSV file first.")
        return
    
    analysis = st.session_state['analysis_data']
    
    # Performance Analysis
    if 'performance_analysis' in analysis:
        display_performance_analysis(analysis['performance_analysis'])
    
    # Trading Patterns
    if 'direction_analysis' in analysis:
        display_direction_analysis(analysis['direction_analysis'])
    
    # Symbol Analysis
    if 'symbol_analysis' in analysis:
        display_symbol_analysis(analysis['symbol_analysis'])
    
    # Volume Analysis
    if 'volume_analysis' in analysis:
        display_volume_analysis(analysis['volume_analysis'])
    
    # Frequency Analysis
    if 'frequency_analysis' in analysis:
        display_frequency_analysis(analysis['frequency_analysis'])

def display_performance_analysis(perf: dict):
    """Display performance analysis"""
    st.subheader("💰 Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total P&L", f"${perf.get('total_pnl', 0):,.2f}")
        st.metric("Winning Trades", perf.get('winning_trades', 0))
        st.metric("Average Win", f"${perf.get('avg_win', 0):,.2f}")
        st.metric("Largest Win", f"${perf.get('largest_win', 0):,.2f}")
    
    with col2:
        st.metric("Win Rate", f"{perf.get('win_rate', 0):.1f}%")
        st.metric("Losing Trades", perf.get('losing_trades', 0))
        st.metric("Average Loss", f"${perf.get('avg_loss', 0):,.2f}")
        st.metric("Largest Loss", f"${perf.get('largest_loss', 0):,.2f}")
    
    # Profit Factor
    profit_factor = perf.get('profit_factor', 0)
    if profit_factor != float('inf'):
        st.metric("📊 Profit Factor", f"{profit_factor:.2f}")
        
        if profit_factor > 1.5:
            st.success("🎉 Excellent profit factor! You're consistently profitable.")
        elif profit_factor > 1.0:
            st.info("👍 Good profit factor. Room for improvement.")
        else:
            st.warning("⚠️ Profit factor below 1.0. Consider reviewing your strategy.")

def display_direction_analysis(direction: dict):
    """Display trading direction analysis"""
    st.subheader("📈 Trading Direction Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Direction metrics
        st.metric("Long Trades", direction.get('long_trades', 0))
        st.metric("Short Trades", direction.get('short_trades', 0))
    
    with col2:
        # Create pie chart
        labels = ['Long', 'Short']
        values = [direction.get('long_trades', 0), direction.get('short_trades', 0)]
        
        fig = px.pie(
            values=values,
            names=labels,
            title="Long vs Short Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_symbol_analysis(symbols: dict):
    """Display symbol trading analysis"""
    st.subheader("🎯 Symbol Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Symbols Traded", symbols.get('total_symbols', 0))
        st.metric("Avg Trades per Symbol", f"{symbols.get('avg_trades_per_symbol', 0):.1f}")
    
    with col2:
        # Most traded symbols
        most_traded = symbols.get('most_traded_symbols', {})
        if most_traded:
            st.write("**Most Traded Symbols:**")
            for symbol, count in list(most_traded.items())[:5]:
                st.write(f"• {symbol}: {count} trades")

def display_volume_analysis(volume: dict):
    """Display volume analysis"""
    st.subheader("📊 Volume Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Quantity", f"{volume.get('total_quantity', 0):,.2f}")
        st.metric("Average Quantity", f"{volume.get('avg_quantity', 0):.2f}")
    
    with col2:
        st.metric("Max Quantity", f"{volume.get('max_quantity', 0):,.2f}")
        st.metric("Min Quantity", f"{volume.get('min_quantity', 0):.2f}")

def display_frequency_analysis(freq: dict):
    """Display trading frequency analysis"""
    st.subheader("⏰ Trading Frequency Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Avg Trades per Day", f"{freq.get('avg_trades_per_day', 0):.1f}")
        st.metric("Max Trades per Day", freq.get('max_trades_per_day', 0))
        st.metric("Total Trading Days", freq.get('total_trading_days', 0))
    
    with col2:
        st.metric("Min Trades per Day", freq.get('min_trades_per_day', 0))
        st.metric("Most Active Day", freq.get('most_active_day', 'N/A'))

def ai_assessment_section():
    """AI assessment of trading patterns"""
    st.header("🤖 AI Trading Assessment")
    
    if 'analysis_data' not in st.session_state:
        st.warning("📥 No analysis data found. Please import a CSV file first.")
        return
    
    st.markdown("Get AI-powered insights into your trading patterns and performance.")
    
    if st.button("🚀 Generate AI Assessment", type="primary"):
        generate_ai_assessment()

def generate_ai_assessment():
    """Generate AI assessment of trading data"""
    with st.spinner("🤖 AI is analyzing your trading patterns..."):
        try:
            analysis = st.session_state['analysis_data']
            
            # Initialize AI
            ai = GeminiAI()
            
            # Prepare data for AI analysis
            assessment_prompt = f"""
            Analyze this trader's historical performance data and provide insights:
            
            PERFORMANCE DATA:
            {json.dumps(analysis, indent=2)}
            
            Please provide:
            1. Trading Style Assessment (scalper, swing trader, position trader)
            2. Strengths and Weaknesses
            3. Risk Management Analysis
            4. Performance Insights
            5. Specific Recommendations for Improvement
            6. Psychological Trading Patterns
            
            Format as a comprehensive trading assessment report.
            """
            
            # Get AI assessment
            assessment = ai.analyze_psychology_with_image(assessment_prompt, None)
            
            # Display assessment
            if assessment:
                st.subheader("🎯 AI Trading Assessment Report")
                
                # Parse and display assessment
                if isinstance(assessment, dict):
                    for key, value in assessment.items():
                        if key != 'raw_text':
                            st.write(f"**{key.replace('_', ' ').title()}:**")
                            st.write(value)
                            st.write("---")
                else:
                    st.write(assessment)
                
                # Store assessment
                st.session_state['ai_assessment'] = assessment
                
                st.success("✅ AI assessment complete!")
                
            else:
                st.error("❌ Failed to generate AI assessment")
                
        except Exception as e:
            st.error(f"❌ Error generating AI assessment: {str(e)}")

if __name__ == "__main__":
    main()
