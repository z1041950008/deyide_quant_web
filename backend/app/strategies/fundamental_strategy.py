from typing import Dict, List
import pandas as pd
import akshare as ak
from enum import Enum
from .base import BaseStrategy
import traceback  # Add this import

class ModelComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class FundamentalStrategy(BaseStrategy):
    def __init__(
        self,
        name: str = "基本面策略",
        description: str = "基于多维财务指标的交易策略",
        complexity: ModelComplexity = ModelComplexity.MEDIUM,
        buy_threshold: float = 0.7,
        sell_threshold: float = 0.3,
        holding_period: int = 20  # 添加持仓天数参数，默认20天
    ):
        super().__init__(name, description)
        self.complexity = complexity
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.holding_period = holding_period
        self._define_indicators()
        self.position_start_dates = {}  # 记录每个股票的建仓日期

    def select_stocks(self, date: str, df: pd.DataFrame) -> List[str]:
        # 选择市值前300的股票
        sorted_df = df.sort_values('circulating_value', ascending=False)
        return sorted_df['code'].head(10).tolist()

    async def generate_signals(self, stock_data: pd.DataFrame) -> Dict[str, str]:
        """
        根据得分和持仓时间生成交易信号
        Args:
            stock_data: 包含股票代码和交易日期等基础信息的DataFrame
        Returns:
            Dict[str, str]: 股票代码到交易信号的映射
        """
        # 获取当前日期
        current_date = pd.to_datetime(stock_data['date'].iloc[0])
        stock_codes = stock_data['code'].unique().tolist()
        
        # 获取基本面数据
        fundamental_data = await self.get_fundamental_data(stock_codes)
        if fundamental_data.empty:
            return {}
            
        # 计算综合得分
        scores = self.calculate_score(fundamental_data)
        signals = {}
        
        for stock_code in stock_codes:
            # 检查是否已持仓
            if stock_code in self.position_start_dates:
                start_date = self.position_start_dates[stock_code]
                holding_days = (current_date - start_date).days
                
                # 如果达到持仓期限，生成卖出信号
                if holding_days >= self.holding_period:
                    signals[stock_code] = 'sell'
                    self.position_start_dates.pop(stock_code)  # 移除持仓记录
                else:
                    signals[stock_code] = 'hold'
            else:
                # 对于未持仓的股票，根据得分决定是否买入
                score = scores.get(stock_code, 0)
                if score >= self.buy_threshold:
                    signals[stock_code] = 'buy'
                    self.position_start_dates[stock_code] = current_date  # 记录建仓日期
                else:
                    signals[stock_code] = 'hold'
                
        return signals

    def _define_indicators(self):
        """
        定义不同复杂度下的指标和权重
        指标权重为正表示越大越好，为负表示越小越好
        """
        # 简单模型：4个核心指标
        self.simple_indicators = {
            'pe_ratio': -0.3,        # 市盈率（越小越好）
            'pb_ratio': -0.2,        # 市净率（越小越好）
            'roe': 0.3,              # 净资产收益率（越大越好）
            'retained_earnings': 0.2, # 每股未分配利润（越大越好）
        }

        # 中等模型：8个指标
        self.medium_indicators = {
            **self.simple_indicators,
            'debt_ratio': -0.1,      # 资产负债率（越小越好）
            'gross_margin': 0.1,     # 毛利率（越大越好）
            'net_profit_growth': 0.1,# 净利润增长率（越大越好）
            'operating_cash_flow': 0.1, # 经营性现金流（越大越好）
        }

        # 复杂模型：12个指标
        self.complex_indicators = {
            **self.medium_indicators,
            'inventory_turnover': 0.05,  # 存货周转率（越大越好）
            'receivables_turnover': 0.05,# 应收账款周转率（越大越好）
            'current_ratio': 0.05,       # 流动比率（越大越好）
            'quick_ratio': 0.05,         # 速动比率（越大越好）
        }

    def _normalize_data(self, df: pd.DataFrame, column: str) -> pd.Series:
        """
        使用Min-Max标准化将数据归一化到[0,1]区间
        """
        min_val = df[column].min()
        max_val = df[column].max()
        if max_val == min_val:
            return pd.Series(0.5, index=df.index)
        return (df[column] - min_val) / (max_val - min_val)

    def _get_current_indicators(self) -> Dict[str, float]:
        """
        根据复杂度返回当前使用的指标和权重
        """
        if self.complexity == ModelComplexity.SIMPLE:
            return self.simple_indicators
        elif self.complexity == ModelComplexity.MEDIUM:
            return self.medium_indicators
        else:
            return self.complex_indicators

    def calculate_score(self, stock_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算每只股票的综合得分
        """
        indicators = self._get_current_indicators()
        scores = {}

        for stock_code in stock_data.index:
            stock = stock_data.loc[stock_code]
            score = 0
            valid_weights_sum = 0

            for indicator, weight in indicators.items():
                if indicator in stock and pd.notna(stock[indicator]):
                    normalized_value = self._normalize_data(stock_data, indicator).loc[stock_code]
                    # 如果权重为负，则将归一化值反转
                    if weight < 0:
                        normalized_value = 1 - normalized_value
                        weight = abs(weight)
                    score += normalized_value * weight
                    valid_weights_sum += abs(weight)

            # 根据有效权重重新归一化得分
            if valid_weights_sum > 0:
                scores[stock_code] = score / valid_weights_sum
            else:
                scores[stock_code] = 0

        return scores

    def _process_numeric_value(self, value: str) -> float:
        """
        处理带有单位的数值字符串，处理空值和无效值
        """
        # 处理空值或不存在的情况
        if value is None or pd.isna(value) or value == '':
            return 0.0
        
        if not isinstance(value, (str, int, float)):
            return 0.0
            
        try:
            # 如果是数字类型，直接转换
            if isinstance(value, (int, float)):
                return float(value)
            
            # 去除空格
            value = value.strip()
            
            # 处理百分比
            if value.endswith('%'):
                return float(value.rstrip('%')) / 100
            
            # 处理金额单位
            unit_multipliers = {
                '万亿': 1e12,
                '亿': 1e8,
                '万': 1e4,
            }
            
            for unit, multiplier in unit_multipliers.items():
                if value.endswith(unit):
                    return float(value.rstrip(unit)) * multiplier
                    
            return float(value)
            
        except (ValueError, TypeError):
            return 0.0  # 转换失败时返回0

    async def get_fundamental_data(self, stock_codes: List[str]) -> pd.DataFrame:
        """
        获取股票的基本面数据，使用异步并行处理
        """
        from concurrent.futures import ThreadPoolExecutor
        import asyncio
        
        async def get_single_stock_data(stock_code: str) -> tuple[str, dict]:
            try:
                # 使用 ThreadPoolExecutor 处理同步调用
                with ThreadPoolExecutor() as executor:
                    financial_data = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")
                    )
                    realtime_data = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: ak.stock_zh_a_spot_em()
                    )
                
                if financial_data.empty or realtime_data.empty:
                    raise ValueError("无法获取数据")
                    
                latest_data = financial_data.iloc[0]
                stock_data = realtime_data[realtime_data['代码'] == stock_code].iloc[0]
                
                return stock_code, {
                    'pe_ratio': self._process_numeric_value(stock_data.get('市盈率-动态')),
                    'pb_ratio': self._process_numeric_value(stock_data.get('市净率')),
                    'roe': self._process_numeric_value(latest_data.get('净资产收益率')),
                    'retained_earnings': self._process_numeric_value(latest_data.get('每股未分配利润')),
                    'debt_ratio': self._process_numeric_value(latest_data.get('资产负债率')),
                    'gross_margin': self._process_numeric_value(latest_data.get('销售毛利率')),
                    'net_profit_growth': self._process_numeric_value(latest_data.get('净利润同比增长率')),
                    'operating_cash_flow': self._process_numeric_value(latest_data.get('每股经营现金流')),
                    'inventory_turnover': self._process_numeric_value(latest_data.get('存货周转率')),
                    'receivables_turnover': 365 / self._process_numeric_value(latest_data.get('应收账款周转天数', 365)),
                    'current_ratio': self._process_numeric_value(latest_data.get('流动比率')),
                    'quick_ratio': self._process_numeric_value(latest_data.get('速动比率'))
                }
                
            except Exception as e:
                print(f"获取股票 {stock_code} 基本面数据时出错: {str(e)}")
                print(traceback.format_exc())

                return stock_code, None
        
        # 并行获取所有股票数据
        tasks = [get_single_stock_data(code) for code in stock_codes]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉失败的数据并构建 DataFrame
        valid_data = dict(filter(lambda x: x[1] is not None, results))
        if not valid_data:
            return pd.DataFrame()
            
        return pd.DataFrame.from_dict(valid_data, orient='index') 