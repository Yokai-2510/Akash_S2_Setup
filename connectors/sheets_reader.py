"""
Data Reader Connector.
Reads from _SYSTEM_DATA (hidden sheet) for reliable Python parsing.
Also reads STATE for portfolio holdings.
"""
import pandas as pd
import os
from typing import Dict, Any, List
from utils.logger import setup_logger

log = setup_logger()


def load_config_and_portfolio(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point - loads config and portfolio from Excel."""
    mode = universal_data['configs']['system_settings']['system'].get('data_source_mode', 'local_excel')
    log.info(f"=== LOADING DATA ({mode.upper()}) ===", tags=["READER", "START"])
    
    if mode == 'local_excel':
        raw_data, file_exists = _read_from_local_excel(universal_data)
    else:
        raise NotImplementedError("Google Sheets mode not implemented")
    
    # If file doesn't exist, create it and use strategy_config defaults
    if not file_exists:
        log.info("Using defaults from strategy_config.json", tags=["READER", "DEFAULTS"])
        from connectors.sheets_writer import _create_professional_template
        
        path_config = universal_data['configs']['system_settings']['paths']
        file_path = os.path.join(universal_data['system']['project_root'], path_config.get('local_excel_file', ''))
        _create_professional_template(file_path, universal_data)
        
        # Build etf_lineup DataFrame from strategy_config
        etf_list = universal_data['configs']['universe_settings']['etfs_to_track']
        lineup_data = []
        for i, etf in enumerate(etf_list):
            lineup_data.append({
                'ETF_ID': f'ETF_{str(i+1).zfill(2)}',
                'Ticker': etf,
                'Enabled': True,
                'Target_%': round(100 / len(etf_list), 1),
                'ATR_Override_%': None,
                'Tags': 'Core'
            })
        universal_data['configs']['etf_lineup'] = pd.DataFrame(lineup_data)
        
        # Use strategy_config defaults
        universal_data['change_detection']['update_trigger'] = False
        universal_data['change_detection']['last_run_timestamp'] = ''
        universal_data['portfolio_state']['holdings'] = pd.DataFrame()
        universal_data['portfolio_state']['summary'] = {'total_s2_value': 0, 'current_s2_weight_pct': 0, 'num_holdings': 0}
        
        log.info(f"Tracking {len(etf_list)} ETFs from strategy_config", tags=["READER", "CONFIG"])
        log.info("=== DATA LOADING COMPLETE (defaults) ===", tags=["READER", "END"])
        return universal_data
    
    # File exists - parse _SYSTEM_DATA
    system_data = raw_data.get('_SYSTEM_DATA', [])
    parsed = _parse_system_data(system_data)
    
    # Use parsed data if available, else keep strategy_config defaults
    if not parsed['system_params'].empty:
        universal_data['configs']['system_params'] = parsed['system_params']
    
    if not parsed['etf_lineup'].empty and 'Enabled' in parsed['etf_lineup'].columns:
        universal_data['configs']['etf_lineup'] = parsed['etf_lineup']
        enabled_etfs = parsed['etf_lineup'][parsed['etf_lineup']['Enabled'] == True]['Ticker'].tolist()
        if enabled_etfs:
            universal_data['configs']['universe_settings']['etfs_to_track'] = enabled_etfs
    
    universal_data['change_detection']['update_trigger'] = parsed['control']['UPDATE_TRIGGER']
    universal_data['change_detection']['last_run_timestamp'] = parsed['control'].get('LAST_RUN_DATE', '')
    
    log.info(f"Loaded {len(universal_data['configs']['universe_settings']['etfs_to_track'])} ETFs", tags=["READER", "CONFIG"])
    log.info(f"Update trigger: {parsed['control']['UPDATE_TRIGGER']}", tags=["READER", "CONTROL"])
    
    # Parse STATE
    state_data = raw_data.get('STATE', [])
    state_parsed = _parse_state_sheet(state_data)
    universal_data['portfolio_state']['holdings'] = state_parsed['holdings']
    universal_data['portfolio_state']['summary'] = state_parsed['summary']
    
    log.info(f"Portfolio: ₹{state_parsed['summary']['total_s2_value']:,.0f} ({state_parsed['summary']['num_holdings']} holdings)", tags=["READER", "STATE"])
    log.info("=== DATA LOADING COMPLETE ===", tags=["READER", "END"])
    
    return universal_data
    
    # Parse STATE
    state_data = raw_data.get('STATE', [])
    state_parsed = _parse_state_sheet(state_data)
    universal_data['portfolio_state']['holdings'] = state_parsed['holdings']
    universal_data['portfolio_state']['summary'] = state_parsed['summary']
    
    log.info(f"Portfolio: ₹{state_parsed['summary']['total_s2_value']:,.0f} ({state_parsed['summary']['num_holdings']} holdings)", tags=["READER", "STATE"])
    log.info("=== DATA LOADING COMPLETE ===", tags=["READER", "END"])
    
    return universal_data


def _read_from_local_excel(universal_data: Dict[str, Any]) -> tuple:
    """Reads sheets from local Excel file. Returns (raw_data, file_exists)."""
    path_config = universal_data['configs']['system_settings']['paths']
    file_path = os.path.join(universal_data['system']['project_root'], path_config.get('local_excel_file', ''))
    
    if not os.path.exists(file_path):
        log.warning("Excel file missing. Will create from defaults.", tags=["READER", "INIT"])
        return {}, False
    
    raw_data = {}
    try:
        xls = pd.read_excel(file_path, sheet_name=None, header=None, dtype=str)
        for sheet_name, df in xls.items():
            raw_data[sheet_name] = df.fillna("").values.tolist()
    except Exception as e:
        log.critical(f"Failed to read Excel: {e}", tags=["READER", "ERROR"])
        raise
    
    return raw_data, True


def _parse_system_data(rows: List[List[str]]) -> Dict[str, Any]:
    """Parses the _SYSTEM_DATA hidden sheet."""
    result = {
        'system_params': pd.DataFrame(),
        'etf_lineup': pd.DataFrame(),
        'control': {'UPDATE_TRIGGER': False, 'RUN_STATUS': 'IDLE', 'LAST_RUN_DATE': '', 'ERROR_MESSAGE': ''}
    }
    
    if not rows:
        return result
    
    # Find section markers
    params = []
    lineup_rows = []
    control_section = False
    lineup_section = False
    lineup_header = None
    
    for row in rows:
        if not row or not row[0]:
            continue
        
        key = str(row[0]).strip()
        
        # Section markers
        if '### ETF_LINEUP ###' in key:
            lineup_section = True
            control_section = False
            continue
        elif '### CONTROL ###' in key:
            control_section = True
            lineup_section = False
            continue
        elif key == 'KEY':  # Header row
            continue
        
        # Control section
        if control_section:
            if len(row) >= 2:
                val = str(row[1]).strip().upper()
                if key == 'UPDATE_TRIGGER':
                    result['control']['UPDATE_TRIGGER'] = val == 'TRUE'
                elif key == 'RUN_STATUS':
                    result['control']['RUN_STATUS'] = val
                elif key == 'LAST_RUN_DATE':
                    result['control']['LAST_RUN_DATE'] = str(row[1]).strip()
                elif key == 'ERROR_MESSAGE':
                    result['control']['ERROR_MESSAGE'] = str(row[1]).strip()
            continue
        
        # ETF Lineup section
        if lineup_section:
            if key == 'ETF_ID':  # Header row
                lineup_header = [str(c).strip() for c in row]
                continue
            if key.startswith('ETF_'):
                lineup_rows.append(row)
            continue
        
        # System params (before any section marker)
        if len(row) >= 2 and not key.startswith('#'):
            params.append({'Parameter': key, 'Value': row[1]})
    
    # Build DataFrames
    if params:
        result['system_params'] = pd.DataFrame(params)
        result['system_params'] = _convert_param_types(result['system_params'])
    
    if lineup_rows and lineup_header:
        result['etf_lineup'] = pd.DataFrame(lineup_rows, columns=lineup_header)
        result['etf_lineup'] = _convert_lineup_types(result['etf_lineup'])
    
    return result


def _parse_state_sheet(rows: List[List[str]]) -> Dict[str, Any]:
    """Parses STATE sheet for portfolio holdings."""
    result = {
        'holdings': pd.DataFrame(),
        'summary': {'total_s2_value': 0.0, 'current_s2_weight_pct': 0.0, 'num_holdings': 0}
    }
    
    if not rows or len(rows) < 2:
        return result
    
    # Find header row (contains 'ETF_ID' or 'Ticker')
    header_idx = None
    for i, row in enumerate(rows):
        if any('ETF_ID' in str(c) or 'Ticker' in str(c) for c in row):
            header_idx = i
            break
    
    if header_idx is None:
        return result
    
    header = [str(c).strip() for c in rows[header_idx]]
    data_rows = []
    
    for row in rows[header_idx + 1:]:
        # Skip empty rows or summary rows
        if not row or not row[0] or str(row[0]).strip() == '':
            continue
        if 'SUMMARY' in str(row[0]).upper() or 'Total' in str(row[0]):
            continue
        # Only include rows that look like ETF data
        first_val = str(row[0]).strip() if row else ''
        if first_val.startswith('ETF_') or (len(row) > 1 and str(row[1]).strip()):
            data_rows.append(row[:len(header)])
    
    if not data_rows:
        return result
    
    df = pd.DataFrame(data_rows, columns=header)
    df = _convert_state_types(df)
    
    # Filter out empty rows
    if 'Ticker' in df.columns:
        df = df[df['Ticker'].astype(str).str.len() > 0]
    
    result['holdings'] = df
    
    # Calculate summary
    if 'Market_Value' in df.columns:
        result['summary']['total_s2_value'] = pd.to_numeric(df['Market_Value'], errors='coerce').fillna(0).sum()
    if 'Current_%' in df.columns:
        result['summary']['current_s2_weight_pct'] = pd.to_numeric(df['Current_%'], errors='coerce').fillna(0).sum()
    result['summary']['num_holdings'] = len(df)
    
    return result


def _convert_param_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converts parameter values to appropriate types."""
    if df.empty:
        return df
    
    def convert_val(row):
        val = str(row['Value']).strip()
        param = str(row['Parameter']).strip()
        
        # Boolean
        if val.upper() in ('TRUE', 'FALSE'):
            return val.upper() == 'TRUE'
        
        # Numeric
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except:
            return val
    
    df['Value'] = df.apply(convert_val, axis=1)
    return df


def _convert_lineup_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converts lineup columns to appropriate types."""
    if df.empty:
        return df
    
    if 'Enabled' in df.columns:
        df['Enabled'] = df['Enabled'].astype(str).str.upper() == 'TRUE'
    
    if 'Target_%' in df.columns:
        df['Target_%'] = pd.to_numeric(df['Target_%'], errors='coerce').fillna(0)
    
    if 'ATR_Override_%' in df.columns:
        df['ATR_Override_%'] = pd.to_numeric(df['ATR_Override_%'], errors='coerce')
    
    return df


def _convert_state_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converts state columns to numeric where appropriate."""
    numeric_cols = ['Units', 'Avg_Cost', 'Current_Price', 'Market_Value', 'Current_%', 'Target_%', 'Gap_%']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df