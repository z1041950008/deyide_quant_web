from datetime import datetime
from app.models import TradingHoliday
from app.models.database import SessionLocal

def init_holidays_2024():
    """初始化2024年节假日数据"""
    holidays_2024 = [
        {"date": "2024-01-01", "name": "元旦"},
        {"date": "2024-02-10", "name": "春节"},
        {"date": "2024-02-11", "name": "春节"},
        {"date": "2024-02-12", "name": "春节"},
        {"date": "2024-02-13", "name": "春节"},
        {"date": "2024-02-14", "name": "春节"},
        {"date": "2024-02-15", "name": "春节"},
        {"date": "2024-02-16", "name": "春节"},
        {"date": "2024-04-04", "name": "清明节"},
        {"date": "2024-05-01", "name": "劳动节"},
        {"date": "2024-06-10", "name": "端午节"},
        {"date": "2024-09-17", "name": "中秋节"},
        {"date": "2024-10-01", "name": "国庆节"},
        {"date": "2024-10-02", "name": "国庆节"},
        {"date": "2024-10-03", "name": "国庆节"},
        {"date": "2024-10-04", "name": "国庆节"},
        {"date": "2024-10-05", "name": "国庆节"},
    ]
    
    db = SessionLocal()
    try:
        for holiday in holidays_2024:
            db_holiday = TradingHoliday(
                date=datetime.strptime(holiday["date"], "%Y-%m-%d").date(),
                name=holiday["name"]
            )
            db.add(db_holiday)
        db.commit()
        print("2024年节假日数据初始化完成")
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_holidays_2024() 