import frappe, requests
import time
import hashlib

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

_global_payments_settings = None

def settings(force=False):
    global _global_payments_settings
    if (_global_payments_settings is None) or (force == True):
        _global_payments_settings = frappe.get_single("Global Payments Settings")
    return _global_payments_settings

def headers():
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + generate_token(),
        "Accept": "application/json",
        "X-GP-Version": "2021-03-22"
    }

def gp_get(endpoint):
    return requests.get(
        settings().api_url + endpoint,
        headers=headers()
    )

def gp_post(endpoint, payload):
    return requests.post(
        settings().api_url + endpoint,
        headers=headers(),
        json=payload
    )

    
def generate_token():
    logger.debug("generating Global Payments Access Token")
    endpoint = '/ucp/accesstoken'

    nonce = str(int(time.time() * 1000))
    app_key = settings().get_password("app_key")
    secretKey = f"{nonce}{app_key}".encode('utf-8')

    payload = {
        "app_id": settings().app_id,
        "nonce": nonce,
        "secret": hashlib.sha512(secretKey).hexdigest(),
        "grant_type": "client_credentials",
        "seconds_to_expire": 60
    }

    # logger.debug(payload)

    res = requests.post(
        settings().api_url + endpoint,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-GP-Version": "2021-03-22"
        },
        json=payload
    )

    result = res.json()
    # logger.debug(result)
    access_token = result.get("token")
    logger.debug(access_token)

    return access_token