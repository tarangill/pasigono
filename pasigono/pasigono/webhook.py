import frappe
from pasigono.pasigono.helcim_api import helcim_get

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

#/api/method/pasigono.pasigono.webhook.helcim

#3791cMGu7bOeJc9JdVl09Ndcm4qn5172

# i had to name it wow (as i was in awe) because apparently helcim doesn't allow "helcim" in webhook url.
@frappe.whitelist(allow_guest=True)
def wow():
    data = frappe.request.get_json()
    logger.debug(data)
    if data.get("type") == "terminalCancel":
        xx = data.get("data").get("invoiceNumber")
        logger.debug(xx)
        notify_pos(xx, 'Cancelled')
    else:
        logger.debug("card transaction")
        
    # logger.debug(frappe.request.headers.get("Content-Type"))

    # transaction_id = data.get("transactionId")

    # txn = helcim_get(f"/card-transactions/{transaction_id}")

    # doc = frappe.get_doc("Helcim Transaction", {
    #     "helcim_reference": transaction_id
    # })

    # if txn["status"] == "APPROVED":
    #     doc.status = "Approved"
    #     notify_pos(doc.invoice, "approved")
    # else:
    #     doc.status = "Declined"
    #     notify_pos(doc.invoice, "declined")

    # doc.save()

def notify_pos(invoice, status):
    frappe.publish_realtime(
        event=f"helcim_payment_{invoice}",
        message={"status": status}
    )