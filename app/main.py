import io
import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

from app.normalizer import MCXQuantEngine
from app.backtester import WalkForwardBacktester
from app.schemas import ContractResult, BacktestResponse

app = FastAPI(
    title="MCX Gold Futures Relative Value Engine",
    description="Backend Quantitative API for MCX Bhavcopy Normalization & Signal Generation",
    version="2.4.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "engine": "MCX Gold Relative Value Engine v2.4"}

@app.post("/api/v1/normalize", response_model=List[ContractResult])
async def normalize_bhavcopy(file: UploadFile = File(...)):
    """Uploads and parses MCX Bhavcopy CSV file, returning normalized prices and signals."""
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

    try:
        content = await file.read()
        df_raw = pd.read_csv(io.BytesIO(content))
        processed_records = MCXQuantEngine.process_bhavcopy(df_raw)
        return processed_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@app.post("/api/v1/backtest", response_model=BacktestResponse)
def execute_backtest(records: List[ContractResult]):
    """Runs walk-forward backtest analysis using processed contract data."""
    data_dicts = [r.model_dump() for r in records]
    results = WalkForwardBacktester.run_simulation(data_dicts)
    return results

# --- Serve Frontend UI at Root ---
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Mount static assets (CSS, JS, templates)
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")