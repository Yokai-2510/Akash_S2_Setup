# data_pipeline/indicator_calculator.py

"""
INDICATOR CALCULATION ENGINE.
Computes technical indicators (RSI, TSI, etc.) using pandas-ta.
Generates 'snapshot' for Decision Engine and saves history to Parquet.
"""

import pandas as pd
import pandas_ta as ta
import json
import os
import datetime
from tqdm import tqdm
from typing import Dict, Any, List
from utils.logger import setup_logger

log = setup_logger()
REQUIRED_COLS = ['open', 'high', 'low', 'close', 'volume']


def process_indicator_calculation(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Entry Point: Computes indicators for all ETFs and timeframes.
    Skips if data hasn't changed since last calculation.
    """
    log.info("=== INDICATOR CALCULATION STARTED ===", tags=["CALC", "START"])
    
    # Check if we should skip
    force_recalc = universal_data['system']['debug_flags'].get('force_indicator_recalc', False)
    
    if not force_recalc:
        # Check if parquet history exists and is recent
        history_path = os.path.join(universal_data['system']['project_root'], 'source', 'data', 'indicator_history.parquet')
        if os.path.exists(history_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(history_path))
            # If calculated within last hour, skip
            if (datetime.now() - file_mtime).total_seconds() < 3600:
                log.info(f"Indicator cache fresh ({file_mtime.strftime('%H:%M')}), loading from parquet", tags=["CALC", "SKIP"])
                try:
                    full_df = pd.read_parquet(history_path)
                    # Extract latest snapshot
                    snapshot_rows = []
                    for (etf, tf), group in full_df.groupby(['ETF', 'Timeframe']):
                        snapshot_rows.append(group.iloc[-1])
                    if snapshot_rows:
                        universal_data['market_data']['indicator_snapshot_df'] = pd.DataFrame(snapshot_rows)
                        log.info(f"Loaded snapshot: {len(snapshot_rows)} rows from cache", tags=["CALC", "CACHE"])
                        return universal_data
                except Exception as e:
                    log.warning(f"Cache load failed: {e}, recalculating", tags=["CALC", "WARNING"])
   
    # Configs
    universe = universal_data['configs']['universe_settings']
    indicators_config = universal_data['configs']['indicator_settings']
    ohlcv_paths = universal_data['market_data']['ohlcv_file_paths']
   
    etfs = universe['etfs_to_track']
    timeframes = universe['timeframes_to_calculate']
   
    all_snapshots = []
    full_history_dfs = []
   
    for etf in tqdm(etfs, desc="Calc Indicators"):
        path = ohlcv_paths.get(etf)
        if not path or not os.path.exists(path):
            continue
           
        try:
            # 1. Load & Prep Data
            df_1m = _load_and_prep_ohlcv(path)
            if df_1m.empty:
                continue
               
            for tf in timeframes:
                # 2. Resample
                df_resampled = _resample_data(df_1m, tf)
                if df_resampled.empty:
                    continue
               
                # 3. Calculate Indicators
                df_calc = _apply_indicators(df_resampled, indicators_config)
               
                # 4. Tag Data
                df_calc['ETF'] = etf
                df_calc['Timeframe'] = tf
               
                # 5. Store latest row for Snapshot
                latest = df_calc.iloc[[-1]].copy()
                all_snapshots.append(latest)
               
                # 6. Store for History (optional, can be large)
                # Reset index to keep timestamp column
                full_history_dfs.append(df_calc.reset_index())
               
        except Exception as e:
            log.error(f"Calc failed for {etf}: {e}", tags=["CALC", "ERROR"])
    # Combine Snapshots
    if all_snapshots:
        snapshot_df = pd.concat(all_snapshots, ignore_index=True)
        universal_data['market_data']['indicator_snapshot_df'] = snapshot_df
        log.info(f"Snapshot created: {len(snapshot_df)} rows.", tags=["CALC", "SNAPSHOT"])
    else:
        universal_data['market_data']['indicator_snapshot_df'] = pd.DataFrame()
        log.warning("No snapshot data generated.", tags=["CALC", "WARNING"])
    # Save Full History (Parquet)
    if full_history_dfs:
        _save_history_parquet(universal_data, full_history_dfs)
    return universal_data


def _load_and_prep_ohlcv(path: str) -> pd.DataFrame:
    """Loads JSON, converts to DataFrame with DatetimeIndex."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
       
        # Upstox format: [timestamp, open, high, low, close, volume, oi]
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
       
        # Ensure numeric
        cols = ['open', 'high', 'low', 'close', 'volume']
        df[cols] = df[cols].apply(pd.to_numeric)
       
        return df[cols]
    except:
        return pd.DataFrame()


def _resample_data(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resamples 1m data to target timeframe (e.g., '1W')."""
    # Map config timeframe to pandas offset aliases
    # 1d -> 1D, 1W -> 1W, 1h -> 1h
    tf_map = {'1m': '1min', '1h': '1h', '1d': '1D', '1W': '1W-FRI'}
    # Note: 1W-FRI aligns weekly candles to Friday close
   
    rule = tf_map.get(timeframe, timeframe)
   
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
   
    try:
        resampled = df.resample(rule).agg(agg_dict).dropna()
        return resampled
    except:
        return pd.DataFrame()


def _apply_indicators(df: pd.DataFrame, config: List[Dict]) -> pd.DataFrame:
    """Applies pandas-ta indicators based on config."""
    # Pandas-TA requires lowercase columns
   
    for ind in config:
        name = ind.get('name')
        params = ind.get('params', {})
       
        # Skip if not enabled (if 'enabled' key exists)
        if not ind.get('enabled', True):
            continue
           
        try:
            # Dynamic call to df.ta.indicator()
            if hasattr(df.ta, name):
                getattr(df.ta, name)(append=True, **params)
        except Exception as e:
            # Log warning but don't crash
            # log.warning(f"Indicator {name} failed: {e}")
            pass
           
    return df


def _save_history_parquet(universal_data: Dict[str, Any], dfs: List[pd.DataFrame]):
    """Saves full history to parquet for analysis."""
    try:
        full_df = pd.concat(dfs, ignore_index=True)
        path = os.path.join(universal_data['system']['project_root'], 'source', 'data', 'indicator_history.parquet')
        full_df.to_parquet(path, compression='snappy')
        log.info(f"Saved full history to {os.path.basename(path)}", tags=["CALC", "HISTORY"])
    except Exception as e:
        log.error(f"Failed to save parquet: {e}", tags=["CALC", "ERROR"])