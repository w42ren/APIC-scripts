#!/usr/bin/env python3
"""
ACME contracts script for Cisco ACI using Python requests.

Assumes:
- Tenant: ACME
- App Profiles:
    - Web_Tier
    - Application_Tier
    - Database_Tier
- EPGs created by the 3-BD ACME build script.

Creates:
- Filters:
    - WEB-TO-APP-FILTER (TCP 80, 443)
    - APP-TO-DB-FILTER (TCP 1433, 3306)
- Contracts:
    - Web-To-App-Contract (uses WEB-TO-APP-FILTER)
    - App-To-DB-Contract (uses APP-TO-DB-FILTER)
- Binds contracts:
    - Web EPGs consume Web-To-App-Contract
    - App EPGs provide Web-To-App-Contract and consume App-To-DB-Contract
    - DB EPGs provide App-To-DB-Contract
"""

import requests
import urllib3

urllib3.disable_warnings()  # lab only

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'

TENANT = "ACME"

WEB_APP = "Web_Tier"
APP_APP = "Application_Tier"
DB_APP  = "Database_Tier"

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

WEB_TO_APP_FILTER = "WEB-TO-APP-FILTER"
APP_TO_DB_FILTER  = "APP-TO-DB-FILTER"

WEB_TO_APP_CONTRACT = "Web-To-App-Contract"
APP_TO_DB_CONTRACT  = "App-To-DB-Contract"


# -----------------------------
# Login
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


# -----------------------------
# Filters
# -----------------------------
def ensure_filter_web_to_app(session):
    """
    Create/update WEB-TO-APP-FILTER with HTTP/HTTPS entries.
    """
    dn = f"uni/tn-{TENANT}/flt-{WEB_TO_APP_FILTER}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "vzFilter": {
            "attributes": {
                "dn": dn,
                "name": WEB_TO_APP_FILTER,
            },
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "HTTP",
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": "80",
                            "dToPort": "80"
                        }
                    }
                },
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "HTTPS",
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": "443",
                            "dToPort": "443"
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[FILTER] {WEB_TO_APP_FILTER} -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def ensure_filter_app_to_db(session):
    """
    Create/update APP-TO-DB-FILTER with SQL-related ports.
    """
    dn = f"uni/tn-{TENANT}/flt-{APP_TO_DB_FILTER}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "vzFilter": {
            "attributes": {
                "dn": dn,
                "name": APP_TO_DB_FILTER,
            },
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "MSSQL",
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": "1433",
                            "dToPort": "1433"
                        }
                    }
                },
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "MySQL",
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": "3306",
                            "dToPort": "3306"
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[FILTER] {APP_TO_DB_FILTER} -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


# -----------------------------
# Contracts
# -----------------------------
def ensure_contract(session, contract_name, filter_name):
    """
    Create/update a contract (vzBrCP) with one subject referencing a filter.
    """
    dn = f"uni/tn-{TENANT}/brc-{contract_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "vzBrCP": {
            "attributes": {
                "dn": dn,
                "name": contract_name,
            },
            "children": [
                {
                    "vzSubj": {
                        "attributes": {
                            "name": f"{contract_name}-Subj"
                        },
                        "children": [
                            {
                                "vzRsSubjFiltAtt": {
                                    "attributes": {
                                        "tnVzFilterName": filter_name
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[CONTRACT] {contract_name} -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


# -----------------------------
# Bind contracts to EPGs
# -----------------------------
def epg_dn(tenant, app, epg):
    return f"uni/tn-{tenant}/ap-{app}/epg-{epg}"


def epg_provide_contract(session, tenant, app, epg, contract_name):
    """
    Make an EPG PROVIDE a contract (fvRsProv).
    """
    dn = epg_dn(tenant, app, epg)
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": dn
            },
            "children": [
                {
                    "fvRsProv": {
                        "attributes": {
                            "tnVzBrCPName": contract_name
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[EPG PROVIDE] {epg} provides {contract_name} -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


def epg_consume_contract(session, tenant, app, epg, contract_name):
    """
    Make an EPG CONSUME a contract (fvRsCons).
    """
    dn = epg_dn(tenant, app, epg)
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvAEPg": {
            "attributes": {
                "dn": dn
            },
            "children": [
                {
                    "fvRsCons": {
                        "attributes": {
                            "tnVzBrCPName": contract_name
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[EPG CONSUME] {epg} consumes {contract_name} -> HTTP {resp.status_code}")
    if resp.status_code >= 300:
        print(resp.text)
    return resp


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    sess = apic_login()

    print("\n=== Create Filters ===")
    ensure_filter_web_to_app(sess)
    ensure_filter_app_to_db(sess)

    print("\n=== Create Contracts ===")
    ensure_contract(sess, WEB_TO_APP_CONTRACT, WEB_TO_APP_FILTER)
    ensure_contract(sess, APP_TO_DB_CONTRACT,  APP_TO_DB_FILTER)

    print("\n=== Bind Contracts to EPGs ===")

    # Web tier: consume Web->App
    print("\n[Web Tier EPGs consume Web-To-App-Contract]")
    for epg in WEB_EPGS:
        epg_consume_contract(sess, TENANT, WEB_APP, epg, WEB_TO_APP_CONTRACT)

    # App tier: provide Web->App, consume App->DB
    print("\n[Application Tier EPGs provide Web-To-App-Contract and consume App-To-DB-Contract]")
    for epg in APP_EPGS:
        epg_provide_contract(sess, TENANT, APP_APP, epg, WEB_TO_APP_CONTRACT)
        epg_consume_contract(sess, TENANT, APP_APP, epg, APP_TO_DB_CONTRACT)

    # DB tier: provide App->DB
    print("\n[Database Tier EPGs provide App-To-DB-Contract]")
    for epg in DB_EPGS:
        epg_provide_contract(sess, TENANT, DB_APP, epg, APP_TO_DB_CONTRACT)

    print("\n[✓] Contracts and bindings configured for ACME 3-tier app.")
