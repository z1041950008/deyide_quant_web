from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(500))
    type = Column(String(50))
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    transactions = relationship("Transaction", back_populates="strategy")
    performances = relationship("Performance", back_populates="strategy")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    stock_code = Column(String(20))
    trade_type = Column(String(10))
    price = Column(Float)
    shares = Column(Integer)
    amount = Column(Float)
    trade_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    strategy = relationship("Strategy", back_populates="transactions")

class Performance(Base):
    __tablename__ = "performances"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    date = Column(DateTime)
    total_value = Column(Float)
    cash_balance = Column(Float)
    daily_return = Column(Float)
    cumulative_return = Column(Float)
    drawdown = Column(Float)
    position_count = Column(Integer)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    strategy = relationship("Strategy", back_populates="performances")
