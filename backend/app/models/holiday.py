from sqlalchemy import Column, String, Date
from .database import Base

class TradingHoliday(Base):
    __tablename__ = "trading_holidays"
    
    date = Column(Date, primary_key=True)
    name = Column(String(32))  # 节假日名称，如"春节"、"国庆节" 