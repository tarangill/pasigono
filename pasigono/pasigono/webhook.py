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
        invoiceNumber = data.get("data").get("invoiceNumber")
        if invoiceNumber:
            doc = frappe.get_doc("Helcim Transaction", invoiceNumber)
            doc.status = "Cancelled"
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            notify_pos(invoiceNumber, 'Cancelled')
        else:
            logger.debug(f"Terminal Cancel webhook missing invoiceNumber!!! transactionID: {transID}")
    elif data.get("type") == "cardTransaction":
        transID = data.get("id")
        xx = helcim_get(f"/card-transactions/{transID}").json()
        logger.debug(xx)
        invoiceNumber = xx.get("invoiceNumber")
        if invoiceNumber:
            status = xx.get("status")
            myStatus = ''
            doc = frappe.get_doc("Helcim Transaction", invoiceNumber)
            if status == "APPROVED":
                myStatus = "Approved"
            elif status == "DECLINED":
                myStatus = "Declined"
            else:
                logger.debug(f"don't know what to do with transaction status: {status}")
            doc.status = myStatus
            doc.helim_transactionId = xx.get("transactionId")
            doc.helim_dateCreated = xx.get("dateCreated ")
            doc.helim_user = xx.get("user")
            doc.helim_cardNumber = xx.get("cardNumber")
            doc.helim_type = xx.get("type")
            doc.helim_amount = xx.get("amount")
            doc.helim_currency = xx.get("currency")
            doc.helim_avsResponse = xx.get("avsResponse")
            doc.helim_cvvResponse = xx.get("cvvResponse")
            doc.helim_cardType = xx.get("cardType")
            doc.helim_approvalCode = xx.get("approvalCode")
            doc.helim_cardToken = xx.get("cardToken")
            doc.helim_cardHolderName = xx.get("cardHolderName")
            doc.helim_customerCode = xx.get("customerCode")
            doc.helim_warning = xx.get("warning")
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            notify_pos(invoiceNumber, myStatus)
        else:
            logger.debug(f"Card Transaction Details missing invoiceNumber!!! transactionID: {transID}")
    else:
        xx = data.get("type")
        logger.debug(f"Unknown webhook type {xx}")
        
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