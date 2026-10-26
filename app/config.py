"""
Configuration settings for MCX Gold Futures Contract Specifications,
Purity mappings, and Quantitative Signal Thresholds.
"""

CONTRACT_SPECS = {
    'GOLDM':      {'lot_g': 100, 'quote_g': 10, 'purity': 995.0},
    'GOLDTEN':    {'lot_g': 10,  'quote_g': 10, 'purity': 999.0},
    'GOLDGUINEA': {'lot_g': 8,   'quote_g': 8,  'purity': 999.0},
    'GOLDPETAL':  {'lot_g': 1,   'quote_g': 1,  'purity': 999.0}
}

# 0.10% (10 bps) brokerage, STT & bid-ask slippage drag
COST_THRESHOLD_PCT = 0.0010  

# Minimum volume filter to eliminate illiquid / stale quotes
MIN_VOLUME_THRESHOLD = 100