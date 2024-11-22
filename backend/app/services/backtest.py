from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from ..strategies.base import BaseStrategy
from .stock_data import StockDataService
from .analysis import PerformanceAnalyzer
from ..models.database import SessionLocal
from ..models.strategy import Strategy, Transaction, Performance

class BacktestService:
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.transactions = []
        self.daily_values = []
        self.stock_data_service = StockDataService()
        self.analyzer = PerformanceAnalyzer(initial_capital)
    
    async def get_stock_universe(self) -> List[str]:
        """获取股票池"""
        return await self.stock_data_service.get_main_board_stock_list()
    
    async def run_backtest(
        self,
        strategy: BaseStrategy,
        start_date: str,
        end_date: str
    ) -> Dict:
        """运行回测"""
        # 获取股票池
        universe = await self.get_stock_universe()
        selected_stocks = strategy.select_stocks("ss", universe)

        # 获取回测区间的所有交易日
        trading_days = pd.date_range(start_date, end_date, freq='B')
        
        # 一次性获取所有历史数据
        all_stock_data = await self.stock_data_service.get_batch_daily_data(
            selected_stocks,
            start_date,
            end_date
        )
        
        for date in trading_days:
            date_str = date.strftime('%Y%m%d')
            # 选股
            
            # 从历史数据中筛选出当前日期之前的30天数据
            mask = (all_stock_data['date'] <= date_str) & (all_stock_data['date'] >= (date - timedelta(days=30)).strftime('%Y%m%d'))
            stock_data = all_stock_data[mask].copy()
            
            # 生成交易信号
            signals = await strategy.generate_signals(stock_data)
            
            # 执行交易
            await self.execute_trades(signals, stock_data, strategy, date_str)
            
            # 更新每日市值
            self.update_daily_value(date_str, stock_data)
        
        # 计算回测结果
        return self.analyzer.calculate_metrics(self.daily_values, self.transactions)
    
    async def execute_trades(
        self,
        signals: Dict[str, str],
        stock_data: pd.DataFrame,
        strategy: BaseStrategy,
        date: str
    ):
        """执行交易"""
        for stock_code, signal in signals.items():
            latest_price = stock_data[stock_data['code'] == stock_code]['close'].iloc[-1]
            
            if signal == 'buy' and stock_code not in self.positions:
                shares = strategy.calculate_position_size(self.current_capital, latest_price)
                cost = shares * latest_price
                if cost <= self.current_capital:
                    self.positions[stock_code] = shares
                    self.current_capital -= cost
                    self.transactions.append({
                        'date': date,
                        'code': stock_code,
                        'type': 'buy',
                        'price': latest_price,
                        'shares': shares,
                        'cost': cost
                    })
            
            elif signal == 'sell' and stock_code in self.positions:
                shares = self.positions[stock_code]
                revenue = shares * latest_price
                self.current_capital += revenue
                del self.positions[stock_code]
                self.transactions.append({
                    'date': date,
                    'code': stock_code,
                    'type': 'sell',
                    'price': latest_price,
                    'shares': shares,
                    'revenue': revenue
                })
    
    def update_daily_value(self, date: str, stock_data: pd.DataFrame):
        """更新每日市值"""
        total_value = self.current_capital
        
        for stock_code, shares in self.positions.items():
            if stock_code in stock_data['code'].values:
                latest_price = stock_data[stock_data['code'] == stock_code]['close'].iloc[-1]
                total_value += shares * latest_price
        
        self.daily_values.append({
            'date': date,
            'value': total_value
        })
