from pydantic import BaseModel
from typing import List, Optional

class ContractResult(BaseModel):
    SYMBOL: str
    EXPIRY_DT: str
    CLOSE: float
    VOLUME: float
    PURITY: float
    norm1gPrice: float
    benchmark: float
    devPct: float
    signal: str

class BacktestPoint(BaseModel):
    month: str
    strategyEquity: float
    benchmarkEquity: float

class BacktestResponse(BaseModel):
    cagr: str
    sharpe: str
    maxDrawdown: str
    winRate: str
    equityCurve: List[BacktestPoint]