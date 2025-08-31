"""
Dynamic CSV Import Page
Analyzes CSV structure and creates database schema dynamically
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import tempfile
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from models.database import init_db
from utils.dynamic_csv_importer import DynamicCSVImporter

# Page config
st.set_page_config(
    page_title="Dynamic CSV Import",
    page_icon="🔄",
    layout="wide"
)

# Initialize
init_db()

st.title("🔄 Dynamic CSV Import")

st.markdown("""
### 🧠 Intelligent CSV Analysis & Import

This page uses **AI-powered analysis** to automatically:
- **Analyze your CSV structure** and detect data types
- **Create database schema** on-the-fly based on your data
- **Intelligently map columns** to trading fields
- **Import all your data** without predefined constraints

**Perfect for any CSV format!** 🎯
""")

# File upload section
st.subheader("📁 Upload Your CSV File")

uploaded_file = st.file_uploader(
    "Upload any CSV file with trading data",
    type=['csv'],
    help="Upload any CSV file - the system will analyze and adapt automatically"
)

if uploaded_file:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_csv_path = tmp_file.name
    
    try:
        # Initialize dynamic importer
        importer = DynamicCSVImporter()
        
        # Analyze CSV structure
        st.subheader("🔍 CSV Structure Analysis")
        
        with st.spinner("Analyzing CSV structure..."):
            analysis = importer.analyze_csv_structure(temp_csv_path)
        
        if analysis:
            st.success(f"✅ Analyzed {analysis['total_rows']} rows with {analysis['total_columns']} columns")
            
            # Display column analysis
            st.subheader("📊 Column Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Column Details:**")
                for col_name, col_info in analysis['columns'].items():
                    with st.expander(f"📊 {col_name}"):
                        st.write(f"**Type:** {col_info['type']}")
                        st.write(f"**Description:** {col_info['description']}")
                        st.write(f"**Unique Values:** {col_info['unique_values']}")
                        st.write(f"**Null Values:** {col_info['null_count']} ({col_info['null_percentage']:.1f}%)")
                        
                        if col_info['sample_values']:
                            st.write("**Sample Values:**")
                            for val in col_info['sample_values']:
                                st.write(f"  - {val}")
            
            with col2:
                st.markdown("**📈 Data Overview:**")
                st.metric("Total Rows", analysis['total_rows'])
                st.metric("Total Columns", analysis['total_columns'])
                
                # Show sample data
                st.markdown("**📊 Sample Data:**")
                sample_df = pd.DataFrame(analysis['sample_data'])
                st.dataframe(sample_df, use_container_width=True)
            
            # Import options
            st.subheader("🚀 Import Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                import_to_dynamic = st.checkbox(
                    "Create Dynamic Table",
                    value=True,
                    help="Create a separate table with your exact CSV structure"
                )
            
            with col2:
                import_to_trades = st.checkbox(
                    "Convert to Trades",
                    value=True,
                    help="Convert data to trade format for analysis"
                )
            
            with col3:
                generate_report = st.checkbox(
                    "Generate Report",
                    value=True,
                    help="Create detailed analysis report"
                )
            
            # Import button
            if st.button("🚀 Start Dynamic Import", type="primary"):
                st.subheader("🔄 Processing Import...")
                
                with st.spinner("Processing dynamic import..."):
                    result = importer.process_csv_file(temp_csv_path)
                
                if result['success']:
                    st.success("🎉 Dynamic Import Successful!")
                    
                    # Display results
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Trades Imported", result['imported_trades'])
                    
                    with col2:
                        st.metric("Dynamic Table Rows", result['dynamic_import_count'])
                    
                    with col3:
                        st.metric("Total CSV Rows", result['total_rows'])
                    
                    with col4:
                        st.metric("Columns Analyzed", result['total_columns'])
                    
                    # Show intelligent mappings
                    if 'schema' in result:
                        st.subheader("🎯 Intelligent Column Mappings")
                        
                        mappings = result['schema']['mappings']
                        st.markdown("**Column Mappings:**")
                        for original, normalized in mappings.items():
                            st.write(f"  - `{original}` → `{normalized}`")
                    
                    # Show detailed analysis
                    st.subheader("📊 Detailed Analysis")
                    
                    # Column type distribution
                    type_counts = {}
                    for col_info in result['column_analysis'].values():
                        col_type = col_info['type']
                        type_counts[col_type] = type_counts.get(col_type, 0) + 1
                    
                    if type_counts:
                        st.markdown("**Data Type Distribution:**")
                        for col_type, count in type_counts.items():
                            st.write(f"  - {col_type}: {count} columns")
                    
                    # Show report file
                    if 'report_file' in result:
                        st.markdown(f"**📄 Analysis Report:** {result['report_file']}")
                        
                        # Download report
                        with open(result['report_file'], 'r') as f:
                            report_content = f.read()
                        
                        st.download_button(
                            label="📥 Download Analysis Report",
                            data=report_content,
                            file_name=result['report_file'],
                            mime="application/json"
                        )
                    
                    # Next steps
                    st.subheader("🎯 Next Steps")
                    st.markdown("""
                    Your data has been successfully imported! You can now:
                    
                    1. **📈 View Analytics** - Go to Analytics Dashboard to see your trading performance
                    2. **🔧 Enhance Trades** - Use Trade Enhancer to add detailed logic and psychology
                    3. **🧠 Import Psychology** - Add your psychology notes for comprehensive analysis
                    4. **🤖 Get AI Coaching** - Receive personalized trading insights
                    """)
                    
                else:
                    st.error(f"❌ Import Failed: {result.get('error', 'Unknown error')}")
        
        else:
            st.error("❌ Could not analyze CSV structure")
    
    except Exception as e:
        st.error(f"❌ Error processing CSV: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)

# Information section
st.markdown("---")
st.subheader("💡 How Dynamic Import Works")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🔍 Smart Analysis:**
    - Automatically detects data types (numeric, datetime, text, boolean)
    - Analyzes column patterns and relationships
    - Identifies trading-related fields intelligently
    - Handles missing data and edge cases
    """)

with col2:
    st.markdown("""
    **🏗️ Dynamic Schema:**
    - Creates database tables based on your CSV structure
    - Normalizes column names for database compatibility
    - Preserves all your original data
    - Maps to trading fields automatically
    """)

# Benefits
st.subheader("✨ Benefits of Dynamic Import")

benefits_col1, benefits_col2, benefits_col3 = st.columns(3)

with benefits_col1:
    st.markdown("""
    **🎯 Universal Compatibility**
    - Works with any CSV format
    - No predefined column requirements
    - Handles custom trading data
    - Supports multiple exchanges
    """)

with benefits_col2:
    st.markdown("""
    **🧠 Intelligent Mapping**
    - AI-powered column detection
    - Automatic data type inference
    - Smart trading field mapping
    - Preserves data integrity
    """)

with benefits_col3:
    st.markdown("""
    **📊 Complete Analysis**
    - Detailed data structure report
    - Sample data preview
    - Statistical analysis
    - Export capabilities
    """)

# Example formats
st.subheader("📋 Supported CSV Formats")

st.markdown("""
The dynamic importer works with **any CSV format**. Here are some examples:

**Delta Exchange:**
```
Time, Contract, Qty, Side, Exec.Price, P&L, Fees
2024-01-01, BTC-PERP, 0.1, Buy, 45000, 150, 2.5
```

**Binance:**
```
Date, Symbol, Side, Price, Amount, Fee, Realized PnL
2024-01-01, BTCUSDT, BUY, 45000, 0.1, 2.5, 0
```

**Custom Format:**
```
timestamp, instrument, direction, quantity, execution_price, profit_loss
2024-01-01 10:30, ETH-PERP, long, 1.5, 2500, 75.50
```

**Any other format you have!** 🎯
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <strong>🔄 Dynamic CSV Import</strong> - Intelligent analysis for any trading data format<br>
    <small>Powered by AI-driven schema detection and intelligent mapping</small>
</div>
""", unsafe_allow_html=True)
