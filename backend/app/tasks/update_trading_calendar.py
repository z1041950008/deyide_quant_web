import akshare as ak
from datetime import datetime
from sqlalchemy import delete
from logging import getLogger
import pandas as pd
from app.models import TradingHoliday
from app.db.session import SessionLocal

logger = getLogger(__name__)

def update_trading_calendar():
    """
    更新交易日历数据
    只更新2024年及以后的数据
    """
    try:
        # 获取新浪交易日历数据
        df = ak.tool_trade_date_hist_sina()
        
        # 转换日期列为datetime类型
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 筛选2024年及以后的数据
        start_date = datetime(2024, 1, 1)
        df = df[df['trade_date'] >= start_date]
        
        # 找出非交易日
        # 将日期范围内的所有日期与交易日对比，得出非交易日
        date_range = pd.date_range(start=start_date, end=df['trade_date'].max())
        trading_dates = set(df['trade_date'].dt.date)
        holidays = [d.date() for d in date_range if d.date() not in trading_dates]
        
        db = SessionLocal()
        try:
            # 删除2024年及以后的现有数据
            db.execute(
                delete(TradingHoliday).where(TradingHoliday.date >= start_date)
            )
            
            # 批量插入新的节假日数据
            holiday_records = [
                TradingHoliday(
                    date=holiday,
                    name="非交易日"  # 这里可以根据具体日期判断具体假期名称，如需要
                )
                for holiday in holidays
            ]
            
            db.bulk_save_objects(holiday_records)
            db.commit()
            
            logger.info(f"成功更新交易日历，共更新 {len(holiday_records)} 条节假日记录")
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新交易日历失败: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"获取交易日历数据失败: {str(e)}")
        raise

if __name__ == "__main__":
    update_trading_calendar() 