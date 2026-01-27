import frappe
from pasigono.helcim.api import helcim_get, helcim_post

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

def returnMessage(status_code, device_id):
    if status_code == 202:
        return {"success": True}
    elif status_code == 404:
        return {"success": False, "error": f"Device not found: {device_id}"}
    elif status_code == 409:
        return {"success": False, "error": "Device not listening, make sure it is on."}
    else:
        return {"success": False, "error": f"Server returned error code: {status_code}"}


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
def start_purchase(pos_invoice_id, amount, device_id, currency):

    docs = frappe.db.get_list('Helcim Transaction',
        filters={
            "status": "Pending",
            'invoice': pos_invoice_id
        },
        fields=['name', 'status'],
    )

    if len(docs) > 0:
        return {"success": False, "error": f"A Pending Helcim Transaction for invoice {pos_invoice_id} already exists."}
    else:
        payload = {
            "transactionAmount": float(amount),
            "currency": currency,
            "invoiceNumber": pos_invoice_id
        }
        res = helcim_post(f"/devices/{device_id}/payment/purchase", payload)

        ret = returnMessage(res.status_code, device_id)

        if ret.get("success"):
            doc = frappe.get_doc({
                "doctype": "Helcim Transaction",
                "invoice": pos_invoice_id,
                "status": "Pending",
                "amount": amount,
                "device_id": device_id,
            }).insert(ignore_permissions=True)
            ret["invoice"] = doc.get("name")
        return ret

@frappe.whitelist()
def start_refund(pos_invoice_id, amount, device_id, original_transaction):
    logger.debug(f"will refund pos_invoice_id: {pos_invoice_id}, amount: {amount}, device_id: {device_id}, original_transaction: {original_transaction}")

    docs = frappe.db.get_list('Helcim Transaction',
        filters={
            "status": "Pending",
            'invoice': pos_invoice_id
        },
        fields=['name', 'status'],
    )

    if len(docs) > 0:
        return {"success": False, "error": f"A Pending Helcim Transaction for invoice {pos_invoice_id} already exists."}
    else:
        originaDoc = frappe.get_doc("Helcim Transaction", original_transaction)
        logger.debug(originaDoc)

        payload = {
            "transactionAmount": float(amount) * -1,
            "originalTransactionId": int(originaDoc.get("helcim_transactionId"))
        }

        logger.debug(payload)

        res = helcim_post(f"/devices/{device_id}/payment/refund", payload)

        ret = returnMessage(res.status_code, device_id)
        
        if ret.get("success"):
            doc = frappe.get_doc({
                "doctype": "Helcim Transaction",
                "invoice": pos_invoice_id,
                "status": "Pending",
                "amount": amount,
                "device_id": device_id,
            }).insert(ignore_permissions=True)
            ret["invoice"] = doc.get("name")
        return ret

