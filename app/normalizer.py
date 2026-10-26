import numpy as np
import pandas as pd
from typing import List, Dict, Any
from app.config import CONTRACT_SPECS, COST_THRESHOLD_PCT, MIN_VOLUME_THRESHOLD

class MCXQuantEngine:

    @staticmethod
    def map_row_headers(df: pd.DataFrame) -> pd.DataFrame:
        """Normalizes varied MCX CSV column names to unified headers."""
        column_map = {}
        for col in df.columns:
            clean_col = col.strip().upper()
            if clean_col in ['SYMBOL', 'INSTRUMENT', 'CONTRACT', 'SYMBOL_NAME']:
                column_map[col] = 'SYMBOL'
            elif clean_col in ['EXPIRY_DT', 'EXPIRY', 'EXPIRY_DATE', 'MATURITY']:
                column_map[col] = 'EXPIRY_DT'
            elif clean_col in ['CLOSE', 'CLOSE_PRICE', 'SETTLEMENT', 'LAST_PRICE']:
                column_map[col] = 'CLOSE'
            elif clean_col in ['VOLUME', 'VOL', 'QTY', 'TRADED_QTY']:
                column_map[col] = 'VOLUME'
            elif clean_col in ['PURITY', 'FINENESS']:
                column_map[col] = 'PURITY'

        df = df.rename(columns=column_map)
        
        if 'PURITY' not in df.columns:
            df['PURITY'] = np.nan
            
        return df

    @classmethod
    def process_bhavcopy(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        df = cls.map_row_headers(df)
        
        # Clean and filter valid MCX Gold contracts
        df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
        df = df[df['SYMBOL'].isin(CONTRACT_SPECS.keys())].copy()

        if df.empty:
            return []

        df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
        df['VOLUME'] = pd.to_numeric(df['VOLUME'], errors='coerce').fillna(0)

        # 1. Calculate Normalized 1g Price (999 Purity Equivalent)
        def calc_norm_price(row):
            spec = CONTRACT_SPECS[row['SYMBOL']]
            active_purity = row['PURITY'] if pd.notna(row['PURITY']) and row['PURITY'] > 0 else spec['purity']
            base_1g = row['CLOSE'] / spec['quote_g']
            norm_1g = base_1g * (999.0 / active_purity)
            return round(norm_1g, 2), active_purity

        results = df.apply(calc_norm_price, axis=1)
        df['norm1gPrice'] = [r[0] for r in results]
        df['PURITY'] = [r[1] for r in results]

        # 2. Compute Benchmark Average 1g Price per Expiry Term
        liquid_df = df[df['VOLUME'] >= MIN_VOLUME_THRESHOLD]
        benchmarks = liquid_df.groupby('EXPIRY_DT')['norm1gPrice'].mean().to_dict()

        # 3. Calculate Relative Deviation (%) & Signals
        def assign_metrics(row):
            exp = row['EXPIRY_DT']
            bench = benchmarks.get(exp, row['norm1gPrice'])
            bench = round(bench, 2)
            
            dev_pct = ((row['norm1gPrice'] - bench) / bench) if bench > 0 else 0.0
            dev_pct_val = round(dev_pct * 100, 2)

            if row['VOLUME'] < MIN_VOLUME_THRESHOLD:
                signal = 'THIN LIQUIDITY'
            elif dev_pct > COST_THRESHOLD_PCT:
                signal = 'OVERPRICED'
            elif dev_pct < -COST_THRESHOLD_PCT:
                signal = 'UNDERPRICED'
            else:
                signal = 'QUIET / Neutral'

            return pd.Series([bench, dev_pct_val, signal])

        df[['benchmark', 'devPct', 'signal']] = df.apply(assign_metrics, axis=1)

        return df.to_dict(orient='records')