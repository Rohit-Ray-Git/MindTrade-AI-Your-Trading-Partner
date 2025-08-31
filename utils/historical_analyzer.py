#!/usr/bin/env python3
"""
Historical Trading Data Analyzer
AI-powered analysis of imported trading history for pattern recognition and insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from models.database import get_db
from models.models import Trade, PsychologyNote, AgentOutput
from models.dal import TradeDAL, AnalyticsDAL
from utils.ai_integration import GeminiAI
from orchestrator.ai_orchestrator import AIOrchestrator

class HistoricalTradingAnalyzer:
    """Analyze historical trading data using AI agents"""
    
    def __init__(self):
        self.ai = GeminiAI()
        self.ai_orchestrator = AIOrchestrator()
        
        print("🤖 Historical Trading Analyzer")
        print("=" * 50)
    
    def get_historical_trades(self, days_back: int = 365) -> List[Dict[str, Any]]:
        """Get historical trades from database"""
        try:
            db = next(get_db())
            trade_dal = TradeDAL(db)
            
            # Get trades from last N days
            cutoff_date = datetime.now() - timedelta(days=days_back)
            trades = trade_dal.get_trades_since(cutoff_date)
            
            # Convert to dict format for analysis
            trade_data = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'direction': trade.direction,
                    'entry_price': float(trade.entry_price),
                    'exit_price': float(trade.exit_price),
                    'stop_price': float(trade.stop_price),
                    'quantity': float(trade.quantity),
                    'pnl': float(trade.pnl),
                    'r_multiple': float(trade.r_multiple),
                    'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                    'source': trade.source,
                    'logic': trade.logic,
                    'notes': trade.notes,
                    'fees': float(trade.fees) if trade.fees else 0.0
                }
                trade_data.append(trade_dict)
            
            print(f"📊 Retrieved {len(trade_data)} historical trades")
            return trade_data
            
        except Exception as e:
            print(f"❌ Error retrieving trades: {str(e)}")
            return []
    
    def calculate_trading_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive trading metrics"""
        if not trades:
            return {}
        
        df = pd.DataFrame(trades)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = df[df['pnl'] > 0]
        losing_trades = df[df['pnl'] < 0]
        
        # Performance metrics
        total_pnl = df['pnl'].sum()
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        largest_win = df['pnl'].max()
        largest_loss = df['pnl'].min()
        
        # Risk metrics
        profit_factor = (winning_trades['pnl'].sum() / abs(losing_trades['pnl'].sum()) 
                        if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else float('inf'))
        
        # R-multiple analysis
        avg_r_multiple = df['r_multiple'].mean()
        positive_r_trades = df[df['r_multiple'] > 0]
        negative_r_trades = df[df['r_multiple'] < 0]
        
        # Direction analysis
        long_trades = df[df['direction'] == 'long']
        short_trades = df[df['direction'] == 'short']
        
        # Symbol analysis
        symbol_performance = df.groupby('symbol').agg({
            'pnl': ['sum', 'count', 'mean'],
            'r_multiple': 'mean'
        }).round(2)
        
        # Convert multi-level columns to string keys for JSON serialization
        symbol_performance_dict = {}
        for symbol in symbol_performance.index:
            symbol_performance_dict[symbol] = {
                'total_pnl': float(symbol_performance.loc[symbol, ('pnl', 'sum')]),
                'trade_count': int(symbol_performance.loc[symbol, ('pnl', 'count')]),
                'avg_pnl': float(symbol_performance.loc[symbol, ('pnl', 'mean')]),
                'avg_r_multiple': float(symbol_performance.loc[symbol, ('r_multiple', 'mean')])
            }
        
        # Time-based analysis
        if 'entry_time' in df.columns and df['entry_time'].notna().any():
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['hour'] = df['entry_time'].dt.hour
            df['day_of_week'] = df['entry_time'].dt.day_name()
            
            hourly_performance = df.groupby('hour')['pnl'].sum()
            daily_performance = df.groupby('day_of_week')['pnl'].sum()
        
        metrics = {
            'summary': {
                'total_trades': total_trades,
                'total_pnl': float(total_pnl),
                'win_rate': float(win_rate),
                'profit_factor': float(profit_factor) if profit_factor != float('inf') else 'N/A'
            },
            'performance': {
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'largest_win': float(largest_win),
                'largest_loss': float(largest_loss),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades)
            },
            'risk_management': {
                'avg_r_multiple': float(avg_r_multiple),
                'positive_r_trades': len(positive_r_trades),
                'negative_r_trades': len(negative_r_trades),
                'avg_positive_r': float(positive_r_trades['r_multiple'].mean()) if len(positive_r_trades) > 0 else 0,
                'avg_negative_r': float(negative_r_trades['r_multiple'].mean()) if len(negative_r_trades) > 0 else 0
            },
            'direction_analysis': {
                'long_trades': len(long_trades),
                'short_trades': len(short_trades),
                'long_pnl': float(long_trades['pnl'].sum()) if len(long_trades) > 0 else 0,
                'short_pnl': float(short_trades['pnl'].sum()) if len(short_trades) > 0 else 0,
                'long_win_rate': float(len(long_trades[long_trades['pnl'] > 0]) / len(long_trades) * 100) if len(long_trades) > 0 else 0,
                'short_win_rate': float(len(short_trades[short_trades['pnl'] > 0]) / len(short_trades) * 100) if len(short_trades) > 0 else 0
            },
            'symbol_performance': symbol_performance_dict,
            'time_analysis': {
                'hourly_performance': hourly_performance.to_dict() if 'hour' in df.columns else {},
                'daily_performance': daily_performance.to_dict() if 'day_of_week' in df.columns else {}
            }
        }
        
        return metrics
    
    def analyze_trading_patterns(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trading patterns using AI"""
        print("🔍 Analyzing trading patterns with AI...")
        
        if not trades:
            return {}
        
        # Prepare data for AI analysis
        analysis_data = {
            'trades': trades[:100],  # Limit to first 100 trades for analysis
            'metrics': self.calculate_trading_metrics(trades),
            'total_trades': len(trades)
        }
        
        # AI Analysis Prompts
        pattern_analysis_prompt = f"""
        Analyze this trader's historical trading data and identify patterns:
        
        TRADING DATA SUMMARY:
        {json.dumps(analysis_data['metrics']['summary'], indent=2)}
        
        PERFORMANCE METRICS:
        {json.dumps(analysis_data['metrics']['performance'], indent=2)}
        
        DIRECTION ANALYSIS:
        {json.dumps(analysis_data['metrics']['direction_analysis'], indent=2)}
        
        Please provide:
        1. Trading Style Classification (scalper, swing trader, position trader, etc.)
        2. Pattern Recognition (recurring setups, time patterns, symbol preferences)
        3. Strengths Analysis (what's working well)
        4. Weaknesses Analysis (areas for improvement)
        5. Risk Management Assessment
        6. Behavioral Patterns (overtrading, revenge trading, FOMO, etc.)
        7. Specific Recommendations for Improvement
        
        Format as a structured analysis with clear sections.
        """
        
        try:
            # Get AI analysis
            pattern_analysis = self.ai.analyze_psychology_with_image(pattern_analysis_prompt, None)
            
            return {
                'pattern_analysis': pattern_analysis,
                'metrics': analysis_data['metrics'],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error in AI pattern analysis: {str(e)}")
            return {
                'pattern_analysis': f"Error in analysis: {str(e)}",
                'metrics': analysis_data['metrics'],
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def generate_trading_style_report(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive trading style report"""
        print("📊 Generating trading style report...")
        
        if not trades:
            return {}
        
        df = pd.DataFrame(trades)
        
        # Trading frequency analysis
        if 'entry_time' in df.columns and df['entry_time'].notna().any():
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['date'] = df['entry_time'].dt.date
            
            daily_trades = df.groupby('date').size()
            avg_trades_per_day = daily_trades.mean()
            max_trades_per_day = daily_trades.max()
            
            # Determine trading frequency style
            if avg_trades_per_day > 10:
                frequency_style = "High Frequency Trader"
            elif avg_trades_per_day > 3:
                frequency_style = "Active Day Trader"
            elif avg_trades_per_day > 1:
                frequency_style = "Moderate Trader"
            else:
                frequency_style = "Position Trader"
        else:
            frequency_style = "Unknown"
            avg_trades_per_day = 0
            max_trades_per_day = 0
        
        # Position sizing analysis
        avg_quantity = df['quantity'].mean()
        quantity_std = df['quantity'].std()
        quantity_consistency = "Consistent" if quantity_std / avg_quantity < 0.5 else "Variable"
        
        # Risk tolerance analysis
        avg_risk = df['r_multiple'].abs().mean()
        if avg_risk > 2:
            risk_tolerance = "High Risk"
        elif avg_risk > 1:
            risk_tolerance = "Moderate Risk"
        else:
            risk_tolerance = "Conservative"
        
        # Direction bias analysis
        long_count = len(df[df['direction'] == 'long'])
        short_count = len(df[df['direction'] == 'short'])
        total_count = len(df)
        
        if long_count / total_count > 0.7:
            direction_bias = "Strong Long Bias"
        elif short_count / total_count > 0.7:
            direction_bias = "Strong Short Bias"
        else:
            direction_bias = "Balanced"
        
        # Symbol concentration
        symbol_counts = df['symbol'].value_counts()
        top_symbol_pct = symbol_counts.iloc[0] / total_count * 100 if len(symbol_counts) > 0 else 0
        
        if top_symbol_pct > 50:
            symbol_concentration = "Highly Concentrated"
        elif top_symbol_pct > 30:
            symbol_concentration = "Moderately Concentrated"
        else:
            symbol_concentration = "Diversified"
        
        # Win rate consistency
        if 'entry_time' in df.columns and df['entry_time'].notna().any():
            df['month'] = df['entry_time'].dt.to_period('M')
            monthly_win_rates = df.groupby('month').apply(
                lambda x: len(x[x['pnl'] > 0]) / len(x) * 100
            )
            win_rate_consistency = "Consistent" if monthly_win_rates.std() < 10 else "Variable"
        else:
            win_rate_consistency = "Unknown"
        
        style_report = {
            'trading_style': {
                'frequency_style': frequency_style,
                'avg_trades_per_day': float(avg_trades_per_day),
                'max_trades_per_day': int(max_trades_per_day),
                'position_sizing': quantity_consistency,
                'risk_tolerance': risk_tolerance,
                'direction_bias': direction_bias,
                'symbol_concentration': symbol_concentration,
                'win_rate_consistency': win_rate_consistency
            },
            'behavioral_insights': {
                'overtrading_indicator': "High" if avg_trades_per_day > 5 else "Normal",
                'risk_management_quality': "Good" if avg_risk < 2 else "Needs Improvement",
                'discipline_level': "High" if win_rate_consistency == "Consistent" else "Variable"
            }
        }
        
        return style_report
    
    def generate_ai_coaching_insights(self, trades: List[Dict[str, Any]], 
                                    pattern_analysis: Dict[str, Any],
                                    style_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI coaching insights"""
        print("🎯 Generating AI coaching insights...")
        
        # Combine all analysis data
        coaching_data = {
            'trades_summary': {
                'total_trades': len(trades),
                'recent_trades': trades[-20:] if len(trades) > 20 else trades
            },
            'pattern_analysis': pattern_analysis,
            'style_report': style_report,
            'metrics': self.calculate_trading_metrics(trades)
        }
        
        coaching_prompt = f"""
        Based on this trader's data, provide personalized coaching insights:
        
        TRADING STYLE:
        {json.dumps(style_report.get('trading_style', {}), indent=2)}
        
        BEHAVIORAL INSIGHTS:
        {json.dumps(style_report.get('behavioral_insights', {}), indent=2)}
        
        PATTERN ANALYSIS:
        {json.dumps(pattern_analysis.get('pattern_analysis', {}), indent=2)}
        
        Please provide:
        1. **Immediate Action Items** (3-5 specific things to focus on this week)
        2. **Behavioral Improvements** (psychology and discipline)
        3. **Strategy Refinements** (setup and execution improvements)
        4. **Risk Management Enhancements** (position sizing, stops, etc.)
        5. **Weekly Goals** (specific, measurable targets)
        6. **Success Metrics** (how to track improvement)
        7. **Motivational Message** (encouragement and mindset)
        
        Format as actionable coaching advice with clear next steps.
        """
        
        try:
            coaching_insights = self.ai.analyze_psychology_with_image(coaching_prompt, None)
            
            return {
                'coaching_insights': coaching_insights,
                'action_items': self._extract_action_items(coaching_insights),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error generating coaching insights: {str(e)}")
            return {
                'coaching_insights': f"Error generating insights: {str(e)}",
                'action_items': [],
                'generated_at': datetime.now().isoformat()
            }
    
    def _extract_action_items(self, coaching_insights: str) -> List[str]:
        """Extract action items from coaching insights"""
        action_items = []
        
        if isinstance(coaching_insights, str):
            lines = coaching_insights.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['action', 'focus', 'improve', 'work on', 'practice']):
                    if line and not line.startswith('#'):
                        action_items.append(line)
        
        return action_items[:5]  # Return top 5 action items
    
    def save_analysis_results(self, analysis_results: Dict[str, Any]) -> str:
        """Save analysis results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"historical_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(analysis_results, f, indent=2, default=str)
            
            print(f"💾 Analysis saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving analysis: {str(e)}")
            return ""
    
    def run_complete_analysis(self, days_back: int = 365) -> Dict[str, Any]:
        """Run complete historical analysis workflow"""
        print(f"\n🚀 Starting Complete Historical Analysis")
        print("=" * 60)
        
        # Step 1: Get historical trades
        trades = self.get_historical_trades(days_back)
        if not trades:
            return {'error': 'No historical trades found'}
        
        # Step 2: Calculate metrics
        metrics = self.calculate_trading_metrics(trades)
        
        # Step 3: Pattern analysis
        pattern_analysis = self.analyze_trading_patterns(trades)
        
        # Step 4: Trading style report
        style_report = self.generate_trading_style_report(trades)
        
        # Step 5: AI coaching insights
        coaching_insights = self.generate_ai_coaching_insights(
            trades, pattern_analysis, style_report
        )
        
        # Step 6: Combine results
        complete_analysis = {
            'analysis_summary': {
                'total_trades_analyzed': len(trades),
                'analysis_period_days': days_back,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'metrics': metrics,
            'pattern_analysis': pattern_analysis,
            'trading_style': style_report,
            'coaching_insights': coaching_insights
        }
        
        # Step 7: Save results
        report_file = self.save_analysis_results(complete_analysis)
        complete_analysis['report_file'] = report_file
        
        print(f"\n✅ Complete Analysis Finished!")
        print(f"📊 Analyzed {len(trades)} trades")
        print(f"📄 Report: {report_file}")
        
        return complete_analysis

def main():
    """Main function for testing"""
    analyzer = HistoricalTradingAnalyzer()
    
    print("🤖 Historical Trading Analysis System")
    print("=" * 50)
    
    # Run complete analysis
    result = analyzer.run_complete_analysis(days_back=365)
    
    if 'error' not in result:
        print(f"\n🎉 Analysis Complete!")
        print(f"📊 Trades analyzed: {result['analysis_summary']['total_trades_analyzed']}")
        print(f"📄 Report saved: {result.get('report_file', 'N/A')}")
        
        # Display key insights
        metrics = result.get('metrics', {})
        if 'summary' in metrics:
            summary = metrics['summary']
            print(f"\n📈 Key Metrics:")
            print(f"   Total P&L: ${summary.get('total_pnl', 0):,.2f}")
            print(f"   Win Rate: {summary.get('win_rate', 0):.1f}%")
            print(f"   Profit Factor: {summary.get('profit_factor', 0)}")
        
        style = result.get('trading_style', {}).get('trading_style', {})
        if style:
            print(f"\n🎯 Trading Style:")
            print(f"   Frequency: {style.get('frequency_style', 'Unknown')}")
            print(f"   Risk Tolerance: {style.get('risk_tolerance', 'Unknown')}")
            print(f"   Direction Bias: {style.get('direction_bias', 'Unknown')}")
        
        coaching = result.get('coaching_insights', {})
        if 'action_items' in coaching and coaching['action_items']:
            print(f"\n🎯 Top Action Items:")
            for i, item in enumerate(coaching['action_items'][:3], 1):
                print(f"   {i}. {item}")
    else:
        print(f"\n❌ Analysis failed: {result['error']}")

if __name__ == "__main__":
    main()
