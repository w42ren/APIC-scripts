import requests
import urllib3

urllib3.disable_warnings()

APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'


def apic_login():
    session = requests.Session()
    payload = {
        "aaaUser": {
            "attributes": {"name": USER, "pwd": PASS}
        }
    }

    resp = session.post(f"{APIC}/api/aaaLogin.json", json=payload, verify=False)
    token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    session.cookies["APIC-cookie"] = token
    return session






def bd_link_vrf(session, tenant, bd_name, vrf_name):
    """
    Link BD to VRF (fvRsCtx under fvBD).
    """
    dn = f"uni/tn-{tenant}/BD-{bd_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvBD": {
            "attributes": {"dn": dn},
            "children": [
                {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": vrf_name
                        }
                    }
                }
            ]
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[BD→VRF] BD '{bd_name}' linked to VRF '{vrf_name}' → HTTP {resp.status_code}")
    print(resp.text)
    return resp

if __name__ == "__main__":
    session = apic_login()
    bd_link_vrf(session, tenant="ACME", vrf_name="ACME-VRF" , bd_name="ACME-BD")