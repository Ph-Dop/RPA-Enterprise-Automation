# Yingdao RPA Project

This folder hosts the **production channel** of the platform: the Yingdao RPA
flow that automates the web-operation part which Python cannot (or should not)
do - logging into the order backend and scraping the day's orders.

## Why is this folder just a README right now?

The actual Yingdao project (`.rdx` file) is created inside the Yingdao RPA
client and cannot be authored as plain text. It will be exported here after
the flow is built in the GUI. The Python side does **not** depend on it:
`python run_demo.py` already runs the full pipeline with mock/API data.

## Planned flow: `order_crawl.rdx`

| Step | Yingdao command | Purpose |
|---|---|---|
| 1 | Open Browser → URL | open order backend login page |
| 2 | Fill/Click | login with configured credentials |
| 3 | Wait Element | wait for the order table to load (timeout + retry) |
| 4 | Loop rows | iterate over the order table |
| 5 | Get Text (multiple) | extract order id, customer, date, product, amount, status |
| 6 | Write Excel / Append CSV | append rows to `data/raw/orders_raw.csv` |
| 7 | Try-Except | on failure, log and trigger human intervention |
| 8 | Run Python Script | invoke `python run_demo.py` to continue the pipeline |

## How to build it (in the Yingdao client)

1. Create a new project named `order_crawl`.
2. Build the flow per the table above; keep the CSV output schema identical
   to `mock_ingest.py`'s `OUTPUT_COLUMNS`:
   `order_id, customer, ordered_at, product, amount, status`.
3. Store credentials in Yingdao's global variables (never hard-code them).
4. Export the project (`.rdx`) into this folder and commit it.
5. Update `docs/user_guide.md` section 6 with any differences.

## Alternative: skip Yingdao entirely

If the order backend exposes a REST API (WooCommerce, Shopify, custom ERP),
set `mode = api` in `config.ini` and use `ApiOrderIngestor` - no Yingdao
project is needed at all.
