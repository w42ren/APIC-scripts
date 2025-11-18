import requests
import urllib3

urllib3.disable_warnings()  # ignore self-signed cert warnings (lab only)

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


def create_bridge_domain(session, tenant_name, bd_name):
    """
    Create a Bridge Domain in the given tenant.

    DN format: uni/tn-<tenant_name>/BD-<bd_name>
    Class: fvBD
    """
    dn = f"uni/tn-{tenant_name}/BD-{bd_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvBD": {
            "attributes": {
                "dn": dn,
                "name": bd_name
                # For a simple example we only set name + dn.
                # Advanced: add children here (fvRsCtx for VRF, fvSubnet for gateway, etc.)
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[BD] '{bd_name}' in tenant '{tenant_name}' -> Status {resp.status_code}")
    print("[BD] Body:", resp.text)
    return resp


if __name__ == "__main__":
    session = apic_login()

    TENANT = "ACME"
    BD_NAME = "ACME-BD"

    create_bridge_domain(session, TENANT, BD_NAME)

    print("\n[✓] Bridge Domain created in ACME tenant.")
