# User Guide

Short practical guide for running and adapting the platform.

## 1. Prerequisites

- Windows 10/11 (or any OS with Python 3.10+)
- Python 3.10+ installed
- (Optional) Yingdao RPA for the production web-automation channel

## 2. Quick start (demo mode)

```bash
pip install -r requirements.txt
python run_demo.py
```

The pipeline will:
1. Generate (or reuse) mock order data in `data/raw/orders_raw.csv`
2. Store all orders in `data/orders.db` (SQLite)
3. Clean the data and produce a quality report
4. Export `data/reports/orders_report_<timestamp>.xlsx`

## 3. Configuration

Copy `config.example.ini` to `config.ini` and edit:

| Section | Key | Meaning |
|---|---|---|
| `[ingest]` | `mode` | `mock` or `api` |
| `[ingest]` | `api_url` | REST API endpoint (WooCommerce `/wc/v3/orders`) |
| `[cleaning]` | `required_fields` | columns that must be non-empty |
| `[cleaning]` | `min_amount` / `max_amount` | valid amount range |
| `[alert]` | `smtp_*` | SMTP settings for alert emails |
| `[alert]` | `retry_times` | email send retries |
| `[alert]` | `alert_after_consecutive_failures` | failures before alerting |

### Secrets via environment variables (recommended)

Never commit real credentials. Override instead:

```bash
set RPA_SMTP_PASSWORD=your_app_password
set RPA_API_TOKEN=your_token
python run_demo.py --mode api
```

All env overrides are listed in `src/rpa_platform/config.py`.

## 4. Demo data generation

```bash
python scripts/generate_mock_data.py --count 500 --seed 42
```

Generates `data/raw/orders_raw.csv` with deliberately dirty rows
(empty fields, duplicates, bad amounts, malformed dates) so the cleaning
stage is exercised.

## 5. Tests

```bash
pip install -e ".[dev]"
pytest            # run the suite
ruff check src tests scripts run_demo.py   # lint
```

## 6. Production channel with Yingdao RPA

1. Import `yingdao_rpa/order_crawl.rdx` into Yingdao RPA.
2. The flow logs into the order backend, scrapes the day's orders and
   appends them to `data/raw/orders_raw.csv` (same schema as mock output).
3. Schedule Yingdao to run daily; schedule `python run_demo.py` afterwards,
   or call it from within the Yingdao flow via "Run Python script".

See `yingdao_rpa/README.md` for the flow design.

## 7. Interpreting outputs

- **Report workbook** – `Summary` (KPIs), `Quality Report` (cleaning stats),
  `Order Details` (valid orders).
- **Audit log** – every step has a timestamped entry in `data/logs/rpa.log`.
- **Alert email** – sent after `alert_after_consecutive_failures`
  consecutive failed runs, including the last run statuses.
