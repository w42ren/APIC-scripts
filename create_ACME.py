#!/usr/bin/env python3
"""
Full ACME build script for Cisco ACI using Python requests.

Creates:
- Tenant: ACME
- VRF: ACME-VRF
- Bridge Domain: ACME-BD (linked to ACME-VRF)
- App Profiles: Web_Tier, Application_Tier, Database_Tier
- EPGs in each App Profile, all attached to ACME-BD
"""

import requests
import urllib3

urllib3.disable_warnings()  # ignore self-signed cert warnings (lab use only)

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'

TENANT = "ACME"
VRF_NAME = "ACME-VRF"
BD_NAME = "ACME-BD"

WEB_APP = "Web_Tier"
APP_APP = "Application_Tier"
DB_APP  = "Database_Tier"


# EPG sets
WEB_EPGS = [
    "Web-Frontend",
    "Public-Web",
    "WebServer-EPG",
    "Nginx-Web",
    "DMZ-Web",
]

APP_EPGS = [
    "App-Middleware",
    "App-Logic",
    "Backend-App",
    "JavaApp-EPG",
    "API-Server-App",
]

DB_EPGS = [
    "DB-Main",
    "SQL-DB",
    "Oracle-DB",
    "MongoDB-Cluster",
    "Finance-DB",
]


# -----------------------------
# Helper functions
# -----------------------------

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
    if resp.status_code != 200:
        print("[LOGIN] Body:", resp.text)
        resp.raise_for_status()

    token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    print("[+] Logged into APIC")
    return session


def create_tenant(session, tenant_name):
    """Create Tenant fvTenant."""
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
    print(f"[TENANT] '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def create_vrf(session, tenant_name, vrf_name):
    """Create VRF (fvCtx) under tenant."""
    dn = f"uni/tn-{tenant_name}/ctx-{vrf_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvCtx": {
            "attributes": {
                "dn": dn,
                "name": vrf_name,
                "status": "created,modified"
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[VRF] '{vrf_name}' in '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def create_bd(session, tenant_name, bd_name, vrf_name=None):
    """
    Create Bridge Domain (fvBD) under tenant.
    If vrf_name is given, link BD to VRF using fvRsCtx.
    """
    dn = f"uni/tn-{tenant_name}/BD-{bd_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    bd = {
        "fvBD": {
            "attributes": {
                "dn": dn,
                "name": bd_name,
                "status": "created,modified"
            },
            "children": []
        }
    }

    if vrf_name:
        bd["fvBD"]["children"].append(
            {
                "fvRsCtx": {
                    "attributes": {
                        "tnFvCtxName": vrf_name
                    }
                }
            }
        )

    resp = session.post(url, json=bd, verify=False)
    print(f"[BD] '{bd_name}' in '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def create_app_profile(session, tenant_name, app_name):
    """Create Application Profile (fvAp)."""
    dn = f"uni/tn-{tenant_name}/ap-{app_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAp": {
            "attributes": {
                "dn": dn,
                "name": app_name,
                "status": "created,modified"
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[APP] '{app_name}' in '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def create_epg(session, tenant_name, app_name, epg_name, bd_name):
    """
    Create EPG (fvAEPg) and attach it to BD via fvRsBd.
    """
    dn = f"uni/tn-{tenant_name}/ap-{app_name}/epg-{epg_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": dn,
                "name": epg_name,
                "status": "created,modified"
            },
            "children": [
                {
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name    # link to Bridge Domain
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[EPG] '{epg_name}' in '{app_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


# -----------------------------
# Main build sequence
# -----------------------------
if __name__ == "__main__":
    session = apic_login()

    print("\n=== Creating Tenant / VRF / BD ===")
    create_tenant(session, TENANT)
    create_vrf(session, TENANT, VRF_NAME)
    create_bd(session, TENANT, BD_NAME, vrf_name=VRF_NAME)

    print("\n=== Creating App Profiles ===")
    create_app_profile(session, TENANT, WEB_APP)
    create_app_profile(session, TENANT, APP_APP)
    create_app_profile(session, TENANT, DB_APP)

    print("\n=== Creating Web Tier EPGs ===")
    for epg in WEB_EPGS:
        create_epg(session, TENANT, WEB_APP, epg, BD_NAME)

    print("\n=== Creating Application Tier EPGs ===")
    for epg in APP_EPGS:
        create_epg(session, TENANT, APP_APP, epg, BD_NAME)

    print("\n=== Creating Database Tier EPGs ===")
    for epg in DB_EPGS:
        create_epg(session, TENANT, DB_APP, epg, BD_NAME)

    print("\n[✓] ACME build complete: Tenant, VRF, BD, App Profiles, and EPGs created and bound to ACME-BD.")
