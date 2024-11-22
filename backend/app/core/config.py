from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MySQL配置
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "your_password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DATABASE: str = "quant_web"
    
    # SQLAlchemy URL
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # 股票数据相关配置
    DATA_CACHE_EXPIRE: int = 1800  # 30分钟
    MAX_CONCURRENT_REQUESTS: int = 5
    
    COMMISSION_RATE: float = 0.0003  # 手续费率
    MIN_COMMISSION: float = 5.0  # 最低手续费

    # 回测相关配置
    DEFAULT_INITIAL_CAPITAL: float = 1000000.0
    
    # 选股配置
    INCLUDE_CYB: bool = False
    INCLUDE_KCB: bool = False
    TOP_N_STOCKS: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
