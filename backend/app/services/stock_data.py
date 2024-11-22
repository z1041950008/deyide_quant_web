import akshare as ak
import pandas as pd
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class StockDataService:
    def __init__(self):
        self.cache_time = timedelta(minutes=30)
    
    @lru_cache(maxsize=100)
    async def get_stock_list_all(self) -> List[str]:
        """获取A股股票列表"""
        try:
            stock_info_df = await self.get_stock_spot_data()
            stock_list = stock_info_df[
                ~stock_info_df['name'].str.contains('ST|退')]
            return stock_list
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    @lru_cache(maxsize=100)
    async def get_main_board_stock_list(self) -> List[str]:
        """获取主板A股股票列表（不包含ST、退市、创业板和科创板）"""
        try:
            stock_info_df = await self.get_stock_spot_data()
            # 过滤ST和退市股票
            # 过滤创业板（以3开头的股票）和科创板（以688开头的股票）
            stock_list = stock_info_df[
                (~stock_info_df['name'].str.contains('ST|退')) & 
                (~stock_info_df['code'].str.startswith('3')) &
                (~stock_info_df['code'].str.startswith('688'))
            ]
            return stock_list
        except Exception as e:
            logger.error(f"获取主板股票列表失败: {e}")
            return pd.DataFrame()
    


    async def get_daily_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取单个股票的日线数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df['code'] = stock_code
            df['date'] = pd.to_datetime(df['date'])
            df = df.copy()
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 数据失败: {e}")
            return pd.DataFrame()

    async def get_batch_daily_data(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """批量获取股票日线数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            包含所有请求股票数据的 DataFrame
        """
        all_data = []
        for stock_code in stock_codes:
            data = await self.get_daily_data(stock_code, start_date, end_date)
            if not data.empty:
                data['code'] = stock_code  # 添加股票代码列
                all_data.append(data)
        
        if not all_data:
            return pd.DataFrame()
        
        return pd.concat(all_data, ignore_index=True)

    async def get_stock_spot_data(self) -> pd.DataFrame:
        """获取A股实时行情数据
        
        Returns:
            DataFrame: 包含以下字段的数据框
                - code: 股票代码
                - name: 股票名称
                - price: 最新价
                - change_percent: 涨跌幅
                - change_amount: 涨跌额
                - volume: 成交量
                - amount: 成交额
                - amplitude: 振幅
                - high: 最高价
                - low: 最低价
                - open: 开盘价
                - pre_close: 昨收价
                - volume_ratio: 量比
                - market_value: 总市值
                - circulating_value: 流通市值
                - turnover_rate: 换手率
                - pe_ttm: 市盈率(TTM)
                - pb: 市净率
        """
        try:
            df = ak.stock_zh_a_spot_em()
            
            # 重命名列为英文
            df = df.rename(columns={
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_percent',
                '涨跌额': 'change_amount',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '量比': 'volume_ratio',
                '总市值': 'market_value',
                '流通市值': 'circulating_value',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe_ttm',
                '市净率': 'pb'
            })
            
            return df
            
        except Exception as e:
            logger.error(f"获取实时行情数据失败: {e}")
            return pd.DataFrame()


