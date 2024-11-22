import pymysql
from .database import engine, Base
from ..core.config import settings

def setup_database():
    """设置数据库"""
    try:
        # 创建数据库连接
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE}")
        print(f"数据库 {settings.MYSQL_DATABASE} 已创建或已存在")

        # 关闭连接
        cursor.close()
        conn.close()

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表已创建")

    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        raise e

if __name__ == "__main__":
    setup_database()