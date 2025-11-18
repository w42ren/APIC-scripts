#!/usr/bin/env python3
"""
ACME Contracts Inventory for Cisco ACI using Python requests.

For a given tenant (default: ACME), this script:

- Lists all EPGs (fvAEPg)
- For each EPG, discovers:
    - Provided contracts (fvRsProv)
    - Consumed contracts (fvRsCons)
- Prints a summary: App Profile -> EPG -> Provides / Consumes
"""

import requests
import urllib3

urllib3.disable_warnings()

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = api url
USER = 'username'
PASS = 'password'
TENANT = "Heroes"               # <-- tenant to inspect


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
    print(f"[+] Logged into APIC as {USER}")
    return session


# -----------------------------
# EPG discovery
# -----------------------------
def get_epgs(session, tenant):
    """
    Get all EPGs (fvAEPg) under a tenant.

    Returns list of dicts:
        {
          "name": <EPG name>,
          "dn":   <EPG DN>,
          "app":  <App profile name>
        }
    """
    url = (
        f"{APIC}/api/node/mo/uni/tn-{tenant}.json"
        "?query-target=subtree&target-subtree-class=fvAEPg"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    epgs = []
    for item in resp.json().get("imdata", []):
        attrs = item["fvAEPg"]["attributes"]
        dn = attrs["dn"]
        name = attrs["name"]

        # DN format: uni/tn-ACME/ap-<App>/epg-<EPG>
        parts = dn.split("/")
        app_name = None
        for p in parts:
            if p.startswith("ap-"):
                app_name = p[3:]  # strip 'ap-'
                break

        epgs.append({
            "name": name,
            "dn": dn,
            "app": app_name or "(unknown-app)"
        })

    return epgs


def get_epg_contracts(session, epg_dn):
    """
    For a given EPG DN, retrieve lists of:

    - provided contracts (fvRsProv -> tnVzBrCPName)
    - consumed contracts (fvRsCons -> tnVzBrCPName)

    Returns: (provided_list, consumed_list)
    """
    url = f"{APIC}/api/mo/{epg_dn}.json?query-target=children"
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    provided = set()
    consumed = set()

    for item in resp.json().get("imdata", []):
        if "fvRsProv" in item:
            attrs = item["fvRsProv"]["attributes"]
            brc_name = attrs.get("tnVzBrCPName")
            if brc_name:
                provided.add(brc_name)

        if "fvRsCons" in item:
            attrs = item["fvRsCons"]["attributes"]
            brc_name = attrs.get("tnVzBrCPName")
            if brc_name:
                consumed.add(brc_name)

    return sorted(provided), sorted(consumed)


# -----------------------------
# Build inventory
# -----------------------------
def build_contract_inventory(session, tenant):
    """
    Build structure:
    {
      "tenant": "ACME",
      "apps": {
        "Web_Tier": [
            {
              "epg": "Web-Frontend",
              "provides": [...],
              "consumes": [...]
            },
            ...
        ],
        "Application_Tier": [...],
        "Database_Tier": [...]
      }
    }
    """
    inv = {
        "tenant": tenant,
        "apps": {}
    }

    epgs = get_epgs(session, tenant)

    for epg in epgs:
        app = epg["app"]
        epg_name = epg["name"]
        epg_dn = epg["dn"]

        provides, consumes = get_epg_contracts(session, epg_dn)

        if app not in inv["apps"]:
            inv["apps"][app] = []

        inv["apps"][app].append({
            "epg": epg_name,
            "provides": provides,
            "consumes": consumes
        })

    return inv


# -----------------------------
# Pretty-print inventory
# -----------------------------
def print_contract_inventory(inv):
    print(f"\n=== Contract Inventory for Tenant: {inv['tenant']} ===\n")

    if not inv["apps"]:
        print("No EPGs found in this tenant.")
        return

    for app, epg_list in inv["apps"].items():
        print(f"App Profile: {app}")
        if not epg_list:
            print("  (no EPGs)")
            continue

        for epg_info in epg_list:
            epg = epg_info["epg"]
            provides = epg_info["provides"]
            consumes = epg_info["consumes"]

            print(f"  EPG: {epg}")
            print(f"    Provides: {', '.join(provides) if provides else '(none)'}")
            print(f"    Consumes: {', '.join(consumes) if consumes else '(none)'}")
        print()  # blank line between app profiles


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    sess = apic_login()
    inventory = build_contract_inventory(sess, TENANT)
    print_contract_inventory(inventory)
