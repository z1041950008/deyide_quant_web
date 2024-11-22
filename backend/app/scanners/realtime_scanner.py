from typing import List, Dict
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from app.strategies.bollinger_bands import BollingerBandsStrategy

class RealtimeScanner:
    def __init__(self):
        self.strategy = BollingerBandsStrategy()

    async def scan_today_stocks(self) -> Dict[str, List[str]]:
        """
        扫描今天符合布林带策略的股票
        返回买入和卖出信号列表
        """
        # 获取当前日期
        today = datetime.now().strftime('%Y%m%d')
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        # 获取A股股票列表
        stock_list = ak.stock_zh_a_spot_em()
        all_signals = {'buy': [], 'sell': [], 'date': today}
        
        # 遍历股票获取数据并分析
        for _, stock in stock_list.iterrows():
            try:
                # 获取单个股票的历史数据
                stock_code = stock['代码']
                df = ak.stock_zh_a_hist(symbol=stock_code, 
                                      start_date=thirty_days_ago,
                                      end_date=today,
                                      adjust="qfq")
                
                # 生成交易信号
                signals = self.strategy.generate_signals(df)
                
                # 将信号添加到结果中
                for code, signal in signals.items():
                    if signal == 'buy':
                        all_signals['buy'].append(code)
                    elif signal == 'sell':
                        all_signals['sell'].append(code)
                        
            except Exception as e:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
                continue
        
        return all_signals