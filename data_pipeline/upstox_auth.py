# data_pipeline/upstox_auth.py

"""
AUTHENTICATION ENGINE - Upstox API Access Token Management.
Handles daily token lifecycle (expires 3:30 AM IST).
Integrates Playwright for automated login if token is expired.
Respects 'force_fresh_login' debug flag.
"""

import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, quote
import requests
import pytz
import pyotp
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Dict, Any, Optional
from utils.logger import setup_logger

log = setup_logger()

# Define IST timezone for token expiry logic
IST = pytz.timezone('Asia/Kolkata')


def process_authentication(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Entry Point: Ensures a valid Upstox access token exists in universal_data.
    """
    log.info("=== AUTHENTICATION ENGINE STARTED ===", tags=["AUTH", "START"])
   
    system_config = universal_data['configs']['system_settings']
    debug_flags = universal_data['system']['debug_flags']
    paths = system_config['paths']
   
    # 1. Load Credentials
    creds_path = os.path.join(universal_data['system']['project_root'], paths['credentials_file'])
    try:
        with open(creds_path, 'r') as f:
            all_creds = json.load(f)
            upstox_creds = all_creds.get('upstox', {})
    except Exception as e:
        log.critical(f"Failed to load credentials: {e}", tags=["AUTH", "ERROR"])
        raise
    # 2. Check Cache vs Force Flag
    token_cache_path = os.path.join(universal_data['system']['project_root'], paths['token_cache_file'])
    force_login = debug_flags.get('force_fresh_login', False)
   
    valid_token = None
   
    if not force_login:
        valid_token = _attempt_token_from_cache(token_cache_path)
    else:
        log.info("Debug flag 'force_fresh_login' is ON. Bypassing cache.", tags=["AUTH", "DEBUG"])
    # 3. Execute Login if needed
    if valid_token:
        universal_data['access_token'] = valid_token
        log.info("Using valid cached access token.", tags=["AUTH", "SUCCESS"])
    else:
        log.info("Initiating fresh authentication flow...", tags=["AUTH", "LOGIN"])
        try:
            fresh_token = _execute_full_authentication(universal_data, upstox_creds)
            _save_token_to_cache(token_cache_path, fresh_token)
            universal_data['access_token'] = fresh_token
            log.info("Authentication successful. Token cached.", tags=["AUTH", "SUCCESS"])
        except Exception as e:
            log.critical(f"Authentication failed: {e}", tags=["AUTH", "CRITICAL"], exc_info=True)
            raise
    log.info("=== AUTHENTICATION ENGINE COMPLETE ===", tags=["AUTH", "END"])
    return universal_data


def _attempt_token_from_cache(cache_path: str) -> Optional[str]:
    """Returns cached token if it exists and hasn't expired (3:30 AM IST rule)."""
    if not os.path.exists(cache_path):
        return None
       
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
           
        saved_at_str = data.get('saved_at')
        token = data.get('access_token')
       
        if not saved_at_str or not token:
            return None
           
        # Check Expiry
        saved_at = datetime.fromisoformat(saved_at_str)
        if saved_at.tzinfo is None:
            saved_at = IST.localize(saved_at)
           
        now_ist = datetime.now(IST)
       
        # Token expires at the *next* 3:30 AM after it was saved
        # If saved today at 8:00 AM, it expires tomorrow 3:30 AM
        # If saved today at 2:00 AM, it expired today at 3:30 AM (if now is 4:00 AM)
       
        # Simplified rule:
        # Calculate the most recent 3:30 AM in the past.
        # If the token was saved BEFORE that 3:30 AM, it is expired.
       
        today_330 = now_ist.replace(hour=3, minute=30, second=0, microsecond=0)
        if now_ist < today_330:
            # We are currently before 3:30 AM, so the "cutoff" was yesterday 3:30 AM
            cutoff_time = today_330 - timedelta(days=1)
        else:
            # We are past 3:30 AM, so the cutoff was today 3:30 AM
            cutoff_time = today_330
           
        if saved_at > cutoff_time:
            return token
        else:
            log.info("Cached token has expired (3:30 AM rule).", tags=["AUTH", "EXPIRED"])
            return None
    except Exception as e:
        log.warning(f"Cache read error: {e}", tags=["AUTH", "WARNING"])
        return None


def _save_token_to_cache(cache_path: str, token: str) -> None:
    """Saves token with timestamp."""
    data = {
        "access_token": token,
        "saved_at": datetime.now(IST).isoformat()
    }
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)


def _execute_full_authentication(universal_data: Dict[str, Any], creds: Dict[str, str]) -> str:
    """Orchestrates Browser Login -> Auth Code -> API Token Exchange."""
   
    # 1. Get Auth Code via Playwright
    auth_code = _obtain_auth_code_via_browser(universal_data, creds)
    if not auth_code:
        raise RuntimeError("Failed to obtain Authorization Code from browser.")
       
    # 2. Exchange for Token
    access_token = _exchange_code_for_token(universal_data, creds, auth_code)
    if not access_token:
        raise RuntimeError("Failed to exchange Authorization Code for Access Token.")
       
    return access_token


def _obtain_auth_code_via_browser(universal_data: Dict[str, Any], creds: Dict[str, str]) -> Optional[str]:
    """Uses Playwright to handle Upstox login UI."""
   
    api_key = creds['API_KEY']
    redirect_uri = creds['RURL']
    login_url = universal_data['configs']['system_settings']['data_urls']['upstox_login_dialog']
   
    auth_url = f"{login_url}?response_type=code&client_id={api_key}&redirect_uri={quote(redirect_uri)}"
    auth_code = None
    log.info("Launching headless browser...", tags=["AUTH", "BROWSER"])
   
    with sync_playwright() as p:
        # Launch options suitable for server environments
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context()
        page = context.new_page()
        # Hook to capture the redirect URL containing the code
        def handle_request(request):
            nonlocal auth_code
            if redirect_uri in request.url and "code=" in request.url:
                parsed = urlparse(request.url)
                auth_code = parse_qs(parsed.query)['code'][0]
                log.info("Authorization Code captured successfully.", tags=["AUTH", "BROWSER"])
        page.on('request', handle_request)
        try:
            page.goto(auth_url, timeout=30000)
           
            # 1. Mobile Number
            page.locator("#mobileNum").fill(creds['MOBILE_NO'])
            page.get_by_role("button", name="Get OTP").click()
            page.wait_for_selector("#otpNum", state="visible", timeout=10000)
           
            # 2. TOTP
            totp = pyotp.TOTP(creds['TOTP_KEY']).now()
            page.locator("#otpNum").fill(totp)
            page.get_by_role("button", name="Continue").click()
            page.wait_for_selector("input[type='password']", state="visible", timeout=10000)
           
            # 3. PIN
            page.get_by_label("Enter 6-digit PIN").fill(creds['PIN'])
            page.get_by_role("button", name="Continue").click()
           
            # Wait for redirect to happen
            page.wait_for_timeout(5000)
           
        except Exception as e:
            log.error(f"Browser automation error: {e}", tags=["AUTH", "BROWSER", "ERROR"])
        finally:
            browser.close()
    return auth_code


def _exchange_code_for_token(universal_data: Dict[str, Any], creds: Dict[str, str], code: str) -> Optional[str]:
    """Calls Upstox API to get the actual token."""
    token_api = universal_data['configs']['system_settings']['data_urls']['upstox_token_api']
   
    payload = {
        'code': code,
        'client_id': creds['API_KEY'],
        'client_secret': creds['SECRET_KEY'],
        'redirect_uri': creds['RURL'],
        'grant_type': 'authorization_code'
    }
   
    headers = {'accept': 'application/json', 'Api-Version': '2.0', 'Content-Type': 'application/x-www-form-urlencoded'}
   
    try:
        resp = requests.post(token_api, data=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json().get('access_token')
    except Exception as e:
        log.error(f"Token exchange API failed: {e}", tags=["AUTH", "API", "ERROR"])
        return None