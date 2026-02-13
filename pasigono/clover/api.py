import frappe, requests
import time
import hashlib


frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

_clover_settings = None

def settings(force=False):
    global _clover_settings
    if (_clover_settings is None) or (force == True):
        _clover_settings = frappe.get_single("Clover Settings")
    return _clover_settings

def headers(extra_headers={}):
    ss = settings()
    extra_headers
    
    return {
        **{
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer " + ss.get('access_token'),
        },
        **extra_headers
    }
    

def get_url():
    return frappe.utils.get_url().replace('http:', 'https:')

def clover_get(endpoint, tries=0):
    if(tries > 1):
        return    

    res = requests.get(
        get_api_url() + endpoint,
        headers=headers()
    )

    if(res.status_code == 401):
        logger.debug(f"401 error code returned, will retry because, tries: {tries}")
        refresh_tokens()
        return clover_get(endpoint, tries+1)
    else:
        return res

def clover_post(endpoint, payload, extra_headers={}, tries=0):
    if(tries > 1):
        return    

    logger.debug(f"will send header: {headers(extra_headers)}")
    logger.debug(f"will send payload: {payload}")

    res = requests.post(
        get_api_url() + endpoint,
        headers=headers(extra_headers),
        json=payload
    )

    if(res.status_code == 401):
        logger.debug(f"401 error code returned, will retry because, tries: {tries}")
        refresh_tokens()
        return clover_post(endpoint, payload, extra_headers, tries+1)
    else:
        return res

def get_api_url():
    ss = settings()
    is_dev = ss.get("is_dev")

    if is_dev == 1: 
        api_url = ss.get("api_url_dev")
    else:
        api_url = ss.get("api_url")

    return api_url

def refresh_tokens():
    ss = settings()
    app_id = ss.get("app_id")
    refresh_token = ss.get("refresh_token")
    refresh_url = "/oauth/v2/refresh"
    
    res = requests.post(
        get_api_url() + refresh_url,
        json={
            "client_id": app_id,
            "refresh_token": refresh_token
        }
    )

    res_json = res.json()
    logger.debug(f"status_code: {res.status_code}, res_json: {res_json}")
    save_tokens(res_json)

def save_tokens(tokens):
    global _clover_settings
    clover_settings = frappe.get_single("Clover Settings")
    for key, value in tokens.items():
        logger.debug(f"{key}: {value}")
        clover_settings.set(key, value)
    logger.debug(f"saving new tokens")
    clover_settings.save(ignore_permissions=True)
    frappe.db.commit()
    _clover_settings = None