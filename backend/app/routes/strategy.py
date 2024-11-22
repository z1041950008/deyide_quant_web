from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.models import BollSignal
from app.db import session
from sqlalchemy import func
import pandas as pd

templates = Jinja2Templates(directory="templates")
strategy_router = APIRouter()

@strategy_router.get('/bollinger')
async def bollinger_stocks(request: Request):
    # 获取最新日期的布林带信号
    latest_date = session.query(func.max(BollSignal.date)).scalar()
    stocks = session.query(BollSignal)\
        .filter_by(date=latest_date)\
        .order_by(BollSignal.score.desc())\
        .all()
    return templates.TemplateResponse(
        "strategy/bollinger_stocks.html",
        {"request": request, "stocks": stocks}
    )

@strategy_router.get('/history')
async def trade_history(request: Request):
    # 获取历史信号数据
    signals = session.query(BollSignal)\
        .order_by(BollSignal.date.desc(), BollSignal.score.desc())\
        .limit(100)\
        .all()
    return templates.TemplateResponse(
        "strategy/trade_history.html",
        {"request": request, "signals": signals}
    )

@strategy_router.get('/performance')
async def strategy_performance(request: Request):
    # 获取策略绩效统计
    signals_df = pd.read_sql(
        session.query(BollSignal).order_by(BollSignal.date).statement,
        session.bind
    )
    
    performance = calculate_performance(signals_df)
    return templates.TemplateResponse(
        "strategy/performance.html",
        {"request": request, "performance": performance}
    )

def calculate_performance(df):
    # 简单的绩效计算示例
    return {
        'total_signals': len(df),
        'buy_signals': len(df[df['signal'] == 'buy']),
        'sell_signals': len(df[df['signal'] == 'sell']),
        'avg_score': df['score'].mean() if 'score' in df.columns else 0
    } 