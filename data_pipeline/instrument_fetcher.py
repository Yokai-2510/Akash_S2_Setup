# data_pipeline/instrument_fetcher.py

"""
INSTRUMENT MASTER FETCHER.
Fetches ETF list from NSE and Upstox to create a unified master mapping.
Handles 'force_nse_refresh' flag and fail-over to Upstox-only mode.
"""

import pandas as pd
import requests
import gzip
import json
import os
import time
from io import BytesIO
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()


def sync_instrument_master(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Entry Point: Creates/Updates 'etf_instrument_master.csv'.
    """
    log.info("=== INSTRUMENT MASTER SYNC STARTED ===", tags=["DATA", "MASTER", "START"])
   
    paths = universal_data['configs']['system_settings']['paths']
    debug_flags = universal_data['system']['debug_flags']
   
    master_path = os.path.join(universal_data['system']['project_root'], paths['instrument_master_file'])
    os.makedirs(os.path.dirname(master_path), exist_ok=True)
   
    # 1. Check Cache vs Force Flag
    force_refresh = debug_flags.get('force_nse_refresh', False)
   
    if not force_refresh and os.path.exists(master_path):
        # Simple check: if file is less than 7 days old
        file_age_days = (time.time() - os.path.getmtime(master_path)) / (24 * 3600)
        if file_age_days < 7:
            log.info(f"Loading cached instrument master ({file_age_days:.1f} days old).", tags=["DATA", "CACHE"])
            universal_data['market_data']['etf_master_list'] = pd.read_csv(master_path)
            return universal_data
           
    log.info("Fetching fresh instrument data...", tags=["DATA", "FETCH"])
   
    try:
        # 2. Fetch Data Sources
        nse_df = _fetch_nse_etfs(universal_data)
        upstox_df = _fetch_upstox_instruments(universal_data)
       
        if upstox_df.empty:
             raise RuntimeError("Critical: Failed to fetch Upstox instruments. Cannot proceed.")
        # 3. Merge logic
        if not nse_df.empty:
            final_df = _merge_sources(nse_df, upstox_df)
        else:
            log.warning("NSE fetch failed. Falling back to Upstox-only mode.", tags=["DATA", "FALLBACK"])
            final_df = _build_upstox_only_master(upstox_df, universal_data)
           
        # 4. Save and Assign
        final_df.to_csv(master_path, index=False)
        universal_data['market_data']['etf_master_list'] = final_df
        log.info(f"Instrument master saved: {len(final_df)} ETFs.", tags=["DATA", "SUCCESS"])
       
    except Exception as e:
        log.critical(f"Instrument sync failed: {e}", tags=["DATA", "CRITICAL"], exc_info=True)
        raise
    return universal_data


def _fetch_nse_etfs(universal_data: Dict[str, Any]) -> pd.DataFrame:
    """Fetches official ETF list from NSE with session warmup."""
    url = universal_data['configs']['system_settings']['data_urls']['nse_etf_url']
    home_url = "https://www.nseindia.com"
   
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nseindia.com/market-data/exchange-traded-funds-etf'
    }
   
    try:
        session = requests.Session()
        # Warmup
        session.get(home_url, headers=headers, timeout=10)
        time.sleep(1)
       
        # API Call
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
       
        data = response.json().get('data', [])
        df = pd.DataFrame(data)
       
        if not df.empty:
            # Normalize columns for merge
            df = df.rename(columns={'symbol': 'nse_symbol', 'assets': 'underlying_asset'})
            # Extract ISIN if available in meta
            if 'meta' in df.columns:
                 df['isin'] = df['meta'].apply(lambda x: x.get('isin') if isinstance(x, dict) else None)
            return df[['nse_symbol', 'underlying_asset', 'isin']]
           
    except Exception as e:
        log.error(f"NSE API error: {e}", tags=["DATA", "NSE", "ERROR"])
       
    return pd.DataFrame()


def _fetch_upstox_instruments(universal_data: Dict[str, Any]) -> pd.DataFrame:
    """Fetches huge JSON dump from Upstox and filters for NSE Equity."""
    url = universal_data['configs']['system_settings']['data_urls']['upstox_instruments_url']
   
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
       
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            data = json.load(gz)
           
        df = pd.DataFrame(data)
        # Filter: NSE exchange + Equity type
        df = df[ (df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ') ]
       
        return df[['instrument_key', 'trading_symbol', 'name']]
       
    except Exception as e:
        log.error(f"Upstox Instrument fetch error: {e}", tags=["DATA", "UPSTOX", "ERROR"])
        return pd.DataFrame()


def _merge_sources(nse_df: pd.DataFrame, upstox_df: pd.DataFrame) -> pd.DataFrame:
    """Joins NSE and Upstox data on symbol."""
    merged = pd.merge(
        nse_df,
        upstox_df,
        left_on='nse_symbol',
        right_on='trading_symbol',
        how='inner' # We only want ETFs tradable on Upstox
    )
   
    return merged.rename(columns={
        'instrument_key': 'upstox_instrument_key',
        'name': 'upstox_name'
    })[['nse_symbol', 'underlying_asset', 'isin', 'upstox_instrument_key', 'upstox_name']]


def _build_upstox_only_master(upstox_df: pd.DataFrame, universal_data: Dict[str, Any]) -> pd.DataFrame:
    """Fallback: Filters Upstox master using our config's ETF list."""
    etfs_to_track = universal_data['configs']['universe_settings']['etfs_to_track']
   
    filtered = upstox_df[upstox_df['trading_symbol'].isin(etfs_to_track)].copy()
    filtered['nse_symbol'] = filtered['trading_symbol']
    filtered['underlying_asset'] = 'Unknown'
    filtered['isin'] = None
   
    return filtered.rename(columns={
        'instrument_key': 'upstox_instrument_key',
        'name': 'upstox_name'
    })[['nse_symbol', 'underlying_asset', 'isin', 'upstox_instrument_key', 'upstox_name']]