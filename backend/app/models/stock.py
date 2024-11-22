from datetime import datetime
from .database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Index

class BollSignal(Base):
    __tablename__ = 'boll_signals'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(50), nullable=False)
    score = Column(Float)
    roe = Column(Float)
    profit_growth = Column(Float)
    gross_margin = Column(Float)
    debt_ratio = Column(Float)
    cash_ratio = Column(Float)
    revenue_growth = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    buy_date = Column(DateTime)                    # 模拟买入时间
    buy_price = Column(Float)                      # 买入价格
    sell_date = Column(DateTime)                   # 模拟卖出时间
    sell_price = Column(Float)                     # 卖出价格
    profit_rate = Column(Float)                    # 收益率
    max_drawdown = Column(Float)                   # 最大回撤
    holding_period = Column(Integer)               # 持仓天数
    trade_status = Column(String(20))              # 交易状态（如：持仓中、已卖出）

    # 创建索引
    __table_args__ = (
        Index('idx_stock_code_date', 'stock_code', 'created_at'),
        Index('idx_trade_dates', 'buy_date', 'sell_date'),
    ) 