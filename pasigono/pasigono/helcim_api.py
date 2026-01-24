import frappe, requests

def settings():
    return frappe.get_single("Helcim Settings")

def headers():
    return {
        "api-token": settings().get_password("api_key"),
        "Content-Type": "application/json"
    }

def helcim_get(endpoint):
    return requests.get(
        settings().api_url + endpoint,
        headers=headers()
    )

def helcim_post(endpoint, payload):
    return requests.post(
        settings().api_url + endpoint,
        headers=headers(),
        json=payload
    )