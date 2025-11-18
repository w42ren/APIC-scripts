# ACI Automation Lab -- ACME 3-Tier Application Deployment

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

-   Interact with Cisco ACI using the **REST API**
-   Automate ACI configuration using **Python + requests**
-   Build a complete **3-tier application network** in ACI:
    -   Tenant → VRF → Bridge Domains → Application Profiles → EPGs →
        Contracts
-   Use inventory scripts to **validate and document** the configuration
-   Understand the relationship between **microsegmentation**, **EPGs**,
    and **contracts**

This lab simulates how a real enterprise (ACME Ltd.) deploys a
production application in an ACI fabric.

------------------------------------------------------------------------

# 🏗️ Lab Overview

You will deploy the following logical architecture using Python
automation:

    Tenant: ACME
        VRF: ACME-VRF

        Bridge Domains (one per tier):
            ACME-Web-BD (10.10.10.1/24)
            ACME-App-BD (10.20.20.1/24)
            ACME-DB-BD  (10.30.30.1/24)

        App Profiles:
            Web_Tier
            Application_Tier
            Database_Tier

        EPGs:
            (5 Web EPGs)
            (5 Application EPGs)
            (5 Database EPGs)

        Contracts:
            Web-To-App (HTTP/HTTPS)
            App-To-DB  (SQL)

This structure mirrors a realistic 3-tier enterprise system using ACI's
policy-based networking.

------------------------------------------------------------------------

# 🧰 Prerequisites

Before starting, ensure you have:

1.  A running Cisco **APIC Simulator** or live ACI fabric\
2.  Python **3.9+** installed\
3.  Required Python modules:

```{=html}
<!-- -->
```
    pip install requests

4.  Update each script with your:
    -   APIC URL/IP\
    -   Username\
    -   Password

------------------------------------------------------------------------

# 📂 Files in This Lab

  -----------------------------------------------------------------------
  Script                          Purpose
  ------------------------------- ---------------------------------------
  `acme_build.py`                 Builds the full ACME tenant, VRF, BDs,
                                  App Profiles, and EPGs

  `acme_contracts.py`             Creates filters and contracts and binds
                                  them to EPGs

  `acme_bd_inventory.py`          Shows VRFs, BDs, subnets, and their
                                  associated EPGs

  `acme_contract_inventory.py`    Shows which contracts each EPG
                                  provides/consumes

  `README.md`                     Full student lab guide
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 🚀 Step 1 -- Build the ACME Tenant & 3-Tier Application

Run:

    python acme_build.py

This script:

-   Creates tenant **ACME**
-   Creates VRF **ACME-VRF**
-   Creates **three Bridge Domains**:
    -   `ACME-Web-BD` with 10.10.10.1/24\
    -   `ACME-App-BD` with 10.20.20.1/24\
    -   `ACME-DB-BD` with 10.30.30.1/24\
-   Creates **three Application Profiles**\
-   Creates **15 EPGs** and binds them to the appropriate BD

### Example Output

    [TENANT] 'ACME' -> HTTP 200
    [VRF] 'ACME-VRF' -> HTTP 200
    [BD] 'ACME-Web-BD'  (10.10.10.1/24)
    [BD] 'ACME-App-BD'  (10.20.20.1/24)
    [BD] 'ACME-DB-BD'   (10.30.30.1/24)

    === EPGs ===
    [EPG] Web-Frontend -> BD 'ACME-Web-BD'
    ...

------------------------------------------------------------------------

# 🔐 Step 2 -- Configure Contracts Between Tiers

Run:

    python acme_contracts.py

This script creates:

### Filters:

-   `WEB-TO-APP-FILTER` → TCP/80 + TCP/443\
-   `APP-TO-DB-FILTER` → TCP/1433 + TCP/3306

### Contracts:

-   `Web-To-App-Contract`\
-   `App-To-DB-Contract`

### Bindings:

-   **Web Tier** EPGs **consume** Web→App\
-   **Application Tier** EPGs **provide** Web→App AND **consume**
    App→DB\
-   **Database Tier** EPGs **provide** App→DB

This implements real microsegmentation.

------------------------------------------------------------------------

# 📊 Step 3 -- Validate VRFs, Bridge Domains & EPGs

Run:

    python acme_bd_inventory.py

This script lists:

-   VRFs\
-   Bridge Domains\
-   Subnets\
-   EPGs per BD\
-   BD → VRF associations

### Example Output

    VRFs:
      - ACME-VRF

    Bridge Domains:
      ACME-Web-BD
        Subnet: 10.10.10.1/24
        EPGs:
          - Web-Frontend
          - Public-Web
          ...

------------------------------------------------------------------------

# 🔍 Step 4 -- Validate Contract Policy (EPG Relationships)

Run:

    python acme_contract_inventory.py

This script shows:

-   App Profile → EPG\
-   Provided contracts\
-   Consumed contracts

### Example Output

    App Profile: Web_Tier
      EPG: Web-Frontend
        Provides: (none)
        Consumes: Web-To-App-Contract

    App Profile: Application_Tier
      EPG: App-Logic
        Provides: Web-To-App-Contract
        Consumes: App-To-DB-Contract

This helps students understand the ACI policy graph.

------------------------------------------------------------------------

# 🧪 Step 5 -- Challenge Tasks

### ✔️ **Task A -- Add an SSH Management Contract**

Create a new contract: - Filter: TCP/22\
- Contract: `Mgmt-SSH-Contract`\
- Bind to selected EPGs only

### ✔️ **Task B -- Add a Logging Tier**

Create: - BD: `ACME-Log-BD`\
- Subnet: 10.40.40.1/24\
- App Profile: `Logging_Tier`\
- EPGs: `Log-Collector`, `Log-Forwarder`\
- Contract: App → Log

### ✔️ **Task C -- Export Documentation**

Modify the inventory scripts to output: - JSON (`acme_inventory.json`) -
CSV (`acme_epgs.csv`)

------------------------------------------------------------------------

# 🎓 What You Learned

You now understand how to:

-   Build an ACI tenant programmatically\
-   Define VRFs, Bridge Domains, subnets, and EPGs\
-   Implement microsegmentation using filters and contracts\
-   Verify configuration using automation\
-   Apply policy-based networking concepts\
-   Document a real fabric using REST APIs

These are key skills for:

-   Network Automation\
-   Cisco DevNet\
-   Cybersecurity & Zero Trust\
-   Data Centre engineering\
-   Cloud-ready infrastructure design

------------------------------------------------------------------------

# 🙌 End of Lab

You now have a fully automated, production-style ACME deployment in
Cisco ACI.


