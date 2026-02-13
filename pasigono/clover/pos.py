import frappe, requests
import time
import hashlib
from pasigono.clover.api import settings, clover_get, clover_post

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

@frappe.whitelist(allow_guest=True)
def get_devices():
    ss = settings()
    res = clover_get(f"/v3/merchants/{ss.get('merchant_id')}/devices")
    res_json = res.json()
    serials = [el["serial"] for el in res_json.get("elements", [])]
    logger.debug(f"devices: {serials}")
    return serials

@frappe.whitelist(allow_guest=True)
def ping_device(device_id):
    ss = settings()
    res = clover_post(
        "/connect/v1/device/display",
        {
            "text":"A message to show on the device",
            "beep":True
        },
        {
            'x-clover-device-id': device_id,
            'x-pos-id': 'MyPOS',
        }
    )
    res_json = res.json()
    logger.debug(f"status: {res.status_code}, devices: {res_json}")
    return res_json
