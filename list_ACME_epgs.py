import requests
import urllib3
import json

urllib3.disable_warnings()

APIC = api url
USER = 'username'
PASS = 'password'

TENANT_FILTER = "ACME"      # only show this tenant


def apic_login():
    session = requests.Session()
    url = f"{APIC}/api/aaaLogin.json"

    payload = {
        "aaaUser": {"attributes": {"name": USER, "pwd": PASS}}
    }

    resp = session.post(url, json=payload, verify=False)
    token = resp.json()['imdata'][0]['aaaLogin']['attributes']['token']
    session.cookies['APIC-cookie'] = token
    return session


def get_all_epgs(session):
    """
    Retrieves ALL EPGs (fvAEPg) from APIC, then filters them
    for the specified tenant.
    """
    url = f"{APIC}/api/node/class/fvAEPg.json"
    resp = session.get(url, verify=False)
    return resp.json()


def print_acme_epgs(epg_data, tenant):
    print(f"\n--- EPGs in Tenant: {tenant} ---\n")

    for item in epg_data.get("imdata", []):
        epg_attrs = item["fvAEPg"]["attributes"]

        dn = epg_attrs["dn"]  # Example: uni/tn-ACME/ap-Web_Tier/epg-Web-Frontend

        # Filter: only list EPGs belonging to the ACME tenant
        if not dn.startswith(f"uni/tn-{tenant}"):
            continue

        # Extract tenant, app profile, and epg name
        parts = dn.split("/")
        tenant_name = parts[1].replace("tn-", "")
        app = parts[2].replace("ap-", "")
        epg = epg_attrs["name"]

        print(f"Tenant: {tenant_name:12}  App: {app:18}  EPG: {epg}")


if __name__ == "__main__":
    session = apic_login()
    epgs = get_all_epgs(session)
    print_acme_epgs(epgs, TENANT_FILTER)
