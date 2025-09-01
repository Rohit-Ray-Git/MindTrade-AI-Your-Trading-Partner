"""
Database models for MindTrade AI
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Setup(Base):
    """Trading setup types"""
    __tablename__ = "setups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trades = relationship("Trade", back_populates="setup")

class Trade(Base):
    """Trade records"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # Long/Short
    entry_price = Column(Float, nullable=False)
    stop_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    account_equity = Column(Float, nullable=False)
    risk_percent = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    r_multiple = Column(Float, nullable=False)
    trade_time = Column(DateTime, nullable=False)
    entry_time = Column(DateTime)  # Optional entry time for compatibility
    exit_time = Column(DateTime)   # Optional exit time for compatibility
    source = Column(String(20), default="manual")  # manual/delta
    exchange = Column(String(50))  # Exchange name (Delta Exchange, etc)
    external_id = Column(String(100))  # External trade ID from exchange
    fees = Column(Float, default=0.0)  # Trading fees
    logic = Column(Text)  # Trade reasoning
    notes = Column(Text)  # General notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    setup_id = Column(Integer, ForeignKey("setups.id"))
    
    # Relationships
    setup = relationship("Setup", back_populates="trades")
    psychology_notes = relationship("PsychologyNote", back_populates="trade", cascade="all, delete-orphan")
    agent_outputs = relationship("AgentOutput", back_populates="trade", cascade="all, delete-orphan")

class PsychologyNote(Base):
    """Psychology and behavioral notes for trades"""
    __tablename__ = "psychology_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    note_text = Column(Text, nullable=False)
    self_tags = Column(JSON)  # Array of user-defined tags
    nlp_tags = Column(JSON)   # Array of AI-detected tags
    sentiment_score = Column(Float)  # -1 to 1
    confidence_score = Column(Float)  # 0 to 1
    fear_score = Column(Float)  # 0 to 1
    greed_score = Column(Float)  # 0 to 1
    patience_score = Column(Float)  # 0 to 1
    fomo_score = Column(Float)  # 0 to 1
    revenge_score = Column(Float)  # 0 to 1
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trade = relationship("Trade", back_populates="psychology_notes", foreign_keys=[trade_id])

class AgentOutput(Base):
    """AI agent analysis outputs"""
    __tablename__ = "agent_outputs"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)  # TradeAnalyzer, PatternFinder, etc.
    output_type = Column(String(50), nullable=False)  # analysis, pattern, coaching, etc.
    output_data = Column(JSON, nullable=False)  # Structured output data
    confidence_score = Column(Float)  # 0 to 1
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    trade = relationship("Trade", back_populates="agent_outputs")

class User(Base):
    """User accounts (for future authentication)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Settings(Base):
    """Application settings"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
