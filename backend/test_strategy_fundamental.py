import asyncio
from datetime import datetime, timedelta
from app.strategies.fundamental_strategy import FundamentalStrategy
from app.services.backtest import BacktestService
from app.services.stock_data import StockDataService
import traceback

async def run_strategy_test():
    try:
        print("开始测试基本面策略...")
        
        # 初始化服务和策略
        strategy = FundamentalStrategy(buy_threshold=0.5)
        backtest = BacktestService(initial_capital=10000000.0)
        stock_service = StockDataService()
        
        # 设置回测时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 一年回测
        
        print(f"\n回测区间: {start_date.strftime('%Y%m%d')} 到 {end_date.strftime('%Y%m%d')}")
        
        # 执行回测
        print("\n开始回测...")
        results = await backtest.run_backtest(
            strategy=strategy,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
        
        # 打印回测结果
        print("\n回测结果:")
        try:
            print(f"总收益率: {results.get('total_return', 0):.2%}")
            print(f"年化收益率: {results.get('annual_return', 0):.2%}")
            print(f"夏普比率: {results.get('sharpe_ratio', 0):.2f}")
            print(f"最大回撤: {results.get('max_drawdown', 0):.2%}")
            print(f"胜率: {results.get('win_rate', 0):.2%}")
            print(f"总交易次数: {results.get('total_trades', 0)}")
        except Exception as e:
            print(f"打印结果时出错: {e}")
        
        # 打印交易记录示例
        if backtest.transactions:
            print("\n最近5笔交易:")
            for trade in backtest.transactions[-5:]:
                print(f"日期: {trade['date']}, 股票: {trade['code']}, "
                      f"类型: {trade['type']}, 价格: {trade['price']:.2f}, "
                      f"数量: {trade['shares']}")
        
        # 打印持仓信息
        if backtest.positions:
            print("\n当前持仓:")
            for code, shares in backtest.positions.items():
                print(f"股票: {code}, 持仓数量: {shares}")
        
    except Exception as e:
        print("\n测试过程中出现错误:", e)
        print(traceback.format_exc())
        raise e

def main():
    """主函数"""
    print("量化策略测试程序启动...")
    try:
        asyncio.run(run_strategy_test())
        print("\n测试完成！")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
    finally:
        print("\n程序结束")

if __name__ == "__main__":

    main() 