import requests
import urllib3
from urllib.parse import quote

urllib3.disable_warnings()  # Ignore self-signed cert warnings (lab use only)

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'



def apic_login():
    """Log into APIC and return an authenticated session."""
    session = requests.Session()
    url = f"{APIC}/api/aaaLogin.json"

    payload = {
        "aaaUser": {
            "attributes": {
                "name": USER,
                "pwd": PASS
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print("[LOGIN] Status:", resp.status_code)
    print("[LOGIN] Body:", resp.text)
    resp.raise_for_status()

    token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    print("[+] Logged into APIC")
    return session


def create_tenant(session, tenant_name):
    dn = f"uni/tn-{tenant_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvTenant": {
            "attributes": {
                "dn": dn,
                "name": tenant_name
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[TENANT] '{tenant_name}' -> Status {resp.status_code}")
    print("[TENANT] Body:", resp.text)
    return resp


def create_app_profile(session, tenant_name, app_name):
    dn = f"uni/tn-{tenant_name}/ap-{app_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAp": {
            "attributes": {
                "dn": dn,
                "name": app_name
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[APP] '{app_name}' -> Status {resp.status_code}")
    print("[APP] Body:", resp.text)
    return resp


def create_epg(session, tenant_name, app_name, epg_name):
    dn = f"uni/tn-{tenant_name}/ap-{app_name}/epg-{epg_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": dn,
                "name": epg_name
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[EPG] '{epg_name}' in '{app_name}' -> Status {resp.status_code}")
    print("[EPG] Body:", resp.text)
    return resp


if __name__ == "__main__":
    session = apic_login()

    tenant = "ACME"

    web_epgs = [
        "Web-Frontend",
        "Public-Web",
        "WebServer-EPG",
        "Nginx-Web",
        "DMZ-Web",
    ]

    app_epgs = [
        "App-Middleware",
        "App-Logic",
        "Backend-App",
        "JavaApp-EPG",
        "API-Server-App",
    ]

    db_epgs = [
        "DB-Main",
        "SQL-DB",
        "Oracle-DB",
        "MongoDB-Cluster",
        "Finance-DB",
    ]

    # App profile names WITHOUT spaces
    web_app = "Web_Tier"
    app_tier = "Application_Tier"
    db_tier = "Database_Tier"

    # 1) Tenant
    create_tenant(session, tenant)

    # 2) Web Tier
    create_app_profile(session, tenant, web_app)
    for epg in web_epgs:
        create_epg(session, tenant, web_app, epg)

    # 3) Application Tier
    create_app_profile(session, tenant, app_tier)
    for epg in app_epgs:
        create_epg(session, tenant, app_tier, epg)

    # 4) Database Tier
    create_app_profile(session, tenant, db_tier)
    for epg in db_epgs:
        create_epg(session, tenant, db_tier, epg)

    print("\n[✓] Finished creating ACME tenant, app profiles, and EPGs.")

