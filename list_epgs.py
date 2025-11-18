import requests
import json
import urllib3

urllib3.disable_warnings()  # suppress self-signed cert warnings

APIC = 'https://sandboxapicdc.cisco.com'
USER = 'admin'
PASS = '!v3G@!4@Y'


def apic_login():
    """
    Logs into APIC and returns an authenticated session
    including the APIC session cookie.
    """
    login_url = f"{APIC}/api/aaaLogin.json"
    payload = {
        "aaaUser": {
            "attributes": {
                "name": USER,
                "pwd": PASS
            }
        }
    }

    session = requests.Session()
    response = session.post(login_url, json=payload, verify=False)

    # Extract token and attach cookie
    token = response.json()['imdata'][0]['aaaLogin']['attributes']['token']
    session.cookies['APIC-cookie'] = token

    return session


def get_epgs(session):
    """
    Retrieves all EPGs (fvAEPg objects) from the APIC.
    """
    url = f"{APIC}/api/node/class/fvAEPg.json"
    response = session.get(url, verify=False)
    return response.json()


def print_epg_list(epg_data):
    """
    Nicely prints the EPG names, tenants, and application profiles.
    """
    print("\n--- EPG List ---")

    for item in epg_data.get("imdata", []):
        epg = item["fvAEPg"]["attributes"]
        
        epg_name = epg["name"]
        dn = epg["dn"]  # contains full path e.g. uni/tn-Heroes/ap-App1/epg-Frontend

        # extract items from the DN
        parts = dn.split("/")
        tenant  = parts[1].replace("tn-", "")
        app     = parts[2].replace("ap-", "")

        print(f"Tenant: {tenant:15}  App Profile: {app:15}  EPG: {epg_name}")


if __name__ == "__main__":
    session = apic_login()
    epgs = get_epgs(session)
    print_epg_list(epgs)
