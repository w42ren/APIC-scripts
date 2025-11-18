#!/usr/bin/env python3
"""
Add subnets to a Bridge Domain in Cisco ACI using Python requests.

Default:
- Tenant: ACME
- Bridge Domain: ACME-BD
- Subnets: example gateway subnets for Web/App/DB tiers
"""

import requests
import urllib3

urllib3.disable_warnings()  # lab use only – ignore self-signed cert warnings

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = api url
USER = 'username'
PASS = 'password'

TENANT = "ACME"
BD_NAME = "ACME-BD"

# Example subnets to add to the BD
# Typically these are the default gateways for your Web/App/DB tiers.
SUBNETS = [
    {"ip": "10.10.10.1/24", "scope": "public"},   # Web tier gateway
    {"ip": "10.20.20.1/24", "scope": "public"},   # App tier gateway
    {"ip": "10.30.30.1/24", "scope": "public"},   # DB tier gateway
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


def add_subnets_to_bd(session, tenant, bd_name, subnets):
    """
    Add one or more fvSubnet children to a Bridge Domain.

    subnets: list of dicts: [{"ip": "10.10.10.1/24", "scope": "public"}, ...]
    """
    bd_dn = f"uni/tn-{tenant}/BD-{bd_name}"
    url = f"{APIC}/api/mo/{bd_dn}.json"

    # Build children list for all subnets
    children = []
    for s in subnets:
        ip = s["ip"]
        scope = s.get("scope", "public")  # default scope = public
        children.append(
            {
                "fvSubnet": {
                    "attributes": {
                        "ip": ip,
                        "scope": scope
                        # You could add "descr" or "virtual": "yes" if needed
                    }
                }
            }
        )

    payload = {
        "fvBD": {
            "attributes": {
                "dn": bd_dn
                # no explicit status -> safe to re-run (idempotent-ish)
            },
            "children": children
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[BD SUBNETS] BD '{bd_name}' in tenant '{tenant}' -> HTTP {resp.status_code}")
    print(resp.text)
    return resp


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    sess = apic_login()
    add_subnets_to_bd(sess, TENANT, BD_NAME, SUBNETS)
    print("\n[✓] Subnets added to Bridge Domain.")
