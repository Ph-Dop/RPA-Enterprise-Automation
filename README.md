# Enterprise Multi-Scenario RPA Automation Platform

> RPA automation solution for SME office workflow automation.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![CI](https://github.com/Ph-Dop/RPA-Enterprise-Automation/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Project Intro

This project is a **hybrid RPA solution** built with **Yingdao RPA** and **Python**.
It automates repetitive sales order collection, data cleaning, weekly/monthly report
generation and failure alerting. The platform ships with robust exception handling,
automatic retry, full running logs and email notification - ready for real daily
office use in small and medium enterprises (SMEs).

**Why hybrid?** Yingdao RPA handles no-code web/desktop process orchestration;
Python handles data cleaning, API integration, KPI calculation and alerting. The
two sides talk through plain files/SQLite, so each stays replaceable.

## Tech Stack

- **Yingdao RPA** – process orchestration & web operation automation (production channel)
- **Python 3.10+** – data processing, report generation, alert system
- **Pandas / Openpyxl** – data frames & styled Excel output
- **Requests** – REST API ingestion (WooCommerce / Shopify style)
- **smtplib** – email alerting
- **SQLite** – system of record for orders & run audit log

## Core Modules

1. **Sales Order Crawling & Data Cleaning**
   Auto-fetch order data (web page via Yingdao RPA, or REST API via Python),
   remove empty/duplicate/invalid rows, flag out-of-range amounts, and merge
   the result into a central SQLite store + a unified Excel table.

2. **Automatic Business Report**
   Compute KPIs (total revenue, order count, average order value, monthly
   breakdown) and export a **formatted Excel report with a built-in data
   quality report** (before/after statistics, issue classification).

3. **Exception Monitor & Email Alert**
   Full audit log of every step; automatic retry on failure; after N
   consecutive failures an alert email with the error context is sent to
   the responsible person.

## Architecture (dual-channel ingestion)

```
                 PRODUCTION CHANNEL                 DEMO / DEV CHANNEL
   Yingdao RPA web automation  --\            /--  Python mock generator
                                  \          /     (or REST API ingestion)
                                   v        v
                              raw orders (CSV / SQLite)
                                       |
                          cleaning -> quality report
                                       |
                       Excel business report + email alerting
```

Any clone can run the whole pipeline with Python only - no Yingdao RPA
required - because the mock/API ingestion channels produce exactly the same
schema as the Yingdao flow.

## Project Features

- ✅ Parameterized configuration (`config.ini` / environment variables) – adapt to different companies without touching code
- ✅ Complete exception handling and automatic retry mechanism
- ✅ Audit running log for workflow traceability (compliance-friendly)
- ✅ Separation of low-code RPA flow and Python extended logic
- ✅ Dual-channel ingestion – demo runs without commercial software
- ✅ Unit tests + CI (pytest, ruff) on GitHub Actions

## How to Run (one command, no RPA software needed)

```bash
# 1. install dependencies (Python 3.10+)
pip install -r requirements.txt

# 2. run the end-to-end pipeline (mock data, generates a report automatically)
python run_demo.py

# 3. see the alerting path: simulate a failure, then run again
python run_demo.py --fail-once
python run_demo.py
```

Outputs:
- `data/reports/orders_report_YYYYMMDD_HHMMSS.xlsx` – business report + quality report
- `data/logs/rpa.log` – audit log
- `data/orders.db` – SQLite store (orders + run log)

### Going live with a real API

```bash
python run_demo.py --mode api
```

Set `api_url` / credentials in `config.ini` or via environment variables
(`RPA_API_URL`, `RPA_API_CONSUMER_KEY`, ...). See `docs/user_guide.md`.

## Project Structure

```
RPA-Enterprise-Automation/
├── README.md
├── pyproject.toml            # packaging + lint/test config
├── config.example.ini        # config template (copy to config.ini)
├── run_demo.py               # one-command pipeline entry
├── src/rpa_platform/
│   ├── config.py             # typed config with env overrides
│   ├── logger.py             # audit logging
│   ├── storage.py            # SQLite persistence
│   ├── ingest/               # mock + API ingestion channels
│   ├── cleaning/             # data cleaning + quality report
│   ├── reporting/            # KPI + Excel report generation
│   └── alerting/             # email alert + failure tracker
├── tests/                    # pytest suite (cleaning/reporting/alerting)
├── scripts/generate_mock_data.py
├── yingdao_rpa/              # Yingdao RPA project (order_crawl.rdx)
├── docs/user_guide.md
└── .github/workflows/ci.yml
```

## Demo

A short demo video (`demo/demo_video.mp4`) shows the whole end-to-end
automation process: flow start, order ingestion, report generation and
failure alerting. *(To be recorded - see `demo/README.md`.)*

## License

MIT
