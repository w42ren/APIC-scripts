import requests
import urllib3

urllib3.disable_warnings()

APIC = api url
USER = 'username'
PASS = 'password'


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


def create_vrf(session, tenant, vrf_name):
    """
    Create a VRF in ACME tenant.
    DN: uni/tn-ACME/ctx-ACME-VRF
    """
    dn = f"uni/tn-{tenant}/ctx-{vrf_name}"
    url = f"{APIC}/api/mo/{dn}.json"

    payload = {
        "fvCtx": {
            "attributes": {
                "dn": dn,
                "name": vrf_name,
                "status": "created"
            }
        }
    }

    resp = session.post(url, json=payload, verify=False)
    print(f"[VRF] '{vrf_name}' created → HTTP {resp.status_code}")
    print(resp.text)
    return resp


if __name__ == "__main__":
    session = apic_login()
    create_vrf(session, tenant="ACME", vrf_name="ACME-VRF")
