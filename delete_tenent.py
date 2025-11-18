import requests
import urllib3
import json

urllib3.disable_warnings()

APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'


def apic_login():
    """Authenticate and return APIC session."""
    session = requests.Session()
    url = f"{APIC}/api/aaaLogin.json"
    payload = {
        "aaaUser": {"attributes": {"name": USER, "pwd": PASS}}
    }
    r = session.post(url, json=payload, verify=False)
    token = r.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    return session


def delete_mo(session, dn):
    """
    Delete a Managed Object (MO) using its DN.
    Example DN: 'uni/tn-Villians/ap-Hackers/epg-Web'
    """
    url = f"{APIC}/api/mo/{dn}.json"
    payload = {"fvAEPg": {"attributes": {"dn": dn, "status": "deleted"}}}
    # The object class in payload does not matter if status="deleted"
    return session.post(url, json=payload, verify=False)


def delete_tenant(session, tenant):
    """
    Delete the entire tenant (and all children).
    """
    dn = f"uni/tn-{tenant}"
    url = f"{APIC}/api/mo/{dn}.json"
    payload = {"fvTenant": {"attributes": {"dn": dn, "status": "deleted"}}}
    return session.post(url, json=payload, verify=False)


if __name__ == "__main__":
    session = apic_login()

    TENANT = "ACME"
    APP = "Hackers"
    EPG = "Web"

    # Option 1: Delete JUST the EPG
    print("Deleting EPG...")
    print(delete_mo(session, f"uni/tn-{TENANT}/ap-{APP}/epg-{EPG}").json())

    # Option 2: Delete JUST the App Profile
    print("Deleting App Profile...")
    print(delete_mo(session, f"uni/tn-{TENANT}/ap-{APP}").json())

    # Option 3: Delete Tenant (recursive destroy)
    print("Deleting Tenant (including all children)...")
    print(delete_tenant(session, TENANT).json())

    print("\n✔ All objects deleted.")
