"""
Deep validation utilities for configuration values.
Checks ranges, data types, and business logic constraints.
"""

from typing import Dict, Any, List
from utils.logger import setup_logger

log = setup_logger()


def validate_system_config_values(config: Dict[str, Any]) -> List[str]:
    """Validate system config values are within acceptable ranges."""
    
    errors = []
    
    # UPDATED: Validate all URLs start with http (key is now data_urls)
    urls = config.get('data_urls', {})
    for key, url in urls.items():
        if not url.startswith('http'):
            errors.append(f"Invalid URL for {key}: {url}")
    
    # Validate data acquisition settings
    acquisition = config.get('data_acquisition', {})
    
    chunk_days = acquisition.get('api_fetch_chunk_days', 0)
    if chunk_days < 1 or chunk_days > 365:
        errors.append(f"api_fetch_chunk_days must be 1-365, got: {chunk_days}")
    
    delay = acquisition.get('api_rate_limit_delay_seconds', -1)
    if delay < 0:
        errors.append(f"api_rate_limit_delay_seconds must be >= 0, got: {delay}")
    
    timeout = acquisition.get('request_timeout_seconds', 0)
    if timeout < 1 or timeout > 300:
        errors.append(f"request_timeout_seconds must be 1-300, got: {timeout}")
    
    # Validate cache policies
    cache = config.get('cache_policies', {})
    
    cache_days = cache.get('instrument_master_cache_days', -1)
    if cache_days < 0:
        errors.append(f"instrument_master_cache_days must be >= 0, got: {cache_days}")
    
    return errors


def validate_strategy_config_values(config: Dict[str, Any]) -> List[str]:
    """Validate strategy config values are within acceptable ranges."""
    
    errors = []
    
    # Validate allocation rules
    allocation = config.get('allocation_rules', {})
    
    s2_target = allocation.get('s2_target_percent', 0)
    if not 0 < s2_target <= 100:
        errors.append(f"s2_target_percent must be 0-100, got: {s2_target}")
    
    weeks = allocation.get('weeks_to_glide', 0)
    if weeks < 1:
        errors.append(f"weeks_to_glide must be >= 1, got: {weeks}")
    
    transfer_cap = allocation.get('weekly_transfer_cap_percent', 0)
    if not 0 < transfer_cap <= 100:
        errors.append(f"weekly_transfer_cap_percent must be 0-100, got: {transfer_cap}")
    
    # Validate risk controls
    risk = config.get('risk_controls', {})
    
    drift_band = risk.get('drift_band_percent', -1)
    if not 0 <= drift_band <= 50:
        errors.append(f"drift_band_percent must be 0-50, got: {drift_band}")
    
    core_floor = risk.get('core_floor_percent', -1)
    if not 0 <= core_floor <= 100:
        errors.append(f"core_floor_percent must be 0-100, got: {core_floor}")
    
    atr_ceiling = risk.get('default_atr_ceiling_percent', 0)
    if not 0 < atr_ceiling <= 10:
        errors.append(f"default_atr_ceiling_percent must be 0-10, got: {atr_ceiling}")
    
    # Validate health gates
    health = config.get('health_gates', {})
    
    required_score = health.get('required_score', 0)
    if not 1 <= required_score <= 4:
        errors.append(f"required_score must be 1-4, got: {required_score}")
    
    # Validate harvest triggers
    harvest = config.get('harvest_triggers', {})
    
    h1 = harvest.get('h1_stretch', {})
    if h1.get('enabled'):
        rsi_threshold = h1.get('rsi_threshold', 0)
        if not 50 <= rsi_threshold <= 100:
            errors.append(f"h1_stretch rsi_threshold must be 50-100, got: {rsi_threshold}")
        
        trim_pct = h1.get('trim_percent', 0)
        if not 0 < trim_pct <= 50:
            errors.append(f"h1_stretch trim_percent must be 0-50, got: {trim_pct}")
    
    h2 = harvest.get('h2_volspike', {})
    if h2.get('enabled'):
        percentile = h2.get('atr_percentile', 0)
        if not 50 <= percentile <= 100:
            errors.append(f"h2_volspike atr_percentile must be 50-100, got: {percentile}")
    
    return errors


def validate_universal_data_structure(universal_data: Dict[str, Any]) -> bool:
    """Validate universal_data has all required top-level keys."""
    
    required_keys = [
        'system',
        'configs',
        'portfolio_state',
        'market_data',
        'analysis',
        'execution_plan',
        'report_sheets',
        'change_detection'
    ]
    
    missing = [key for key in required_keys if key not in universal_data]
    
    if missing:
        raise ValueError(f"Universal data missing keys: {missing}")
    
    return True