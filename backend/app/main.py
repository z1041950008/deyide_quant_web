from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from .strategies.bollinger_bands import BollingerBandsStrategy
from .services.backtest import BacktestService

app = FastAPI(
    title="量化交易策略平台",
    description="基于 FastAPI 的量化交易策略回测系统",
    version="1.0.0"
)

# 首页路由
@app.get("/")
async def root():
    return {
        "message": "欢迎使用量化交易策略平台",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# API版本
@app.get("/api/version")
async def get_version():
    return {"version": "1.0.0"}

# 回测请求模型
class BacktestRequest(BaseModel):
    start_date: str
    end_date: str
    window: Optional[int] = 20
    std_dev: Optional[float] = 2.0
    volume_factor: Optional[float] = 2.0
    initial_capital: Optional[float] = 1000000.0

# 布林带策略回测接口
@app.post("/api/backtest/bollinger")
async def run_bollinger_backtest(request: BacktestRequest):
    try:
        strategy = BollingerBandsStrategy(
            window=request.window,
            std_dev=request.std_dev,
            volume_factor=request.volume_factor
        )
        
        backtest = BacktestService(initial_capital=request.initial_capital)
        
        results = await backtest.run_backtest(
            strategy=strategy,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
