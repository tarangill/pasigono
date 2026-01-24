import frappe
from pasigono.pasigono.helcim_api import helcim_get, helcim_post

# @frappe.whitelist()
# def helcim_settings():
#     xx = frappe.get_single("Helcim Settings")
#     frappe.errprint(xx.get_password("api_key"))
#     return xx

@frappe.whitelist()
def get_devices():
    return helcim_get("/devices").json()

@frappe.whitelist()
def ping_device(device_id):
    res = helcim_get("/devices/" + device_id + "/ping")
    if res.status_code == 202:
        return {"success": True}
    elif res.status_code == 404:
        return {"success": False, "error": "Device not found: " + device_id}
    elif res.status_code == 409:
        return {"success": False, "error": "Device not listening, make sure it is on."}
    else:
        return {"success": False, "error": "Server returned error code: "+ res.status_code}
        

@frappe.whitelist()
def start_purchase(invoice, amount, device_id):
    payload = {
        "deviceId": device_id,
        "amount": float(amount),
        "currency": "USD",
        "reference": invoice
    }

    res = helcim_post("/card-terminal/start-purchase", payload)

    frappe.get_doc({
        "doctype": "Helcim Transaction",
        "invoice": invoice,
        "status": "Pending",
        "amount": amount,
        "device_id": device_id,
        "helcim_reference": res.get("transactionId")
    }).insert(ignore_permissions=True)

    return res