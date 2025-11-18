#!/usr/bin/env python3
"""
ACME build script (3-tier, 3 BDs) for Cisco ACI using Python requests.

Creates:
- Tenant: ACME
- VRF: ACME-VRF
- Bridge Domains:
    - ACME-Web-BD  (10.10.10.1/24)
    - ACME-App-BD  (10.20.20.1/24)
    - ACME-DB-BD   (10.30.30.1/24)
- App Profiles:
    - Web_Tier
    - Application_Tier
    - Database_Tier
- EPGs:
    - Web EPGs bound to ACME-Web-BD
    - App EPGs bound to ACME-App-BD
    - DB EPGs bound to ACME-DB-BD
"""

import requests
import urllib3

urllib3.disable_warnings()  # ignore self-signed cert warnings (lab use only)

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = api url
USER = 'username'
PASS = 'password'

TENANT   = "ACME"
VRF_NAME = "ACME-VRF"

WEB_BD = "ACME-Web-BD"
APP_BD = "ACME-App-BD"
DB_BD  = "ACME-DB-BD"

WEB_SUBNET = "10.10.10.1/24"
APP_SUBNET = "10.20.20.1/24"
DB_SUBNET  = "10.30.30.1/24"

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
    resp.raise_for_status()

    token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    print("[+] Logged into APIC")
    return session


def ensure_tenant(session, tenant_name):
    """Create or update Tenant (fvTenant)."""
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


def ensure_vrf(session, tenant_name, vrf_name):
    """Create or update VRF (fvCtx) under tenant."""
    dn = f"uni/tn-{tenant_name}/ctx-{vrf_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvCtx": {
            "attributes": {
                "dn": dn,
                "name": vrf_name
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[VRF] '{vrf_name}' in '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def ensure_bd_with_subnet(session, tenant_name, bd_name, vrf_name, subnet_ip):
    """
    Create or update Bridge Domain (fvBD) with:
    - link to VRF (fvRsCtx)
    - single subnet (fvSubnet)
    """
    dn = f"uni/tn-{tenant_name}/BD-{bd_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvBD": {
            "attributes": {
                "dn": dn,
                "name": bd_name
            },
            "children": [
                {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": vrf_name
                        }
                    }
                },
                {
                    "fvSubnet": {
                        "attributes": {
                            "ip": subnet_ip,
                            "scope": "public"
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[BD] '{bd_name}' ({subnet_ip}) -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def ensure_app_profile(session, tenant_name, app_name):
    """Create or update Application Profile (fvAp)."""
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
    print(f"[APP] '{app_name}' in '{tenant_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def ensure_epg(session, tenant_name, app_name, epg_name, bd_name):
    """
    Create or update EPG (fvAEPg) and attach it to a BD via fvRsBd.
    """
    dn = f"uni/tn-{tenant_name}/ap-{app_name}/epg-{epg_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": dn,
                "name": epg_name
            },
            "children": [
                {
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[EPG] '{epg_name}' -> BD '{bd_name}' -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


# -----------------------------
# Main build sequence
# -----------------------------
if __name__ == "__main__":
    session = apic_login()

    print("\n=== Tenant and VRF ===")
    ensure_tenant(session, TENANT)
    ensure_vrf(session, TENANT, VRF_NAME)

    print("\n=== Bridge Domains (one per tier) ===")
    ensure_bd_with_subnet(session, TENANT, WEB_BD, VRF_NAME, WEB_SUBNET)
    ensure_bd_with_subnet(session, TENANT, APP_BD, VRF_NAME, APP_SUBNET)
    ensure_bd_with_subnet(session, TENANT, DB_BD,  VRF_NAME, DB_SUBNET)

    print("\n=== App Profiles ===")
    ensure_app_profile(session, TENANT, WEB_APP)
    ensure_app_profile(session, TENANT, APP_APP)
    ensure_app_profile(session, TENANT, DB_APP)

    print("\n=== Web Tier EPGs (→ ACME-Web-BD) ===")
    for epg in WEB_EPGS:
        ensure_epg(session, TENANT, WEB_APP, epg, WEB_BD)

    print("\n=== Application Tier EPGs (→ ACME-App-BD) ===")
    for epg in APP_EPGS:
        ensure_epg(session, TENANT, APP_APP, epg, APP_BD)

    print("\n=== Database Tier EPGs (→ ACME-DB-BD) ===")
    for epg in DB_EPGS:
        ensure_epg(session, TENANT, DB_APP, epg, DB_BD)

    print("\n[✓] ACME 3-BD build complete: Tenant, VRF, 3 BDs, App Profiles, and EPGs created and bound to the right BDs.")
