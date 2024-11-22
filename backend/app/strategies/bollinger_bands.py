from typing import List, Dict
import pandas as pd
import numpy as np
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    def __init__(
        self,
        name: str = "布林带策略",
        description: str = "基于布林带的交易策略",
        window: int = 20,
        std_dev: float = 2.0,
        volume_factor: float = 2.0,
    ):
        super().__init__(name, description)
        self.window = window
        self.std_dev = std_dev
        self.volume_factor = volume_factor
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['middle_band'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper_band'] = df['middle_band'] + (df['std'] * self.std_dev)
        df['lower_band'] = df['middle_band'] - (df['std'] * self.std_dev)
        return df
    
    def check_volume_surge(self, df: pd.DataFrame) -> bool:
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(window=self.window).mean().iloc[-1]
        return current_volume > avg_volume * self.volume_factor
    
    def select_stocks(self, date: str, df: pd.DataFrame) -> List[str]:
        # Sort stocks by circulating_market_value and return top 300 stock codes
        sorted_df = df.sort_values('circulating_value', ascending=False)
        return sorted_df['code'].head(300).tolist()
    
    def generate_signals(self, stock_data: pd.DataFrame) -> Dict[str, str]:
        signals = {}
        
        for stock_code in stock_data['code'].unique():
            df = stock_data[stock_data['code'] == stock_code].copy()
            if len(df) < self.window:
                continue
            
            df = self.calculate_bollinger_bands(df)
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            if (
                latest['close'] <= latest['lower_band'] and
                prev['close'] > prev['lower_band'] and 
                self.check_volume_surge(df)
            ):
                signals[stock_code] = 'buy'
            elif (
                latest['close'] >= latest['upper_band'] or
                latest['close'] < latest['middle_band']
            ):
                signals[stock_code] = 'sell'
            else:
                signals[stock_code] = 'hold'
        
        return signals
