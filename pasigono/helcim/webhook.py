import frappe
from pasigono.helcim.api import helcim_get

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

#/api/method/pasigono.helcim.webhook.wow

# this will not work, as helcim does not allowe "helcim" in webhook url... so you need to move this somewhere else

@frappe.whitelist(allow_guest=True)
def wow():
    data = frappe.request.get_json()
    logger.debug(data)

    if data.get("type") == "terminalCancel":

        invoiceNumber = data.get("data").get("invoiceNumber")
        if invoiceNumber:
            try:
                doc = frappe.get_doc("Helcim Transaction", {
                    "invoice": invoiceNumber,
                    "status": "Pending"
                })
                logger.debug(f"found a pending helcim transaction with invoice: {invoiceNumber}")
                doc.delete(ignore_permissions=True)
                frappe.db.commit()
                notify_pos(invoiceNumber, 'Cancelled')
            except:
                # no Helcim Transaction with invoiceNumber pending (maybe this is a repeat hook call)
                logger.debug(f"DID NOT find any pending helcim transaction with invoice: {invoiceNumber}. Looks like a duplicate webhook call.")
                return ''
        else:
            logger.debug(f"Terminal Cancel webhook missing invoiceNumber!!!")

    elif data.get("type") == "cardTransaction":
        logger.debug("looks like cardTransaction")
        helclim_trans_id = data.get("id")
        xx = helcim_get(f"/card-transactions/{helclim_trans_id}").json()
        logger.debug(xx)

        transType = xx.get("type")
        if transType not in ['purchase', 'refund']:
            logger.debug(f"don't know what to do with transaction type: {transType}")
            return ''

        invoiceNumber = xx.get("invoiceNumber")

        if invoiceNumber:
            try:
                doc = frappe.get_doc("Helcim Transaction", {
                    "invoice": invoiceNumber,
                    "status": "Pending"
                })
                
                status = xx.get("status")
                myStatus = ''
                if status == "APPROVED":
                    myStatus = "Approved"
                elif status == "DECLINED":
                    myStatus = "Declined"
                else:
                    logger.debug(f"don't know what to do with transaction status: {status}")
                    return ''

                doc.status = myStatus
                doc.helcim_transactionId = xx.get("transactionId")
                doc.helcim_dateCreated = xx.get("dateCreated ")
                doc.helcim_user = xx.get("user")
                doc.helcim_cardNumber = xx.get("cardNumber")
                doc.helcim_type = xx.get("type")
                doc.helcim_amount = xx.get("amount")
                doc.helcim_currency = xx.get("currency")
                doc.helcim_avsResponse = xx.get("avsResponse")
                doc.helcim_cvvResponse = xx.get("cvvResponse")
                doc.helcim_cardType = xx.get("cardType")
                doc.helcim_approvalCode = xx.get("approvalCode")
                doc.helcim_cardToken = xx.get("cardToken")
                doc.helcim_cardHolderName = xx.get("cardHolderName")
                doc.helcim_customerCode = xx.get("customerCode")
                doc.helcim_warning = xx.get("warning")
                doc.save(ignore_permissions=True)
                frappe.db.commit()
                notify_pos(invoiceNumber, myStatus)
                return ''

                # try:
                #     invoiceDoc = frappe.get_doc("POS Invoice", invoiceNumber )
                #     invoiceDoc.helcim_transaction = doc.name    
                #     invoiceDoc.save(ignore_permissions=True)

                    # frappe.db.commit()
                #     notify_pos(invoiceNumber, myStatus)
                # except Exception:
                #     logger.debug(f"for some reason I could not find a POS Invoice with number: {invoiceNumber}.")
                #     return ''
            except frappe.DoesNotExistError:
                # no Helcim Transaction with invoiceNumber pending (maybe this is a repeat hook call)
                logger.debug(f"DID NOT find any 'pending' helcim transaction with invoice: {invoiceNumber}. Looks like a duplicate webhook call.")
                return ''

        else:
            logger.debug(f"Card Transaction Details missing invoiceNumber!!! transactionID: {helclim_trans_id}")
    else:
        xx = data.get("type")
        logger.debug(f"Unknown webhook type {xx}")


def notify_pos(invoice, status):
    frappe.publish_realtime(
        event=f"helcim_{invoice}",
        message={"status": status}
    )