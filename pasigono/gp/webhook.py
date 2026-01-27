import frappe
from pasigono.gp.api import gp_get, generate_token, gp_post

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=False, file_count=50)

#/api/method/pasigono.gp.webhook.wow

@frappe.whitelist(allow_guest=True)
def wow():
    from uuid import uuid4
    req_id = str(uuid4())[:8]
    data = frappe.request.get_json()
    logger.debug(f"[REQ-{req_id}] webhook call for global payments")
    logger.debug(f"[REQ-{req_id}] {data}")


