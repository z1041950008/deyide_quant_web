from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.holiday import TradingHoliday
from app.models.database import get_db

async def is_trading_day(date: datetime, db: AsyncSession = None) -> bool:
    """
    判断是否为A股交易日
    - 排除周末
    - 排除法定节假日
    """
    # 检查是否为周末
    if date.weekday() >= 5:
        return False
        
    # 检查数据库中的节假日
    if db is None:
        db = next(get_db())
    
    query = select(TradingHoliday).where(TradingHoliday.date == date.date())
    result = await db.execute(query)
    holiday = result.scalar_one_or_none()
    
    return holiday is None 