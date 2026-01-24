import frappe
from pasigono.pasigono.helcim_api import helcim_get, helcim_post

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

@frappe.whitelist()
def helcim_settings():
    return frappe.get_single("Helcim Settings")

@frappe.whitelist()
def get_devices():
    # logger.debug(helcim_get("/devices").json())
    return helcim_get("/devices").json()

@frappe.whitelist()
def ping_device(device_id):
    res = helcim_get("/devices/" + device_id + "/ping")
    return returnMessage(res.status_code, device_id)
        

@frappe.whitelist()
def start_purchase(invoiceNumber, amount, device_id, currency):

    xx = frappe.get_doc({
        "doctype": "Helcim Transaction",
        "invoice": invoiceNumber,
        "status": "Pending",
        "amount": amount,
        "device_id": device_id,
    }).insert(ignore_permissions=True)


    payload = {
        "transactionAmount": float(amount),
        "currency": currency,
        "invoiceNumber": xx.get("name")
    }
    res = helcim_post(f"/devices/{device_id}/payment/purchase", payload)

    ret = returnMessage(res.status_code, device_id)

    if ret.get("success"):
        ret["invoice"] = xx.get("name")

    return ret

def returnMessage(status_code, device_id):
    if status_code == 202:
        return {"success": True}
    elif status_code == 404:
        return {"success": False, "error": f"Device not found: {device_id}"}
    elif status_code == 409:
        return {"success": False, "error": "Device not listening, make sure it is on."}
    else:
        return {"success": False, "error": f"Server returned error code: {status_code}"}
