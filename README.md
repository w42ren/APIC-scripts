# ACI Automation Lab -- ACME 3-Tier Application Deployment

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

-   Interact with Cisco ACI using the REST API
-   Automate ACI configuration using Python + requests
-   Build a complete 3-tier application network in ACI:
    -   Tenant → VRF → Bridge Domains → Application Profiles → EPGs →
        Contracts
-   Use inventory scripts to validate and document the configuration
-   Understand the relationship between microsegmentation, EPGs, and
    contracts

## 🏗️ Lab Overview

You will deploy the following logical architecture using Python
automation:

Tenant: ACME VRF: ACME-VRF

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

## 🧰 Prerequisites

-   Cisco APIC Simulator or live ACI fabric\
-   Python 3.9+\
-   Install dependencies:

```{=html}
<!-- -->
```
    pip install requests

## 🚀 Step 1 -- Run the ACME Build Script

    python acme_build.py

## 🔐 Step 2 -- Configure Contracts

    python acme_contracts.py

## 📊 Step 3 -- Validate VRFs, BDs, Subnets, EPGs

    python acme_bd_inventory.py

## 🔍 Step 4 -- Validate Contracts

    python acme_contract_inventory.py

## 🧪 Step 5 -- Challenge Tasks

-   Add SSH contract\
-   Add a Logging tier\
-   Export tenant inventory to JSON/CSV

## 🎓 What You Learned

-   ACI policy model\
-   ACI automation with REST\
-   Microsegmentation with EPGs and contracts\
-   Documentation and verification using inventory scripts
