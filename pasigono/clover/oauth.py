import frappe, requests
import time
import hashlib
from pasigono.clover.api import settings, get_url, get_api_url, save_tokens

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

#
# read documentation at: https://docs.clover.com/dev/docs/high-trust-app-auth-flow#
# and: https://docs.clover.com/dev/docs/generate-expiring-tokens-using-v2-oauth-flow
#


@frappe.whitelist(allow_guest=True)
def url():
    ss = settings()
    is_dev = ss.get("is_dev")
    app_id = ss.get("app_id")

    if is_dev == 1: 
        auth_url = ss.get("auth_url_dev")
    else:
        auth_url = ss.get("auth_url")

    auth_url = f"{auth_url}/oauth/v2/authorize?client_id={app_id}&redirect_uri={get_url()}/api/method/pasigono.clover.oauth.callback"
    return {"auth_url": auth_url}

@frappe.whitelist(allow_guest=True)
def callback():
    from uuid import uuid4
    req_id = str(uuid4())[:8]
    logger.debug(f"[REQ-{req_id}] oauth callback for clover")
    merchant_id = frappe.request.args.get('merchant_id')
    client_id = frappe.request.args.get('client_id')
    code = frappe.request.args.get('code')

    logger.debug(f"[REQ-{req_id}] merchant_id: {merchant_id} client_id: {client_id} code: {code}")

    ss = settings()
    app_id = ss.get("app_id")
    app_secret = ss.get_password("app_secret")
    token_url = "/oauth/v2/token"

    if(client_id != app_id) :
        return {"success":  False, "error": "wrong app_id"}

    if code == None:
        return {"success":  False, "error": "missing authentication_code"}

    save_tokens({
        "merchant_id": merchant_id
    })

    res = call_clover(
        {
            "client_id": app_id,
            "client_secret": app_secret,
            "code": code
        },
        token_url
    )

    res_json = res.json()
    logger.debug(f"status_code: {res.status_code}, res_json: {res_json}")

    save_tokens(res_json)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/app/clover-settings/Clover%20Settings"


def call_clover( payload, endpoint ):

    # logger.debug(f"is_dev: {is_dev} api_url:{get_api_url()} endpoint: {endpoint} payload: {payload}")

    return requests.post(
        get_api_url() + endpoint,
        json=payload
    )

