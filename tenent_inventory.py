#!/usr/bin/env python3
"""
Tenant inventory script for Cisco ACI using Python requests.

For a given tenant, show:

- VRFs in the tenant
- Bridge Domains in the tenant
- For each BD:
    - associated VRF
    - configured subnets
    - EPGs using that BD
"""

import requests
import urllib3

urllib3.disable_warnings()

# -----------------------------
# APIC connection parameters
# -----------------------------
APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'
TENANT = "ACME"               # <-- tenant to inspect


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
    resp.raise_for_status()

    token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    print(f"[+] Logged into APIC as {USER}")
    return session


# -----------------------------
# VRFs
# -----------------------------
def get_vrfs(session, tenant):
    """
    Get all VRFs (fvCtx) under a tenant.
    """
    url = (
        f"{APIC}/api/node/mo/uni/tn-{tenant}.json"
        "?query-target=children&target-subtree-class=fvCtx"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()
    vrfs = []
    for item in resp.json().get("imdata", []):
        ctx = item["fvCtx"]["attributes"]
        vrfs.append(ctx["name"])
    return vrfs


# -----------------------------
# Bridge Domains
# -----------------------------
def get_bds(session, tenant):
    """
    Get all BDs (fvBD) under a tenant.
    Returns dict: {bd_name: {"dn": dn}}
    """
    url = (
        f"{APIC}/api/node/mo/uni/tn-{tenant}.json"
        "?query-target=children&target-subtree-class=fvBD"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    bds = {}
    for item in resp.json().get("imdata", []):
        bd = item["fvBD"]["attributes"]
        name = bd["name"]
        dn = bd["dn"]
        bds[name] = {
            "dn": dn,
            "vrf": None,
            "subnets": [],
            "epgs": [],
        }
    return bds


def get_bd_vrf(session, bd_dn):
    """
    For a given BD DN, retrieve its associated VRF (via fvRsCtx).
    Returns VRF name or None.
    """
    url = (
        f"{APIC}/api/node/mo/{bd_dn}.json"
        "?query-target=children&target-subtree-class=fvRsCtx"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    data = resp.json().get("imdata", [])
    if not data:
        return None

    # There may be one fvRsCtx child
    for item in data:
        if "fvRsCtx" in item:
            attrs = item["fvRsCtx"]["attributes"]
            # usually tnFvCtxName holds the VRF name
            return attrs.get("tnFvCtxName")
    return None


def get_bd_subnets(session, bd_dn):
    """
    For a given BD DN, retrieve its subnets (fvSubnet).
    Returns list of (ip, scope) tuples.
    """
    url = (
        f"{APIC}/api/node/mo/{bd_dn}.json"
        "?query-target=children&target-subtree-class=fvSubnet"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    subnets = []
    for item in resp.json().get("imdata", []):
        if "fvSubnet" in item:
            s = item["fvSubnet"]["attributes"]
            ip = s.get("ip")
            scope = s.get("scope")  # e.g. "public", "private", "shared"
            subnets.append((ip, scope))
    return subnets


# -----------------------------
# EPGs and their BD bindings
# -----------------------------
def get_epgs(session, tenant):
    """
    Get all EPGs (fvAEPg) under a tenant.
    Returns list of {"name": ..., "dn": ...}
    """
    url = (
        f"{APIC}/api/node/mo/uni/tn-{tenant}.json"
        "?query-target=subtree&target-subtree-class=fvAEPg"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    epgs = []
    for item in resp.json().get("imdata", []):
        epg = item["fvAEPg"]["attributes"]
        epgs.append({
            "name": epg["name"],
            "dn": epg["dn"]
        })
    return epgs


def get_epg_bd(session, epg_dn):
    """
    For a given EPG DN, retrieve its associated BD via fvRsBd child.
    Returns BD name or None.
    """
    url = (
        f"{APIC}/api/node/mo/{epg_dn}.json"
        "?query-target=children&target-subtree-class=fvRsBd"
    )
    resp = session.get(url, verify=False)
    resp.raise_for_status()

    data = resp.json().get("imdata", [])
    if not data:
        return None

    for item in data:
        if "fvRsBd" in item:
            attrs = item["fvRsBd"]["attributes"]
            return attrs.get("tnFvBDName")
    return None


# -----------------------------
# Inventory builder
# -----------------------------
def build_tenant_inventory(session, tenant):
    """
    Build a nested structure:
    {
      "vrfs": [ ...names... ],
      "bds": {
          "BD_NAME": {
              "dn": "...",
              "vrf": "ACME-VRF",
              "subnets": [("10.0.10.1/24","public"), ...],
              "epgs": ["Web-Frontend", "App-Logic", ...]
          },
          ...
      }
    }
    """
    inventory = {
        "tenant": tenant,
        "vrfs": [],
        "bds": {}
    }

    # VRFs
    inventory["vrfs"] = get_vrfs(session, tenant)

    # BDs (structure initialised)
    bds = get_bds(session, tenant)

    # Fill in VRF and subnets for each BD
    for bd_name, info in bds.items():
        dn = info["dn"]
        info["vrf"] = get_bd_vrf(session, dn)
        info["subnets"] = get_bd_subnets(session, dn)

    # EPGs and which BD they use
    epgs = get_epgs(session, tenant)
    for epg in epgs:
        epg_name = epg["name"]
        epg_dn = epg["dn"]
        bd_name = get_epg_bd(session, epg_dn)
        if bd_name and bd_name in bds:
            bds[bd_name]["epgs"].append(epg_name)

    inventory["bds"] = bds
    return inventory


# -----------------------------
# Pretty-print inventory
# -----------------------------
def print_inventory(inv):
    print(f"\n=== Tenant Inventory: {inv['tenant']} ===\n")

    # VRFs
    print("VRFs:")
    if inv["vrfs"]:
        for vrf in inv["vrfs"]:
            print(f"  - {vrf}")
    else:
        print("  (none)")

    print("\nBridge Domains:")
    if not inv["bds"]:
        print("  (none)")
        return

    for bd_name, info in inv["bds"].items():
        print(f"\n  BD: {bd_name}")
        print(f"    DN:   {info['dn']}")
        print(f"    VRF:  {info['vrf'] or '(none linked)'}")

        # Subnets
        if info["subnets"]:
            print("    Subnets:")
            for ip, scope in info["subnets"]:
                print(f"      - {ip} (scope: {scope})")
        else:
            print("    Subnets: (none)")

        # EPGs
        if info["epgs"]:
            print("    EPGs using this BD:")
            for epg in info["epgs"]:
                print(f"      - {epg}")
        else:
            print("    EPGs using this BD: (none)")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    sess = apic_login()
    inv = build_tenant_inventory(sess, TENANT)
    print_inventory(inv)
