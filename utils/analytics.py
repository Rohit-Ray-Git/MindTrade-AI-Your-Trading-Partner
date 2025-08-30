"""
Advanced Analytics Engine for Trading Performance
Provides comprehensive trading analytics, metrics, and visualizations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sqlalchemy.orm import Session
from loguru import logger

from models.models import Trade, Setup, PsychologyNote
from models.dal import get_db_session

class TradingAnalytics:
    """Comprehensive trading analytics and performance metrics"""
    
    def __init__(self):
        """Initialize analytics engine"""
        self.db = get_db_session()
        logger.info("Trading Analytics Engine initialized")
    
    def get_trading_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive trading summary with key metrics"""
        try:
            # Build query with date filters
            query = self.db.query(Trade)
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.exit_time <= end_date)
            
            trades = query.all()
            
            if not trades:
                return self._get_empty_summary()
            
            # Convert to DataFrame for easier analysis
            df = self._trades_to_dataframe(trades)
            
            # Calculate key metrics
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            break_even_trades = len(df[df['pnl'] == 0])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = df['pnl'].sum()
            total_fees = df['fees'].sum() if 'fees' in df.columns else 0
            net_pnl = total_pnl - total_fees
            
            avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            
            profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else float('inf')
            
            # R-multiple analysis
            avg_r_multiple = df['r_multiple'].mean() if 'r_multiple' in df.columns else 0
            total_r = df['r_multiple'].sum() if 'r_multiple' in df.columns else 0
            
            # Drawdown analysis
            cumulative_pnl = df['pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = (max_drawdown / running_max.max() * 100) if running_max.max() > 0 else 0
            
            # Consecutive wins/losses
            df['win'] = df['pnl'] > 0
            df['streak'] = df['win'].groupby((df['win'] != df['win'].shift()).cumsum()).cumcount() + 1
            max_consecutive_wins = df[df['win']]['streak'].max() if winning_trades > 0 else 0
            max_consecutive_losses = df[~df['win']]['streak'].max() if losing_trades > 0 else 0
            
            # Time-based analysis
            if len(df) > 1:
                total_days = (df['exit_time'].max() - df['entry_time'].min()).days
                trades_per_day = total_trades / max(total_days, 1)
            else:
                trades_per_day = 0
            
            # Volatility metrics
            pnl_std = df['pnl'].std()
            sharpe_ratio = (df['pnl'].mean() / pnl_std) if pnl_std > 0 else 0
            
            return {
                'overview': {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'break_even_trades': break_even_trades,
                    'win_rate': round(win_rate, 2),
                    'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'N/A'
                },
                'pnl_metrics': {
                    'total_pnl': round(total_pnl, 2),
                    'total_fees': round(total_fees, 2),
                    'net_pnl': round(net_pnl, 2),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'avg_trade': round(total_pnl / total_trades, 2) if total_trades > 0 else 0
                },
                'risk_metrics': {
                    'avg_r_multiple': round(avg_r_multiple, 2),
                    'total_r': round(total_r, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'max_drawdown_pct': round(max_drawdown_pct, 2),
                    'sharpe_ratio': round(sharpe_ratio, 2)
                },
                'behavioral_metrics': {
                    'max_consecutive_wins': int(max_consecutive_wins) if not pd.isna(max_consecutive_wins) else 0,
                    'max_consecutive_losses': int(max_consecutive_losses) if not pd.isna(max_consecutive_losses) else 0,
                    'trades_per_day': round(trades_per_day, 2),
                    'pnl_volatility': round(pnl_std, 2)
                },
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                    'total_days': total_days if len(df) > 1 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating trading summary: {e}")
            return self._get_empty_summary()
    
    def get_setup_performance(self) -> List[Dict[str, Any]]:
        """Analyze performance by trading setup"""
        try:
            # Query trades with setup information
            trades = (
                self.db.query(Trade, Setup)
                .outerjoin(Setup, Trade.setup_id == Setup.id)
                .all()
            )
            
            if not trades:
                return []
            
            # Group by setup
            setup_data = {}
            for trade, setup in trades:
                setup_name = setup.name if setup else "No Setup"
                
                if setup_name not in setup_data:
                    setup_data[setup_name] = {
                        'trades': [],
                        'setup_id': setup.id if setup else None
                    }
                
                setup_data[setup_name]['trades'].append(trade)
            
            # Calculate metrics for each setup
            results = []
            for setup_name, data in setup_data.items():
                trades_list = data['trades']
                df = self._trades_to_dataframe(trades_list)
                
                total_trades = len(df)
                winning_trades = len(df[df['pnl'] > 0])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                total_pnl = df['pnl'].sum()
                avg_pnl = df['pnl'].mean()
                avg_r_multiple = df['r_multiple'].mean() if 'r_multiple' in df.columns else 0
                
                profit_factor = (
                    abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum())
                    if len(df[df['pnl'] < 0]) > 0 else float('inf')
                )
                
                results.append({
                    'setup_name': setup_name,
                    'setup_id': data['setup_id'],
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'avg_pnl': round(avg_pnl, 2),
                    'avg_r_multiple': round(avg_r_multiple, 2),
                    'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'N/A'
                })
            
            # Sort by total PnL descending
            results.sort(key=lambda x: x['total_pnl'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error calculating setup performance: {e}")
            return []
    
    def generate_pnl_curve(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> go.Figure:
        """Generate cumulative P&L curve with drawdown"""
        try:
            # Get trades data
            query = self.db.query(Trade).order_by(Trade.exit_time)
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.exit_time <= end_date)
            
            trades = query.all()
            
            if not trades:
                return self._get_empty_chart("No trades found for the selected period")
            
            df = self._trades_to_dataframe(trades)
            df = df.sort_values('exit_time')
            
            # Calculate cumulative metrics
            df['cumulative_pnl'] = df['pnl'].cumsum()
            df['running_max'] = df['cumulative_pnl'].expanding().max()
            df['drawdown'] = df['cumulative_pnl'] - df['running_max']
            df['drawdown_pct'] = (df['drawdown'] / df['running_max'] * 100).fillna(0)
            df['trade_number'] = range(1, len(df) + 1)
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Cumulative P&L', 'Drawdown ($)', 'Drawdown (%)'),
                row_heights=[0.5, 0.25, 0.25],
                shared_xaxes=True,
                vertical_spacing=0.05
            )
            
            # P&L curve
            fig.add_trace(
                go.Scatter(
                    x=df['exit_time'],
                    y=df['cumulative_pnl'],
                    mode='lines+markers',
                    name='Cumulative P&L',
                    line=dict(color='#00CC96', width=2),
                    marker=dict(size=4),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Cumulative P&L:</b> $%{y:,.2f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Add running maximum
            fig.add_trace(
                go.Scatter(
                    x=df['exit_time'],
                    y=df['running_max'],
                    mode='lines',
                    name='High Water Mark',
                    line=dict(color='#FFA15A', width=1, dash='dash'),
                    hovertemplate='<b>Date:</b> %{x}<br><b>High Water Mark:</b> $%{y:,.2f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Drawdown in dollars
            fig.add_trace(
                go.Scatter(
                    x=df['exit_time'],
                    y=df['drawdown'],
                    mode='lines',
                    name='Drawdown ($)',
                    fill='tonegative',
                    line=dict(color='#EF553B', width=1),
                    fillcolor='rgba(239, 85, 59, 0.3)',
                    hovertemplate='<b>Date:</b> %{x}<br><b>Drawdown:</b> $%{y:,.2f}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Drawdown percentage
            fig.add_trace(
                go.Scatter(
                    x=df['exit_time'],
                    y=df['drawdown_pct'],
                    mode='lines',
                    name='Drawdown (%)',
                    fill='tonegative',
                    line=dict(color='#AB63FA', width=1),
                    fillcolor='rgba(171, 99, 250, 0.3)',
                    hovertemplate='<b>Date:</b> %{x}<br><b>Drawdown:</b> %{y:.2f}%<extra></extra>'
                ),
                row=3, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text='Trading Performance Analysis',
                    x=0.5,
                    font=dict(size=20)
                ),
                height=700,
                showlegend=True,
                hovermode='x unified',
                template='plotly_white'
            )
            
            # Update y-axes
            fig.update_yaxes(title_text="P&L ($)", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown ($)", row=2, col=1)
            fig.update_yaxes(title_text="Drawdown (%)", row=3, col=1)
            
            # Update x-axes
            fig.update_xaxes(title_text="Date", row=3, col=1)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating P&L curve: {e}")
            return self._get_empty_chart(f"Error generating chart: {str(e)}")
    
    def generate_monthly_performance(self) -> go.Figure:
        """Generate monthly performance heatmap"""
        try:
            trades = self.db.query(Trade).all()
            
            if not trades:
                return self._get_empty_chart("No trades found")
            
            df = self._trades_to_dataframe(trades)
            df['year'] = df['exit_time'].dt.year
            df['month'] = df['exit_time'].dt.month
            df['month_name'] = df['exit_time'].dt.strftime('%B')
            
            # Group by year and month
            monthly_pnl = df.groupby(['year', 'month', 'month_name'])['pnl'].sum().reset_index()
            
            # Create pivot table for heatmap
            pivot_data = monthly_pnl.pivot(index='month_name', columns='year', values='pnl')
            
            # Ensure all months are present
            month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            pivot_data = pivot_data.reindex(month_order)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale='RdYlGn',
                hoverongaps=False,
                hovertemplate='<b>%{y} %{x}</b><br>P&L: $%{z:,.2f}<extra></extra>',
                colorbar=dict(title="P&L ($)")
            ))
            
            fig.update_layout(
                title='Monthly Performance Heatmap',
                xaxis_title='Year',
                yaxis_title='Month',
                height=500,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating monthly performance: {e}")
            return self._get_empty_chart(f"Error generating chart: {str(e)}")
    
    def generate_setup_comparison(self) -> go.Figure:
        """Generate setup performance comparison chart"""
        try:
            setup_data = self.get_setup_performance()
            
            if not setup_data:
                return self._get_empty_chart("No setup data found")
            
            # Prepare data for chart
            setup_names = [item['setup_name'] for item in setup_data]
            win_rates = [item['win_rate'] for item in setup_data]
            total_pnls = [item['total_pnl'] for item in setup_data]
            trade_counts = [item['total_trades'] for item in setup_data]
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Win Rate by Setup', 'Total P&L by Setup', 
                               'Trade Count by Setup', 'Avg P&L per Trade'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Win rate bar chart
            fig.add_trace(
                go.Bar(
                    x=setup_names,
                    y=win_rates,
                    name='Win Rate (%)',
                    marker_color='lightblue',
                    hovertemplate='<b>%{x}</b><br>Win Rate: %{y}%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Total P&L bar chart
            colors = ['green' if pnl >= 0 else 'red' for pnl in total_pnls]
            fig.add_trace(
                go.Bar(
                    x=setup_names,
                    y=total_pnls,
                    name='Total P&L ($)',
                    marker_color=colors,
                    hovertemplate='<b>%{x}</b><br>Total P&L: $%{y:,.2f}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Trade count bar chart
            fig.add_trace(
                go.Bar(
                    x=setup_names,
                    y=trade_counts,
                    name='Trade Count',
                    marker_color='orange',
                    hovertemplate='<b>%{x}</b><br>Trades: %{y}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Average P&L per trade
            avg_pnls = [item['avg_pnl'] for item in setup_data]
            avg_colors = ['green' if avg >= 0 else 'red' for avg in avg_pnls]
            fig.add_trace(
                go.Bar(
                    x=setup_names,
                    y=avg_pnls,
                    name='Avg P&L ($)',
                    marker_color=avg_colors,
                    hovertemplate='<b>%{x}</b><br>Avg P&L: $%{y:,.2f}<extra></extra>'
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                title='Trading Setup Performance Comparison',
                height=600,
                showlegend=False,
                template='plotly_white'
            )
            
            # Update y-axes
            fig.update_yaxes(title_text="Win Rate (%)", row=1, col=1)
            fig.update_yaxes(title_text="Total P&L ($)", row=1, col=2)
            fig.update_yaxes(title_text="Trade Count", row=2, col=1)
            fig.update_yaxes(title_text="Avg P&L ($)", row=2, col=2)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating setup comparison: {e}")
            return self._get_empty_chart(f"Error generating chart: {str(e)}")
    
    def generate_r_multiple_distribution(self) -> go.Figure:
        """Generate R-multiple distribution histogram"""
        try:
            trades = self.db.query(Trade).filter(Trade.r_multiple.isnot(None)).all()
            
            if not trades:
                return self._get_empty_chart("No R-multiple data found")
            
            df = self._trades_to_dataframe(trades)
            r_multiples = df['r_multiple'].dropna()
            
            if r_multiples.empty:
                return self._get_empty_chart("No valid R-multiple data")
            
            # Create histogram
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=r_multiples,
                nbinsx=20,
                name='R-Multiple Distribution',
                marker_color='skyblue',
                opacity=0.7,
                hovertemplate='R-Multiple: %{x:.2f}<br>Count: %{y}<extra></extra>'
            ))
            
            # Add vertical line at R=0
            fig.add_vline(x=0, line_dash="dash", line_color="red", 
                         annotation_text="Break Even")
            
            # Add mean line
            mean_r = r_multiples.mean()
            fig.add_vline(x=mean_r, line_dash="dash", line_color="green",
                         annotation_text=f"Mean: {mean_r:.2f}R")
            
            fig.update_layout(
                title='R-Multiple Distribution',
                xaxis_title='R-Multiple',
                yaxis_title='Frequency',
                height=400,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating R-multiple distribution: {e}")
            return self._get_empty_chart(f"Error generating chart: {str(e)}")
    
    def _trades_to_dataframe(self, trades: List[Trade]) -> pd.DataFrame:
        """Convert trades to pandas DataFrame"""
        data = []
        for trade in trades:
            data.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'fees': trade.fees or 0,
                'r_multiple': trade.r_multiple,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'setup_id': trade.setup_id
            })
        
        return pd.DataFrame(data)
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure"""
        return {
            'overview': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'break_even_trades': 0,
                'win_rate': 0,
                'profit_factor': 'N/A'
            },
            'pnl_metrics': {
                'total_pnl': 0,
                'total_fees': 0,
                'net_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_trade': 0
            },
            'risk_metrics': {
                'avg_r_multiple': 0,
                'total_r': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0
            },
            'behavioral_metrics': {
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'trades_per_day': 0,
                'pnl_volatility': 0
            },
            'period': {
                'start_date': None,
                'end_date': None,
                'total_days': 0
            }
        }
    
    def _get_empty_chart(self, message: str) -> go.Figure:
        """Return empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            template='plotly_white',
            height=400
        )
        return fig
    
    def __del__(self):
        """Cleanup database session"""
        if hasattr(self, 'db'):
            self.db.close()
