import logging
from datetime import datetime
import traceback
from typing import List, Dict
from sqlalchemy import and_

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.stock import BollSignal
from app.tasks.boll_screener import BollScreener

logger = logging.getLogger(__name__)

class StockScreenerTask:
    def is_trading_day(self) -> bool:
        """检查是否为交易日"""
        try:
            import akshare as ak
            trade_cal = ak.tool_trade_date_hist_sina()
            today = datetime.now().strftime('%Y-%m-%d')
            return today in trade_cal['trade_date'].values
        except Exception as e:
            logger.error(f"检查交易日失败: {str(e)}")
            return False

    def process_signals(self, db, buy_signals: List[Dict], sell_signals: List[Dict], signal_date: datetime = None) -> None:
        """处理买入和卖出信号
        
        Args:
            db: 数据库会话
            buy_signals: 买入信号列表
            sell_signals: 卖出信号列表
            signal_date: 信号产生的日期，用于回测。默认为 None，表示使用当前时间
        """
        try:
            # 如果没有指定日期，使用当前时间
            signal_date = signal_date or datetime.now()
            
            # 处理卖出信号
            sell_codes = {signal['stock_code'] for signal in sell_signals}
            if sell_codes:
                # 查找所有要卖出的持仓记录
                holding_positions = db.query(BollSignal).filter(
                    and_(
                        BollSignal.stock_code.in_(sell_codes),
                        BollSignal.trade_status == '持仓中'
                    )
                ).all()

                # 更新卖出信息
                for position in holding_positions:
                    sell_signal = next(s for s in sell_signals if s['stock_code'] == position.stock_code)
                    position.sell_date = signal_date
                    position.sell_price = sell_signal['close_price']
                    position.trade_status = '已卖出'
                    # 计算收益率
                    position.profit_rate = (position.sell_price - position.buy_price) / position.buy_price * 100
                    # 计算持仓天数
                    position.holding_period = (position.sell_date - position.buy_date).days
                    # 计算最大回撤（如果有历史价格数据的话）
                    # position.max_drawdown = calculate_max_drawdown(position)
                    db.add(position)

            # 处理买入信号
            new_signals = [
                BollSignal(
                    stock_code=signal['stock_code'],
                    stock_name=signal['stock_name'],
                    score=signal.get('score'),
                    roe=signal.get('roe'),
                    profit_growth=signal.get('profit_growth'),
                    gross_margin=signal.get('gross_margin'),
                    debt_ratio=signal.get('debt_ratio'),
                    cash_ratio=signal.get('cash_ratio'),
                    revenue_growth=signal.get('revenue_growth'),
                    buy_date=signal_date,
                    buy_price=signal['close_price'],
                    trade_status='持仓中'
                ) for signal in buy_signals
            ]
            
            if new_signals:
                db.bulk_save_objects(new_signals)
            
            db.commit()
            logger.info(f"成功处理 {len(new_signals)} 条买入信号和 {len(holding_positions)} 条卖出信号")
            
        except Exception as e:
            db.rollback()
            logger.error(f"信号处理失败: {str(e)}")
            raise

    def execute(self) -> None:
        """执行选股任务"""
        try:
            if not self.is_trading_day():
                logger.info("今天不是交易日，跳过执行")
                return

            logger.info("开始执行选股任务")
            
            db = SessionLocal()
            try:
                screener = BollScreener(
                    include_cyb=settings.INCLUDE_CYB,
                    include_kcb=settings.INCLUDE_KCB,
                    top_n=settings.TOP_N_STOCKS
                )
                buy_signals, sell_signals = screener.run()
                
                if buy_signals or sell_signals:
                    self.process_signals(db, buy_signals, sell_signals, datetime.now())
                    logger.info(f"选股任务完成，买入信号 {len(buy_signals)} 只，卖出信号 {len(sell_signals)} 只")
                else:
                    logger.warning("没有符合条件的股票")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"选股任务执行失败: {str(e)}")
            logger.error(traceback.format_exc()) 

    def backtest_historical_data(self, start_date: str, end_date: str) -> None:
        """回测历史数据并写入数据库
        
        Args:
            start_date: 开始日期，格式：'YYYY-MM-DD'
            end_date: 结束日期，格式：'YYYY-MM-DD'
        """
        try:
            logger.info(f"开始回测从 {start_date} 到 {end_date} 的历史数据")
            
            # 获取交易日历
            import akshare as ak
            trade_cal = ak.tool_trade_date_hist_sina()
            trading_days = trade_cal[
                (trade_cal['trade_date'] >= start_date) & 
                (trade_cal['trade_date'] <= end_date)
            ]['trade_date'].values
            
            db = SessionLocal()
            try:
                screener = BollScreener(
                    include_cyb=settings.INCLUDE_CYB,
                    include_kcb=settings.INCLUDE_KCB,
                    top_n=settings.TOP_N_STOCKS
                )
                
                # 遍历每个交易日
                for trade_date in trading_days:
                    logger.info(f"正在处理交易日: {trade_date}")
                    
                    # 设置当前日期为回测日期
                    current_date = datetime.strptime(trade_date, '%Y-%m-%d')
                    
                    # 运行策略获取信号
                    buy_signals, sell_signals = screener.run(trade_date=trade_date)
                    
                    if buy_signals or sell_signals:
                        # 处理信号时使用历史日期
                        with db.begin():
                            self.process_signals(
                                db, 
                                buy_signals, 
                                sell_signals, 
                                signal_date=current_date
                            )
                        logger.info(f"{trade_date} 处理完成：买入信号 {len(buy_signals)} 只，卖出信号 {len(sell_signals)} 只")
                    
                logger.info("历史数据回测完成")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"历史数据回测失败: {str(e)}")
            logger.error(traceback.format_exc()) 

# 回测过去一年的数据
screener_task = StockScreenerTask()
start_date = '2023-03-20'  # 一年前的日期
end_date = '2024-03-20'    # 当前日期
screener_task.backtest_historical_data(start_date, end_date)