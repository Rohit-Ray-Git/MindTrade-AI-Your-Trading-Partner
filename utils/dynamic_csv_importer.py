#!/usr/bin/env python3
"""
Dynamic CSV Importer for Trading Data
Analyzes CSV structure and creates database schema dynamically
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database import init_db, get_db
from models.models import Trade, Setup
from models.dal import TradeDAL, SetupDAL

class DynamicCSVImporter:
    """Dynamic CSV importer that creates schema based on CSV structure"""
    
    def __init__(self):
        # Initialize database
        init_db()
        
        print("🔄 Dynamic CSV Importer")
        print("=" * 50)
    
    def analyze_csv_structure(self, csv_file_path: str) -> Dict[str, Any]:
        """Analyze CSV structure and infer data types"""
        print(f"\n🔍 Analyzing CSV structure: {csv_file_path}")
        
        try:
            # Read CSV with pandas
            df = pd.read_csv(csv_file_path)
            
            print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
            print(f"📋 Columns: {list(df.columns)}")
            
            # Analyze each column
            column_analysis = {}
            
            for col in df.columns:
                col_analysis = self._analyze_column(df[col], col)
                column_analysis[col] = col_analysis
                print(f"   📊 {col}: {col_analysis['type']} - {col_analysis['description']}")
            
            # Sample data
            print(f"\n📊 Sample data (first 3 rows):")
            print(df.head(3).to_string())
            
            return {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': column_analysis,
                'sample_data': df.head(5).to_dict('records'),
                'dataframe': df
            }
            
        except Exception as e:
            print(f"❌ Error analyzing CSV: {str(e)}")
            return {}
    
    def _analyze_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Analyze a single column to determine its type and characteristics"""
        
        # Remove NaN values for analysis
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {
                'type': 'unknown',
                'description': 'Empty column',
                'unique_values': 0,
                'sample_values': []
            }
        
        # Try to detect data type
        column_type = 'string'
        description = f"Text data with {len(clean_series)} non-null values"
        
        # Check if it's numeric
        try:
            numeric_series = pd.to_numeric(clean_series, errors='coerce')
            if not numeric_series.isna().all():
                column_type = 'numeric'
                description = f"Numeric data: min={numeric_series.min():.2f}, max={numeric_series.max():.2f}, mean={numeric_series.mean():.2f}"
        except:
            pass
        
        # Check if it's datetime
        try:
            datetime_series = pd.to_datetime(clean_series, errors='coerce')
            if not datetime_series.isna().all():
                column_type = 'datetime'
                description = f"Date/time data from {datetime_series.min()} to {datetime_series.max()}"
        except:
            pass
        
        # Check if it's boolean
        if clean_series.dtype == bool or clean_series.isin([True, False, 'true', 'false', '1', '0']).all():
            column_type = 'boolean'
            description = f"Boolean data with {clean_series.value_counts().to_dict()}"
        
        # Analyze unique values
        unique_count = clean_series.nunique()
        sample_values = clean_series.head(5).tolist()
        
        return {
            'type': column_type,
            'description': description,
            'unique_values': unique_count,
            'sample_values': sample_values,
            'null_count': series.isna().sum(),
            'null_percentage': (series.isna().sum() / len(series)) * 100
        }
    
    def create_dynamic_schema(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create database schema based on CSV analysis"""
        print(f"\n🏗️ Creating dynamic schema...")
        
        schema = {
            'table_name': 'dynamic_trades',
            'columns': {},
            'mappings': {}
        }
        
        # Map CSV columns to database columns
        for col_name, col_analysis in analysis['columns'].items():
            db_col_name = self._normalize_column_name(col_name)
            
            # Determine SQLAlchemy column type
            if col_analysis['type'] == 'numeric':
                col_type = Float
            elif col_analysis['type'] == 'datetime':
                col_type = DateTime
            elif col_analysis['type'] == 'boolean':
                col_type = Boolean
            else:
                col_type = String(500)  # Default to string with reasonable length
            
            schema['columns'][db_col_name] = {
                'original_name': col_name,
                'type': col_type,
                'analysis': col_analysis
            }
            
            schema['mappings'][col_name] = db_col_name
            
            print(f"   📋 {col_name} → {db_col_name} ({col_type.__name__})")
        
        return schema
    
    def _normalize_column_name(self, column_name: str) -> str:
        """Normalize column name for database use"""
        # Remove special characters and spaces
        normalized = ''.join(c for c in column_name if c.isalnum() or c == '_')
        # Ensure it starts with a letter
        if normalized and not normalized[0].isalpha():
            normalized = 'col_' + normalized
        # Ensure it's not empty
        if not normalized:
            normalized = 'unnamed_column'
        return normalized.lower()
    
    def create_dynamic_table(self, schema: Dict[str, Any]) -> Table:
        """Create SQLAlchemy table dynamically"""
        print(f"\n🗄️ Creating dynamic table: {schema['table_name']}")
        
        metadata = MetaData()
        
        # Create columns
        columns = []
        for col_name, col_info in schema['columns'].items():
            column = Column(col_name, col_info['type'], nullable=True)
            columns.append(column)
        
        # Create table
        table = Table(schema['table_name'], metadata, *columns)
        
        return table
    
    def import_to_dynamic_table(self, df: pd.DataFrame, schema: Dict[str, Any]) -> int:
        """Import data to dynamic table"""
        print(f"\n💾 Importing data to dynamic table...")
        
        try:
            # Create SQLite connection
            db_path = "dynamic_trades.db"
            engine = create_engine(f'sqlite:///{db_path}')
            
            # Create table
            table = self.create_dynamic_table(schema)
            table.create(engine, checkfirst=True)
            
            # Prepare data for import
            import_data = []
            for _, row in df.iterrows():
                row_dict = {}
                for col_name, value in row.items():
                    if col_name in schema['mappings']:
                        db_col_name = schema['mappings'][col_name]
                        row_dict[db_col_name] = value
                import_data.append(row_dict)
            
            # Insert data
            with engine.connect() as conn:
                result = conn.execute(table.insert(), import_data)
                conn.commit()
            
            print(f"✅ Successfully imported {len(import_data)} rows to dynamic table")
            return len(import_data)
            
        except Exception as e:
            print(f"❌ Error importing to dynamic table: {str(e)}")
            return 0
    
    def convert_to_trades(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert CSV data to trade format using intelligent mapping"""
        print(f"\n🔄 Converting to trade format...")
        
        trades = []
        default_setup_id = self._get_or_create_default_setup()
        
        # Intelligent column mapping
        mappings = self._intelligent_column_mapping(analysis['columns'])
        print(f"🎯 Intelligent mappings: {mappings}")
        
        for index, row in df.iterrows():
            try:
                trade_data = self._extract_trade_data(row, mappings, index)
                trade_data['setup_id'] = default_setup_id
                trades.append(trade_data)
                
            except Exception as e:
                print(f"⚠️ Error processing row {index}: {str(e)}")
                continue
        
        print(f"✅ Converted {len(trades)} trades")
        return trades
    
    def _intelligent_column_mapping(self, columns: Dict[str, Any]) -> Dict[str, str]:
        """Intelligently map CSV columns to trade fields"""
        mappings = {}
        
        # Common patterns for different trade fields
        patterns = {
            'symbol': ['contract', 'symbol', 'instrument', 'product', 'pair', 'ticker'],
            'side': ['side', 'direction', 'type', 'buy_sell', 'order_side'],
            'quantity': ['qty', 'quantity', 'size', 'amount', 'volume'],
            'price': ['price', 'exec_price', 'execution_price', 'fill_price', 'avg_price'],
            'timestamp': ['time', 'timestamp', 'created_at', 'execution_time', 'date'],
            'pnl': ['pnl', 'profit_loss', 'pl', 'realised', 'realized', 'profit'],
            'fees': ['fees', 'commission', 'cost', 'fee', 'trading_fee'],
            'order_id': ['order_id', 'id', 'trade_id', 'fill_id', 'order'],
            'status': ['status', 'state', 'order_status', 'filled']
        }
        
        for field, patterns_list in patterns.items():
            for col_name in columns.keys():
                col_lower = col_name.lower()
                for pattern in patterns_list:
                    if pattern in col_lower:
                        mappings[field] = col_name
                        break
                if field in mappings:
                    break
        
        return mappings
    
    def _extract_trade_data(self, row: pd.Series, mappings: Dict[str, str], index: int) -> Dict[str, Any]:
        """Extract trade data from a row using mappings"""
        
        # Helper function to safely get value
        def get_value(field, default=None):
            if field in mappings and mappings[field] in row:
                value = row[mappings[field]]
                if pd.isna(value):
                    return default
                return value
            return default
        
        # Extract basic trade data
        symbol = get_value('symbol', 'UNKNOWN')
        side = get_value('side', 'long')
        quantity = float(get_value('quantity', 0))
        price = float(get_value('price', 0))
        timestamp = get_value('timestamp', datetime.now())
        pnl = float(get_value('pnl', 0))
        fees = float(get_value('fees', 0))
        order_id = str(get_value('order_id', f"dynamic_{index}"))
        status = get_value('status', 'unknown')
        
        # Normalize side
        if side and isinstance(side, str):
            side = side.lower().strip()
            if side in ['buy', 'b']:
                side = 'long'
            elif side in ['sell', 's']:
                side = 'short'
        
        # Parse timestamp
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = pd.to_datetime(timestamp)
            except:
                timestamp = datetime.now()
        
        trade_data = {
            'symbol': symbol,
            'direction': side,
            'quantity': quantity,
            'entry_price': price,
            'exit_price': price,  # Same as entry for now
            'stop_price': price * 0.98,  # Estimate
            'account_equity': 10000.0,
            'risk_percent': 2.0,
            'pnl': pnl,
            'r_multiple': 0.0,
            'trade_time': timestamp,
            'entry_time': timestamp,
            'exit_time': timestamp,
            'source': 'dynamic_csv_import',
            'exchange': 'Dynamic Import',
            'external_id': order_id,
            'fees': fees,
            'logic': f'Dynamically imported - Status: {status}',
            'notes': f'Dynamically imported from CSV on {datetime.now().strftime("%Y-%m-%d")}. Original data: {dict(row)}'
        }
        
        # Calculate R-multiple if we have P&L
        if trade_data['pnl'] != 0 and trade_data['entry_price'] > 0:
            risk_amount = trade_data['entry_price'] * trade_data['quantity'] * (trade_data['risk_percent'] / 100)
            if risk_amount > 0:
                trade_data['r_multiple'] = trade_data['pnl'] / risk_amount
        
        return trade_data
    
    def _get_or_create_default_setup(self) -> int:
        """Get or create default setup for imported trades"""
        try:
            db = next(get_db())
            
            # Look for existing "Dynamic Import" setup
            existing_setup = db.query(Setup).filter(Setup.name == "Dynamic Import").first()
            
            if existing_setup:
                return existing_setup.id
            
            # Create new setup
            new_setup = Setup(
                name="Dynamic Import",
                description="Default setup for trades imported using dynamic CSV analysis."
            )
            
            db.add(new_setup)
            db.commit()
            db.refresh(new_setup)
            
            return new_setup.id
        except Exception as e:
            print(f"⚠️ Error creating setup: {str(e)}")
            return 1
    
    def import_to_database(self, trades: List[Dict[str, Any]]) -> int:
        """Import trades to main database"""
        print(f"\n💾 Importing {len(trades)} trades to main database...")
        
        try:
            db = next(get_db())
            imported_count = 0
            
            for trade_data in trades:
                try:
                    # Check if trade already exists
                    existing_trade = db.query(Trade).filter(
                        Trade.external_id == trade_data['external_id'],
                        Trade.source == 'dynamic_csv_import'
                    ).first()
                    
                    if existing_trade:
                        print(f"⚠️ Skipping duplicate trade: {trade_data['external_id']}")
                        continue
                    
                    # Create new trade
                    new_trade = Trade(**trade_data)
                    db.add(new_trade)
                    imported_count += 1
                    
                except Exception as e:
                    print(f"❌ Error importing trade: {str(e)}")
                    continue
            
            db.commit()
            print(f"✅ Successfully imported {imported_count} trades to main database")
            return imported_count
            
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return 0
    
    def generate_analysis_report(self, analysis: Dict[str, Any], imported_count: int) -> str:
        """Generate comprehensive analysis report"""
        print(f"\n📄 Generating analysis report...")
        
        report = {
            'import_summary': {
                'timestamp': datetime.now().isoformat(),
                'imported_trades': imported_count,
                'total_rows': analysis['total_rows'],
                'total_columns': analysis['total_columns'],
                'status': 'success' if imported_count > 0 else 'failed'
            },
            'column_analysis': analysis['columns'],
            'sample_data': analysis['sample_data']
        }
        
        # Save report
        report_filename = f"dynamic_csv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Report saved: {report_filename}")
        return report_filename
    
    def process_csv_file(self, csv_file_path: str) -> Dict[str, Any]:
        """Complete dynamic CSV processing workflow"""
        print(f"\n🚀 Starting Dynamic CSV Import Process")
        print("=" * 50)
        
        # Step 1: Analyze CSV structure
        analysis = self.analyze_csv_structure(csv_file_path)
        if not analysis:
            return {'success': False, 'error': 'Could not analyze CSV structure'}
        
        # Step 2: Create dynamic schema
        schema = self.create_dynamic_schema(analysis)
        
        # Step 3: Import to dynamic table (optional)
        dynamic_import_count = self.import_to_dynamic_table(analysis['dataframe'], schema)
        
        # Step 4: Convert to trades
        trades = self.convert_to_trades(analysis['dataframe'], analysis)
        
        # Step 5: Import to main database
        imported_count = self.import_to_database(trades)
        
        # Step 6: Generate report
        report_file = self.generate_analysis_report(analysis, imported_count)
        
        return {
            'success': True,
            'imported_trades': imported_count,
            'dynamic_import_count': dynamic_import_count,
            'total_rows': analysis['total_rows'],
            'total_columns': analysis['total_columns'],
            'column_analysis': analysis['columns'],
            'schema': schema,
            'report_file': report_file
        }

def main():
    """Main function for testing"""
    importer = DynamicCSVImporter()
    
    # Example usage
    csv_file = input("Enter path to CSV file: ").strip()
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    result = importer.process_csv_file(csv_file)
    
    if result['success']:
        print(f"\n🎉 Dynamic CSV Import Successful!")
        print(f"📊 Imported: {result['imported_trades']} trades")
        print(f"📋 Analyzed: {result['total_columns']} columns")
        print(f"📄 Report: {result['report_file']}")
    else:
        print(f"\n❌ Dynamic CSV Import Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
