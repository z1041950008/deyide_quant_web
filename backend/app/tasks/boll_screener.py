import pandas as pd
import numpy as np
from datetime import datetime
import akshare as ak
from typing import List, Dict

class StockScorer:
    def __init__(self):
        # 定义财务指标权重
        self.weights = {
            'ROE': 0.2,              # 净资产收益率
            'profit_growth': 0.15,    # 净利润增长率
            'gross_margin': 0.15,     # 毛利率
            'debt_ratio': -0.1,       # 资产负债率（负相关）
            'pe_ratio': -0.1,         # 市盈率（负相关）
            'pb_ratio': -0.1,         # 市净率（负相关）
            'revenue_growth': 0.1,    # 营收增长率
            'cash_ratio': 0.1         # 现金比率
        }
        
    def get_financial_data(self, stock_code: str) -> Dict:
        """获取股票财务指标"""
        try:
            # 获取主要财务指标
            financial = ak.stock_financial_analysis_indicator(stock=stock_code)
            
            # 获取最新一期的财务数据
            latest = financial.iloc[0]
            prev_year = financial.iloc[4]  # 去年同期
            
            return {
                'ROE': latest['净资产收益率(%)'],
                'profit_growth': (latest['净利润'] - prev_year['净利润']) / abs(prev_year['净利润']) * 100,
                'gross_margin': latest['销售毛利率(%)'],
                'debt_ratio': latest['资产负债比率(%)'],
                'cash_ratio': latest['现金比率(%)'],
                'revenue_growth': (latest['营业收入'] - prev_year['营业收入']) / abs(prev_year['营业收入']) * 100
            }
        except Exception as e:
            print(f"获取 {stock_code} 财务数据失败: {str(e)}")
            return None

    def normalize_score(self, data: Dict) -> float:
        """计算归一化后的得分"""
        score = 0
        for metric, weight in self.weights.items():
            if metric in data:
                # 将数据归一化到0-1之间
                normalized_value = (data[metric] - min(data[metric])) / (max(data[metric]) - min(data[metric]))
                score += normalized_value * weight
        return score

class BollScreener:
    def __init__(self, period=20, std_dev=2, include_cyb=False, include_kcb=False, top_n=10):
        self.period = period
        self.std_dev = std_dev
        self.include_cyb = include_cyb
        self.include_kcb = include_kcb
        self.top_n = top_n  # 最终选取的股票数量
        self.scorer = StockScorer()
        
    def get_stock_list(self):
        """获取符合条件的股票列表"""
        print("正在获取股票列表...")
        
        # 获取所有A股基本信息
        stock_info = ak.stock_zh_a_spot_em()
        
        # 基础过滤：剔除ST和退市股票
        df = stock_info[~stock_info['名称'].str.contains('ST|退')]
        
        # 板块过滤
        if not self.include_cyb:
            df = df[~df['代码'].str.startswith('300')]
        if not self.include_kcb:
            df = df[~df['代码'].str.startswith('688')]
            
        # 获取流通市值数据并排序
        df['流通市值'] = df['流通市值'].astype(float)
        df = df.nsmallest(300, '流通市值')
        
        return df[['代码', '名称']].to_dict('records')

    def check_signals(self, data: pd.DataFrame) -> str:
        """检查布林带买卖信号"""
        # 计算布林带指标
        data['MA'] = data['收盘'].rolling(window=self.period).mean()
        data['STD'] = data['收盘'].rolling(window=self.period).std()
        data['Upper'] = data['MA'] + (self.std_dev * data['STD'])
        data['Lower'] = data['MA'] - (self.std_dev * data['STD'])
        
        # 获取最新数据
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 买入信号：价格从下轨上穿
        if latest['收盘'] > latest['Lower'] and prev['收盘'] <= prev['Lower']:
            return 'BUY'
        # 卖出信号：价格从上轨下穿
        elif latest['收盘'] < latest['Upper'] and prev['收盘'] >= prev['Upper']:
            return 'SELL'
        else:
            return 'HOLD'

    def run(self):
        """主运行函数"""
        print(f"开始布林带选股 - {datetime.now()}")
        
        # 获取初始股票池
        stock_list = self.get_stock_list()
        print(f"初始股票池数量: {len(stock_list)}")
        
        # 存储买卖信号的股票
        buy_signals = []
        sell_signals = []
        
        # 布林带筛选
        for i, stock in enumerate(stock_list, 1):
            try:
                print(f"布林带筛选进度: {i}/{len(stock_list)} - {stock['代码']}")
                stock_data = ak.stock_zh_a_hist(
                    symbol=stock['代码'], 
                    period="daily",
                    start_date="20240101",
                    end_date=datetime.now().strftime("%Y%m%d")
                )
                
                signal = self.check_signals(stock_data)
                if signal == 'BUY':
                    # 获取财务数据并计算得分
                    financial_data = self.scorer.get_financial_data(stock['代码'])
                    if financial_data:
                        score = self.scorer.normalize_score(financial_data)
                        buy_signals.append({
                            'code': stock['代码'],
                            'name': stock['名称'],
                            'score': score,
                            'financial_data': financial_data
                        })
                elif signal == 'SELL':
                    sell_signals.append({
                        'code': stock['代码'],
                        'name': stock['名称']
                    })
                    
            except Exception as e:
                print(f"处理股票 {stock['代码']} 时出错: {str(e)}")
                continue
        
        # 按得分排序买入信号
        buy_signals.sort(key=lambda x: x['score'], reverse=True)
        buy_signals = buy_signals[:self.top_n]  # 只保留得分最高的 top_n 只股票
        
        print(f"\n买入信号数量: {len(buy_signals)}")
        print(f"卖出信号数量: {len(sell_signals)}")
        
        return buy_signals, sell_signals

if __name__ == "__main__":
    screener = BollScreener(include_cyb=False, include_kcb=False, top_n=10)
    buy_signals, sell_signals = screener.run() 