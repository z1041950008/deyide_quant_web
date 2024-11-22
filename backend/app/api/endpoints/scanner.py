from fastapi import APIRouter, Depends
from app.scanners.realtime_scanner import RealtimeScanner
from app.dependencies import get_scanner

router = APIRouter()

@router.get("/scan/bollinger")
async def scan_bollinger_stocks(
    scanner: RealtimeScanner = Depends(get_scanner)
):
    """获取当天符合布林带策略的股票"""
    return await scanner.scan_today_stocks() 