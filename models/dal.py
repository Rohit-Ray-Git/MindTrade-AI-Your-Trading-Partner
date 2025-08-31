"""
Data Access Layer (DAL) for database operations
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from .models import Trade, PsychologyNote, Setup, AgentOutput, User, Settings
from .database import SessionLocal
from loguru import logger

class TradeDAL:
    """Data Access Layer for Trade operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """Create a new trade"""
        try:
            # Calculate P&L and R-multiple
            if trade_data['direction'] == 'Long':
                pnl = (trade_data['exit_price'] - trade_data['entry_price']) * trade_data['quantity']
            else:
                pnl = (trade_data['entry_price'] - trade_data['exit_price']) * trade_data['quantity']
            
            risk_amount = abs(trade_data['entry_price'] - trade_data['stop_price']) * trade_data['quantity']
            r_multiple = pnl / risk_amount if risk_amount > 0 else 0
            
            # Create trade object
            trade = Trade(
                symbol=trade_data['symbol'],
                direction=trade_data['direction'],
                entry_price=trade_data['entry_price'],
                stop_price=trade_data['stop_price'],
                exit_price=trade_data['exit_price'],
                quantity=trade_data['quantity'],
                account_equity=trade_data['account_equity'],
                risk_percent=trade_data['risk_percent'],
                pnl=pnl,
                r_multiple=r_multiple,
                trade_time=trade_data['trade_time'],
                source=trade_data.get('source', 'manual'),
                logic=trade_data.get('logic'),
                notes=trade_data.get('notes'),
                setup_id=trade_data.get('setup_id')
            )
            
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            logger.info(f"Created trade: {trade.symbol} {trade.direction} P&L: ${trade.pnl:.2f}")
            return trade
            
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            self.db.rollback()
            raise
    
    def get_trade(self, trade_id: int) -> Optional[Trade]:
        """Get trade by ID"""
        return self.db.query(Trade).filter(Trade.id == trade_id).first()
    
    def get_trades(self, 
                   limit: int = 100, 
                   offset: int = 0,
                   symbol: Optional[str] = None,
                   setup_id: Optional[int] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Trade]:
        """Get trades with filters"""
        query = self.db.query(Trade)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        if setup_id:
            query = query.filter(Trade.setup_id == setup_id)
        if start_date:
            query = query.filter(Trade.trade_time >= start_date)
        if end_date:
            query = query.filter(Trade.trade_time <= end_date)
        
        return query.order_by(desc(Trade.trade_time)).offset(offset).limit(limit).all()
    
    def get_trades_since(self, cutoff_date: datetime) -> List[Trade]:
        """Get trades since a specific date"""
        return self.db.query(Trade).filter(
            Trade.entry_time >= cutoff_date
        ).order_by(desc(Trade.entry_time)).all()
    
    def update_trade(self, trade_id: int, trade_data: Dict[str, Any]) -> Optional[Trade]:
        """Update trade"""
        trade = self.get_trade(trade_id)
        if not trade:
            return None
        
        try:
            for key, value in trade_data.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            
            # Recalculate P&L and R-multiple if prices changed
            if any(key in trade_data for key in ['entry_price', 'stop_price', 'exit_price', 'quantity']):
                if trade.direction == 'Long':
                    pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                else:
                    pnl = (trade.entry_price - trade.exit_price) * trade.quantity
                
                risk_amount = abs(trade.entry_price - trade.stop_price) * trade.quantity
                r_multiple = pnl / risk_amount if risk_amount > 0 else 0
                
                trade.pnl = pnl
                trade.r_multiple = r_multiple
            
            self.db.commit()
            self.db.refresh(trade)
            return trade
            
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            self.db.rollback()
            raise
    
    def delete_trade(self, trade_id: int) -> bool:
        """Delete trade"""
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        try:
            self.db.delete(trade)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting trade: {e}")
            self.db.rollback()
            raise

class PsychologyDAL:
    """Data Access Layer for Psychology operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_psychology_note(self, note_data: Dict[str, Any]) -> PsychologyNote:
        """Create psychology note"""
        try:
            # Extract only the fields that exist in the PsychologyNote model
            valid_fields = {
                'trade_id': note_data.get('trade_id'),
                'note_text': note_data.get('note_text'),
                'self_tags': note_data.get('self_tags'),
                'nlp_tags': note_data.get('nlp_tags'),
                'sentiment_score': note_data.get('sentiment_score'),
                'confidence_score': note_data.get('confidence_score'),
                'fear_score': note_data.get('fear_score'),
                'greed_score': note_data.get('greed_score'),
                'patience_score': note_data.get('patience_score'),
                'fomo_score': note_data.get('fomo_score'),
                'revenge_score': note_data.get('revenge_score')
            }
            
            # Remove None values
            valid_fields = {k: v for k, v in valid_fields.items() if v is not None}
            
            note = PsychologyNote(**valid_fields)
            self.db.add(note)
            self.db.commit()
            self.db.refresh(note)
            return note
        except Exception as e:
            logger.error(f"Error creating psychology note: {e}")
            self.db.rollback()
            raise
    
    def get_psychology_notes(self, trade_id: int) -> List[PsychologyNote]:
        """Get psychology notes for a trade"""
        return self.db.query(PsychologyNote).filter(PsychologyNote.trade_id == trade_id).all()
    
    def get_recent_notes(self, limit: int = 10) -> List[PsychologyNote]:
        """Get the most recent psychology notes"""
        return self.db.query(PsychologyNote).order_by(desc(PsychologyNote.created_at)).limit(limit).all()
    
    def create_note(self, note_data: Dict[str, Any]) -> PsychologyNote:
        """Create a psychology note (alias for create_psychology_note)"""
        return self.create_psychology_note(note_data)
    
    def update_psychology_note(self, note_id: int, note_data: Dict[str, Any]) -> Optional[PsychologyNote]:
        """Update psychology note"""
        note = self.db.query(PsychologyNote).filter(PsychologyNote.id == note_id).first()
        if not note:
            return None
        
        try:
            for key, value in note_data.items():
                if hasattr(note, key):
                    setattr(note, key, value)
            
            self.db.commit()
            self.db.refresh(note)
            return note
        except Exception as e:
            logger.error(f"Error updating psychology note: {e}")
            self.db.rollback()
            raise

class SetupDAL:
    """Data Access Layer for Setup operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_setups(self) -> List[Setup]:
        """Get all setups"""
        return self.db.query(Setup).all()
    
    def get_all_setups(self) -> List[Setup]:
        """Get all setups (alias for get_setups)"""
        return self.get_setups()
    
    def get_setup(self, setup_id: int) -> Optional[Setup]:
        """Get setup by ID"""
        return self.db.query(Setup).filter(Setup.id == setup_id).first()
    
    def create_setup(self, name: str, description: str = None) -> Setup:
        """Create new setup"""
        try:
            setup = Setup(name=name, description=description)
            self.db.add(setup)
            self.db.commit()
            self.db.refresh(setup)
            return setup
        except Exception as e:
            logger.error(f"Error creating setup: {e}")
            self.db.rollback()
            raise

class AnalyticsDAL:
    """Data Access Layer for Analytics operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_trading_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading summary statistics"""
        query = self.db.query(Trade)
        
        if start_date:
            query = query.filter(Trade.trade_time >= start_date)
        if end_date:
            query = query.filter(Trade.trade_time <= end_date)
        
        trades = query.all()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'avg_r_multiple': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        avg_r_multiple = sum(t.r_multiple for t in trades) / total_trades if total_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown (simplified)
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda x: x.trade_time):
            cumulative_pnl += trade.pnl
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': avg_pnl,
            'avg_r_multiple': avg_r_multiple,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor
        }
    
    def get_setup_performance(self) -> List[Dict[str, Any]]:
        """Get performance by setup"""
        results = []
        
        setups = self.db.query(Setup).all()
        for setup in setups:
            trades = self.db.query(Trade).filter(Trade.setup_id == setup.id).all()
            
            if not trades:
                continue
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            win_rate = (winning_trades / total_trades) * 100
            total_pnl = sum(t.pnl for t in trades)
            avg_r_multiple = sum(t.r_multiple for t in trades) / total_trades
            
            results.append({
                'setup_name': setup.name,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_r_multiple': avg_r_multiple
            })
        
        return results

def get_db_session():
    """Get database session"""
    return SessionLocal()
