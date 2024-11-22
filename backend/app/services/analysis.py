import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

class PerformanceAnalyzer:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
    
    def calculate_returns(self, daily_values: List[float]) -> pd.Series:
        """计算收益率序列"""
        values = pd.Series(daily_values)
        returns = values.pct_change().fillna(0)
        return returns
    
    def calculate_drawdown(self, daily_values: List[float]) -> pd.Series:
        """计算回撤序列"""
        values = pd.Series(daily_values)
        rolling_max = values.expanding().max()
        drawdowns = values / rolling_max - 1
        return drawdowns
    
    def calculate_metrics(self, daily_values: List[Dict], transactions: List[Dict]) -> Dict:
        """计算策略表现指标"""
        values = [d['value'] for d in daily_values]
        returns = self.calculate_returns(values)
        drawdowns = self.calculate_drawdown(values)
        
        # 计算总收益率和年化收益率
        total_days = len(values)
        total_return = (values[-1] - values[0]) / values[0]
        annual_return = (1 + total_return) ** (252 / total_days) - 1
        
        # 计算最大回撤
        max_drawdown = drawdowns.min()
        
        # 计算夏普比率
        risk_free_rate = 0.03  # 假设无风险利率为3%
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
        
        # 计算交易统计
        trades_df = pd.DataFrame(transactions)
        win_rate = 0
        avg_profit = 0
        total_trades = len(transactions)
        
        if not trades_df.empty:
            profits = []  # 用于存储每对交易的盈亏
            
            for i in range(0, len(trades_df), 2):  # 每两笔交易为一组（买入和卖出）
                if i + 1 < len(trades_df):  # 确保有配对的交易
                    buy_trade = trades_df.iloc[i]
                    sell_trade = trades_df.iloc[i + 1]
                    
                    if buy_trade['type'] == 'buy' and sell_trade['type'] == 'sell':
                        profit = (sell_trade['price'] - buy_trade['price']) * buy_trade['shares']
                        profits.append(profit)
                        trades_df.loc[i:i+1, 'profit'] = profit
            
            if profits:  # 确保有完成的交易
                profitable_trades = len([p for p in profits if p > 0])
                total_pairs = len(profits)
                win_rate = profitable_trades / total_pairs if total_pairs > 0 else 0
                avg_profit = sum(profits) / total_pairs if total_pairs > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit
        }
