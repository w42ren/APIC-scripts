import requests
import urllib3
import json

urllib3.disable_warnings()

APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'


def apic_login():
    """Authenticate to APIC and return a session with APIC-cookie."""
    url = f"{APIC}/api/aaaLogin.json"
    payload = {
        "aaaUser": {
            "attributes": {
                "name": USER,
                "pwd": PASS
            }
        }
    }

    session = requests.Session()
    r = session.post(url, json=payload, verify=False)
    token = r.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    return session


def create_tenant(session, tenant_name):
    """
    Create a tenant.
    API: POST /api/mo/uni/tn-<tenant>.json
    """
    url = f"{APIC}/api/mo/uni/tn-{tenant_name}.json"
    payload = {
        "fvTenant": {
            "attributes": {
                "dn": f"uni/tn-{tenant_name}",
                "name": tenant_name
            }
        }
    }
    return session.post(url, json=payload, verify=False)


def create_app_profile(session, tenant, app):
    """
    Create an Application Profile inside a tenant.
    API: POST /api/mo/uni/tn-<tenant>/ap-<app>.json
    """
    url = f"{APIC}/api/mo/uni/tn-{tenant}/ap-{app}.json"
    payload = {
        "fvAp": {
            "attributes": {
                "dn": f"uni/tn-{tenant}/ap-{app}",
                "name": app
            }
        }
    }
    return session.post(url, json=payload, verify=False)


def create_epg(session, tenant, app, epg):
    """
    Create an EPG inside an App Profile.
    API: POST /api/mo/uni/tn-<tenant>/ap-<app>/epg-<epg>.json
    """
    url = f"{APIC}/api/mo/uni/tn-{tenant}/ap-{app}/epg-{epg}.json"
    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": f"uni/tn-{tenant}/ap-{app}/epg-{epg}",
                "name": epg
            }
        }
    }
    return session.post(url, json=payload, verify=False)


# -----------------------------
# Run all steps
# -----------------------------
if __name__ == "__main__":
    session = apic_login()

    # Define names
    TENANT = "Villans"
    APP = "Hackers"
    EPG = "Web"

    print("Creating Tenant...")
    print(create_tenant(session, TENANT).json())

    print("Creating App Profile...")
    print(create_app_profile(session, TENANT, APP).json())

    print("Creating EPG...")
    print(create_epg(session, TENANT, APP, EPG).json())

    print("\n✔ Completed: Tenant, App Profile, and EPG created.")
