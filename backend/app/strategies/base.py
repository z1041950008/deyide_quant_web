from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.positions: Dict[str, float] = {}
    
    @abstractmethod
    def select_stocks(self, date: str, universe: List[str]) -> List[str]:
        """选股策略"""
        pass
    
    @abstractmethod
    def generate_signals(self, stock_data: pd.DataFrame) -> Dict[str, str]:
        """生成交易信号"""
        pass
    
    def calculate_position_size(self, capital: float, price: float) -> float:
        """计算仓位大小"""
        position = capital * 0.01  # 默认每个股票使用10%资金
        shares = (position / price) // 100 * 100  # 向下取整到100股
        return shares
