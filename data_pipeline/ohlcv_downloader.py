# data_pipeline/ohlcv_downloader.py

"""
OHLCV SYNCHRONIZATION ENGINE.
Downloads 1-minute historical data with intelligent incremental sync.
Handles 'force_ohlcv_resync' flag.
Ensures data integrity (sorting, deduplication).
"""

import pandas as pd
import requests
import json
import os
import time
from datetime import datetime, date, timedelta
from tqdm import tqdm
from typing import Dict, Any, List, Tuple, Optional
from utils.logger import setup_logger

log = setup_logger()


def process_ohlcv_sync(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Entry Point: Syncs OHLCV data for all tracked ETFs.
    """
    log.info("=== OHLCV DATA SYNC STARTED ===", tags=["DATA", "OHLCV", "START"])
   
    # Configs
    etfs_to_track = universal_data['configs']['universe_settings']['etfs_to_track']
    debug_flags = universal_data['system']['debug_flags']
    paths = universal_data['configs']['system_settings']['paths']
   
    # Master List Mappings
    master_df = universal_data['market_data'].get('etf_master_list')
    if master_df is None or master_df.empty:
        raise RuntimeError("ETF Master list missing. Cannot sync OHLCV.")
       
    symbol_map = dict(zip(master_df['nse_symbol'], master_df['upstox_instrument_key']))
   
    # Setup Directory
    ohlcv_dir = os.path.join(universal_data['system']['project_root'], paths['ohlcv_data_dir'])
    os.makedirs(ohlcv_dir, exist_ok=True)
   
    ohlcv_files = {}
    stats = {'synced': 0, 'skipped': 0, 'failed': 0}
   
    force_resync = debug_flags.get('force_ohlcv_resync', False)
    if force_resync:
        log.info("Debug flag 'force_ohlcv_resync' is ON. Will redownload all data.", tags=["DATA", "DEBUG"])
    # Iterate ETFs
    log.info(f"Syncing {len(etfs_to_track)} ETFs...", tags=["DATA", "LOOP"])
   
    for etf in tqdm(etfs_to_track, desc="Syncing OHLCV"):
        file_path = os.path.join(ohlcv_dir, f"{etf}_1m_history.json")
        ohlcv_files[etf] = file_path
       
        instrument_key = symbol_map.get(etf)
        if not instrument_key:
            log.warning(f"Skipping {etf}: Instrument key not found in master.", tags=["DATA", "WARNING"])
            stats['failed'] += 1
            continue
           
        try:
            # Determine Date Range
            start_date, end_date = _get_fetch_range(file_path, universal_data, force_resync)
           
            if start_date is None:
                # Cache is current, skip
                stats['skipped'] += 1
            elif start_date <= end_date:
                # Fetch Data
                new_data = _fetch_data_chunks(universal_data, instrument_key, start_date, end_date)
                if new_data:
                    _update_cache_file(file_path, new_data, force_resync)
                    stats['synced'] += 1
                else:
                    stats['skipped'] += 1
            else:
                stats['skipped'] += 1
               
        except Exception as e:
            log.error(f"Failed to sync {etf}: {e}", tags=["DATA", "ERROR"])
            stats['failed'] += 1
           
    universal_data['market_data']['ohlcv_file_paths'] = ohlcv_files
    log.info(f"Sync Complete. Stats: {stats}", tags=["DATA", "SUMMARY"])
   
    return universal_data


def _get_fetch_range(file_path: str, universal_data: Dict[str, Any], force_resync: bool) -> Tuple[Optional[date], date]:
    """
    Calculates [start_date, end_date] for fetching.
    Returns (None, end_date) if cache is already current.
    """
    today = date.today()
    end_date = today
   
    default_start_str = universal_data['configs']['system_settings']['data_acquisition']['full_history_start_date']
    default_start = datetime.strptime(default_start_str, '%Y-%m-%d').date()
   
    if force_resync or not os.path.exists(file_path):
        return default_start, end_date
       
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if not data:
                return default_start, end_date
               
            # Get last cached timestamp
            last_ts_str = data[-1][0]
            # Handle timezone-aware timestamps
            if 'T' in last_ts_str:
                last_ts_str = last_ts_str.split('+')[0].split('T')[0] if '+' in last_ts_str else last_ts_str.split('T')[0]
            last_date = datetime.strptime(last_ts_str[:10], '%Y-%m-%d').date()
           
            # If last cached data is from today, skip
            if last_date >= today:
                log.info(f"Cache current ({last_date}), skipping fetch", tags=["DATA", "SKIP"])
                return None, end_date
            
            # If last cached is yesterday or before, fetch from next day
            return last_date + timedelta(days=1), end_date
           
    except (json.JSONDecodeError, IndexError, ValueError) as e:
        log.warning(f"Cache parse error: {e}, forcing full sync.", tags=["DATA", "CORRUPT"])
        return default_start, end_date


def _fetch_data_chunks(universal_data: Dict[str, Any], instrument_key: str, start_date: date, end_date: date) -> List[List]:
    """Fetches data in chunks to respect API limits."""
   
    chunk_size_days = universal_data['configs']['system_settings']['data_acquisition']['api_fetch_chunk_days']
    all_candles = []
   
    curr_start = start_date
   
    while curr_start <= end_date:
        curr_end = min(curr_start + timedelta(days=chunk_size_days), end_date)
       
        candles = _fetch_single_chunk(universal_data, instrument_key, curr_start, curr_end)
        if candles:
            all_candles.extend(candles)
           
        curr_start = curr_end + timedelta(days=1)
        time.sleep(0.2) # Rate limit nicety
       
    return all_candles


def _fetch_single_chunk(universal_data: Dict[str, Any], instrument_key: str, start: date, end: date) -> List[List]:
    """Calls Upstox Historical API."""
    base_url = universal_data['configs']['system_settings']['data_urls']['upstox_historical_api']
    token = universal_data['access_token']
   
    # Format: {instrumentKey}/minutes/{interval}/{to_date}/{from_date}
    url = f"{base_url}/{instrument_key}/minutes/1/{end}/{start}"
   
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
   
    try:
        resp = requests.get(url, headers=headers, timeout=10)
       
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                return data.get('data', {}).get('candles', [])
    except Exception as e:
        log.warning(f"Chunk fetch failed for {instrument_key}: {e}", tags=["DATA", "API_WARN"])
       
    return []


def _update_cache_file(file_path: str, new_data: List[List], force_resync: bool) -> None:
    """
    Updates JSON file. Handles Sorting and Deduplication.
    Upstox returns data in Reverse Chronological (newest first).
    We store Chronological (oldest first).
    """
    if not new_data and not force_resync:
        return
    existing_data = []
   
    if not force_resync and os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    # Merge
    combined = existing_data + new_data
   
    # Deduplicate based on Timestamp (index 0)
    unique_map = {row[0]: row for row in combined}
   
    # Sort Chronologically
    sorted_data = sorted(unique_map.values(), key=lambda x: x[0])
   
    with open(file_path, 'w') as f:
        json.dump(sorted_data, f)