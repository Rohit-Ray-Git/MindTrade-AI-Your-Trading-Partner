#!/usr/bin/env python3
"""
CSV Importer for Delta Exchange Trading History
Import complete trading history from CSV file for AI analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os
from sqlalchemy.orm import Session
from models.database import get_db, init_db
from models.models import Trade, Setup
from models.dal import TradeDAL, SetupDAL

class DeltaCSVImporter:
    """Import and process Delta Exchange CSV trading data"""
    
    def __init__(self):
        # Initialize database
        init_db()
        
        print("📊 Delta Exchange CSV Importer")
        print("=" * 50)
    
    def detect_csv_format(self, csv_file_path: str) -> Dict[str, str]:
        """Detect CSV format and column mappings"""
        print(f"\n🔍 Analyzing CSV format: {csv_file_path}")
        
        try:
            # Read first few rows to detect format
            df_sample = pd.read_csv(csv_file_path, nrows=5)
            columns = df_sample.columns.tolist()
            
            print(f"📋 Detected columns: {columns}")
            
            # Delta Exchange CSV column patterns (updated for your format)
            column_mappings = {
                'symbol': self._find_column(columns, ['contract', 'symbol', 'instrument', 'product', 'pair']),
                'side': self._find_column(columns, ['side', 'direction', 'type', 'buy_sell']),
                'quantity': self._find_column(columns, ['qty', 'quantity', 'size', 'amount']),
                'exec_price': self._find_column(columns, ['exec. price', 'exec_price', 'execution_price', 'price', 'fill_price', 'avg_price']),
                'order_price': self._find_column(columns, ['order price', 'order_price', 'limit_price']),
                'stop_price': self._find_column(columns, ['stop price', 'stop_price', 'stop_loss']),
                'timestamp': self._find_column(columns, ['time', 'timestamp', 'created_at', 'execution_time', 'date']),
                'pnl': self._find_column(columns, ['realised p.', 'realised p&l', 'realised_pnl', 'realized_pnl', 'pnl', 'profit_loss', 'pl', 'realised p']),
                'fees': self._find_column(columns, ['trading fe', 'trading_fee', 'fees', 'commission', 'cost', 'fee']),
                'order_id': self._find_column(columns, ['order id', 'order_id', 'id', 'trade_id', 'fill_id']),
                'client_order': self._find_column(columns, ['client orde', 'client_order', 'client_id']),
                'order_type': self._find_column(columns, ['order type', 'order_type', 'type']),
                'status': self._find_column(columns, ['status', 'state', 'order_status', 'filled/remaining']),
                'explanation': self._find_column(columns, ['explanatio', 'explanation', 'notes', 'comment']),
                'cashflow': self._find_column(columns, ['cashflow', 'cash_flow', 'net_amount']),
                'order_value': self._find_column(columns, ['order valu', 'order_value', 'total_value'])
            }
            
            print(f"🎯 Column mappings detected:")
            for key, value in column_mappings.items():
                status = "✅" if value else "❌"
                print(f"   {status} {key}: {value}")
            
            return column_mappings
            
        except Exception as e:
            print(f"❌ Error analyzing CSV: {str(e)}")
            return {}
    
    def _find_column(self, columns: List[str], patterns: List[str]) -> Optional[str]:
        """Find column name matching patterns"""
        columns_lower = [col.lower() for col in columns]
        
        for pattern in patterns:
            for i, col in enumerate(columns_lower):
                if pattern.lower() in col:
                    return columns[i]
        
        return None
    
    def load_csv_data(self, csv_file_path: str, column_mappings: Dict[str, str]) -> pd.DataFrame:
        """Load and clean CSV data"""
        print(f"\n📥 Loading CSV data...")
        
        try:
            df = pd.read_csv(csv_file_path)
            print(f"✅ Loaded {len(df)} rows")
            print(f"📋 Original columns: {list(df.columns)}")
            
            # Show sample data for debugging
            print(f"📊 Sample data (first 2 rows):")
            print(df.head(2).to_string())
            
            # Rename columns based on mappings
            rename_map = {v: k for k, v in column_mappings.items() if v is not None}
            print(f"🔄 Rename mapping: {rename_map}")
            
            # Debug: Show data before renaming
            print(f"📊 Data before renaming - Shape: {df.shape}")
            print(f"📊 Sample data before renaming:")
            print(df.head(2).to_string())
            
            # Rename columns
            df = df.rename(columns=rename_map)
            
            # Debug: Show data after renaming
            print(f"📊 Data after renaming - Shape: {df.shape}")
            print(f"📊 Sample data after renaming:")
            print(df.head(2).to_string())
            
            print(f"📋 Available columns after renaming: {list(df.columns)}")
            
            # Clean and process data
            df = self._clean_data(df)
            
            print(f"✅ Cleaned data: {len(df)} valid rows")
            return df
            
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return pd.DataFrame()
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Store data as-is without cleaning"""
        print("📦 Storing data as-is (no cleaning)...")
        
        original_count = len(df)
        print(f"✅ Keeping all {original_count} rows without modification")
        
        # Just normalize side values for consistency (optional)
        if 'side' in df.columns:
            print(f"🔄 Normalizing side values...")
            df['side'] = df['side'].str.lower().str.strip()
            df['side'] = df['side'].map({'buy': 'long', 'sell': 'short', 'long': 'long', 'short': 'short'})
            print(f"✅ Side values normalized")
        
        print(f"✅ Data stored as-is: {len(df)} rows")
        return df
    

    
    def analyze_trading_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading patterns from historical data"""
        print(f"\n📊 Analyzing trading patterns...")
        
        analysis = {}
        
        try:
            # Basic statistics
            total_trades = len(df)
            analysis['total_trades'] = total_trades
            
            # Date range
            if 'timestamp' in df.columns:
                try:
                    # Convert timestamp to datetime for analysis
                    df_temp = df.copy()
                    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'], errors='coerce')
                    df_temp = df_temp.dropna(subset=['timestamp'])
                    
                    if len(df_temp) > 0:
                        date_range = {
                            'start_date': df_temp['timestamp'].min().strftime('%Y-%m-%d'),
                            'end_date': df_temp['timestamp'].max().strftime('%Y-%m-%d'),
                            'trading_days': (df_temp['timestamp'].max() - df_temp['timestamp'].min()).days
                        }
                        analysis['date_range'] = date_range
                except Exception as e:
                    print(f"⚠️ Could not analyze date range: {str(e)}")
            
            # Trading direction analysis
            if 'side' in df.columns:
                side_counts = df['side'].value_counts()
                analysis['direction_analysis'] = {
                    'long_trades': int(side_counts.get('long', 0)),
                    'short_trades': int(side_counts.get('short', 0)),
                    'long_percentage': float(side_counts.get('long', 0) / total_trades * 100),
                    'short_percentage': float(side_counts.get('short', 0) / total_trades * 100)
                }
            
            # Symbol analysis
            if 'symbol' in df.columns:
                symbol_counts = df['symbol'].value_counts()
                analysis['symbol_analysis'] = {
                    'most_traded_symbols': symbol_counts.head(10).to_dict(),
                    'total_symbols': len(symbol_counts),
                    'avg_trades_per_symbol': float(total_trades / len(symbol_counts))
                }
            
            # Volume analysis
            if 'quantity' in df.columns:
                analysis['volume_analysis'] = {
                    'total_quantity': float(df['quantity'].sum()),
                    'avg_quantity': float(df['quantity'].mean()),
                    'max_quantity': float(df['quantity'].max()),
                    'min_quantity': float(df['quantity'].min())
                }
            
            # P&L analysis (if available)
            if 'pnl' in df.columns:
                winning_trades = df[df['pnl'] > 0]
                losing_trades = df[df['pnl'] < 0]
                
                analysis['performance_analysis'] = {
                    'total_pnl': float(df['pnl'].sum()),
                    'winning_trades': len(winning_trades),
                    'losing_trades': len(losing_trades),
                    'win_rate': float(len(winning_trades) / total_trades * 100),
                    'avg_win': float(winning_trades['pnl'].mean()) if len(winning_trades) > 0 else 0,
                    'avg_loss': float(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0,
                    'largest_win': float(df['pnl'].max()),
                    'largest_loss': float(df['pnl'].min()),
                    'profit_factor': float(winning_trades['pnl'].sum() / abs(losing_trades['pnl'].sum())) if len(losing_trades) > 0 else float('inf')
                }
            
            # Fees analysis
            if 'fees' in df.columns:
                analysis['fees_analysis'] = {
                    'total_fees': float(df['fees'].sum()),
                    'avg_fee_per_trade': float(df['fees'].mean())
                }
            
            # Trading frequency
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
                daily_trades = df.groupby('date').size()
                
                analysis['frequency_analysis'] = {
                    'avg_trades_per_day': float(daily_trades.mean()),
                    'max_trades_per_day': int(daily_trades.max()),
                    'min_trades_per_day': int(daily_trades.min()),
                    'most_active_day': str(daily_trades.idxmax()),
                    'total_trading_days': len(daily_trades)
                }
            
            print(f"✅ Analysis complete - {len(analysis)} categories analyzed")
            return analysis
            
        except Exception as e:
            print(f"❌ Error in analysis: {str(e)}")
            return {}
    
    def convert_to_internal_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert CSV data to internal trade format"""
        print(f"\n🔄 Converting to internal format...")
        
        trades = []
        default_setup_id = self._get_or_create_default_setup()
        
        for index, row in df.iterrows():
            try:
                # Safely convert values with error handling
                def safe_float(value, default=0.0):
                    if pd.isna(value) or value == '':
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                def safe_str(value, default=''):
                    if pd.isna(value) or value == '':
                        return default
                    return str(value)
                
                # Parse timestamp safely
                timestamp = row.get('timestamp', datetime.now())
                if isinstance(timestamp, str):
                    try:
                        timestamp = pd.to_datetime(timestamp, errors='coerce')
                        if pd.isna(timestamp):
                            timestamp = datetime.now()
                    except:
                        timestamp = datetime.now()
                
                # Extract trade data with safe conversion
                entry_price = safe_float(row.get('exec_price', row.get('order_price', 0)))
                exit_price = safe_float(row.get('exec_price', 0))
                quantity = safe_float(row.get('quantity', 0))
                pnl = safe_float(row.get('pnl', 0))
                fees = safe_float(row.get('fees', 0))
                stop_price = safe_float(row.get('stop_price', entry_price * 0.98))
                
                trade_data = {
                    'symbol': safe_str(row.get('symbol', 'UNKNOWN')),
                    'direction': safe_str(row.get('side', 'long')),
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'stop_price': stop_price,
                    'account_equity': 10000.0,
                    'risk_percent': 2.0,
                    'pnl': pnl,
                    'r_multiple': 0.0,
                    'trade_time': timestamp,
                    'entry_time': timestamp,
                    'exit_time': timestamp,
                    'source': 'csv_import',
                    'exchange': 'Delta Exchange',
                    'external_id': safe_str(row.get('order_id', f"csv_{index}")),
                    'fees': fees,
                    'logic': f'Imported from CSV - Order Type: {safe_str(row.get("order_type", "Unknown"))} - Status: {safe_str(row.get("status", "Unknown"))}',
                    'notes': f'Imported from Delta Exchange CSV on {datetime.now().strftime("%Y-%m-%d")}. {safe_str(row.get("explanation", ""))}',
                    'setup_id': default_setup_id
                }
                
                # Calculate R-multiple if we have P&L
                if trade_data['pnl'] != 0 and trade_data['entry_price'] > 0:
                    risk_amount = trade_data['entry_price'] * trade_data['quantity'] * (trade_data['risk_percent'] / 100)
                    if risk_amount > 0:
                        trade_data['r_multiple'] = trade_data['pnl'] / risk_amount
                
                trades.append(trade_data)
                
            except Exception as e:
                print(f"⚠️ Error processing row {index}: {str(e)}")
                continue
        
        print(f"✅ Converted {len(trades)} trades to internal format")
        return trades
    
    def _get_or_create_default_setup(self) -> int:
        """Get or create default setup for imported trades"""
        try:
            db = next(get_db())
            
            # Look for existing "CSV Import" setup
            existing_setup = db.query(Setup).filter(Setup.name == "CSV Import").first()
            
            if existing_setup:
                return existing_setup.id
            
            # Create new setup
            new_setup = Setup(
                name="CSV Import",
                description="Default setup for trades imported from CSV files. Historical trades imported from Delta Exchange CSV export."
            )
            
            db.add(new_setup)
            db.commit()
            db.refresh(new_setup)
            
            return new_setup.id
        except Exception as e:
            print(f"⚠️ Error creating setup: {str(e)}")
            return 1  # Return default setup ID
    
    def import_to_database(self, trades: List[Dict[str, Any]]) -> int:
        """Import trades to database"""
        print(f"\n💾 Importing {len(trades)} trades to database...")
        
        try:
            db = next(get_db())
            imported_count = 0
            
            for trade_data in trades:
                try:
                    # Check if trade already exists (by external_id)
                    existing_trade = db.query(Trade).filter(
                        Trade.external_id == trade_data['external_id'],
                        Trade.source == 'csv_import'
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
            print(f"✅ Successfully imported {imported_count} trades")
            return imported_count
            
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return 0
    
    def generate_import_report(self, analysis: Dict[str, Any], imported_count: int) -> str:
        """Generate comprehensive import report"""
        print(f"\n📄 Generating import report...")
        
        report = {
            'import_summary': {
                'timestamp': datetime.now().isoformat(),
                'imported_trades': imported_count,
                'status': 'success' if imported_count > 0 else 'failed'
            },
            'trading_analysis': analysis
        }
        
        # Save report
        report_filename = f"delta_csv_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Report saved: {report_filename}")
        return report_filename
    
    def process_csv_file(self, csv_file_path: str) -> Dict[str, Any]:
        """Complete CSV processing workflow"""
        print(f"\n🚀 Starting CSV Import Process")
        print("=" * 50)
        
        # Step 1: Detect CSV format
        column_mappings = self.detect_csv_format(csv_file_path)
        if not column_mappings:
            return {'success': False, 'error': 'Could not detect CSV format'}
        
        # Step 2: Load data
        df = self.load_csv_data(csv_file_path, column_mappings)
        if df.empty:
            return {'success': False, 'error': 'Could not load CSV data'}
        
        # Step 3: Analyze patterns
        analysis = self.analyze_trading_patterns(df)
        
        # Step 4: Convert to internal format
        trades = self.convert_to_internal_format(df)
        
        # Step 5: Import to database
        imported_count = self.import_to_database(trades)
        
        # Step 6: Generate report
        report_file = self.generate_import_report(analysis, imported_count)
        
        return {
            'success': True,
            'imported_trades': imported_count,
            'total_rows': len(df),
            'analysis': analysis,
            'report_file': report_file
        }

def main():
    """Main function for testing"""
    importer = DeltaCSVImporter()
    
    # Example usage
    csv_file = input("Enter path to Delta Exchange CSV file: ").strip()
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    result = importer.process_csv_file(csv_file)
    
    if result['success']:
        print(f"\n🎉 CSV Import Successful!")
        print(f"📊 Imported: {result['imported_trades']} trades")
        print(f"📄 Report: {result['report_file']}")
    else:
        print(f"\n❌ CSV Import Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
