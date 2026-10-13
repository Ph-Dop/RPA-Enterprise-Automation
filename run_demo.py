"""End-to-end demo pipeline for RPA Enterprise Automation.

Runs the full flow with a single command (no Yingdao RPA required):

    python run_demo.py                       # mock channel, full pipeline
    python run_demo.py --mode api            # real REST API channel
    python run_demo.py --fail-once           # simulate one failure to demo alerting

Pipeline: ingest -> persist (SQLite) -> clean (+quality report) -> report -> alert check
"""
from __future__ import annotations

import argparse
import logging
import sys
import traceback

from rpa_platform.alerting.mail_alert import FailureTracker, MailAlert
from rpa_platform.cleaning.cleaner import DataCleaner
from rpa_platform.config import PROJECT_ROOT, Settings
from rpa_platform.ingest.api_ingest import ApiOrderIngestor
from rpa_platform.ingest.mock_ingest import MockOrderIngestor
from rpa_platform.logger import setup_logger
from rpa_platform.reporting.report_gen import ReportGenerator, compute_kpis
from rpa_platform.storage import OrderStore

# Child logger of "rpa": inherits the handlers configured by setup_logger().
logger = logging.getLogger("rpa.pipeline")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the RPA automation pipeline end to end.")
    parser.add_argument(
        "--mode", choices=["mock", "api"], default=None, help="Override ingest channel"
    )
    parser.add_argument(
        "--fail-once", action="store_true", help="Simulate a run failure to demo the alerting path"
    )
    return parser


def run_pipeline(args: argparse.Namespace) -> int:
    setup_logger()
    settings = Settings()
    logger.info(
        "=== Pipeline start (mode=%s, company=%s) ===",
        args.mode or settings.ingest_mode,
        settings.company_name,
    )

    store = OrderStore(settings.database_path)

    if args.fail_once:
        _simulate_failure(settings, store)
        return 1

    run_id = store.start_run("pipeline")
    try:
        # 1) ingest ---------------------------------------------------------
        mode = args.mode or settings.ingest_mode
        ingestor = ApiOrderIngestor(settings) if mode == "api" else MockOrderIngestor(settings)
        raw = ingestor.ingest()
        logger.info("Ingested %d raw order rows", len(raw))

        # 2) persist --------------------------------------------------------
        written = store.save_orders(raw, source=mode)
        logger.info("Persisted %d rows to SQLite (%s)", written, settings.database_path)

        # 3) clean ----------------------------------------------------------
        cleaner = DataCleaner(settings)
        cleaned, quality = cleaner.clean(raw)
        logger.info(
            "Quality: raw=%d valid=%d removed=%d %s",
            quality["raw_count"],
            quality["cleaned_count"],
            quality["removed_total"],
            quality["issue_counts"],
        )

        # 4) report ---------------------------------------------------------
        generator = ReportGenerator(settings)
        kpis = compute_kpis(cleaned, settings.report_currency_symbol)
        report_path = generator.export(cleaned, quality, kpis)
        logger.info("Report: %s", report_path)

        # 5) alert check ----------------------------------------------------
        tracker = FailureTracker()
        tracker.record_success()

        store.finish_run(run_id, "success", message=f"report={report_path.name}")
        _print_summary(raw, cleaned, quality, kpis, report_path)
        return 0
    except Exception as exc:  # noqa: BLE001 - deliberate top-level guard
        logger.error("Pipeline failed: %s\n%s", exc, traceback.format_exc())
        store.finish_run(run_id, "failed", error=str(exc))
        _handle_failure(settings, store)
        return 1


def _handle_failure(settings: Settings, store: OrderStore) -> None:
    tracker = FailureTracker()
    count = tracker.record_failure()
    threshold = settings.alert_after_consecutive_failures
    logger.warning("Consecutive failures: %d/%d", count, threshold)
    if tracker.should_alert(threshold):
        body = (
            f"RPA pipeline failed {count} consecutive times.\n"
            f"Company: {settings.company_name}\n"
            f"Last run statuses: {store.recent_run_statuses()}\n"
            "Please check the logs under data/logs/rpa.log"
        )
        MailAlert(settings).send(f"[RPA Alert] Pipeline failed x{count}", body)


def _simulate_failure(settings: Settings, store: OrderStore) -> None:
    setup_logger()
    run_id = store.start_run("pipeline")
    error = "Simulated failure (--fail-once): connection to order source timed out"
    logger.error(error)
    store.finish_run(run_id, "failed", error=error)
    _handle_failure(settings, store)


def _print_summary(raw, cleaned, quality, kpis, report_path) -> None:  # noqa: ANN001
    print("\n" + "=" * 60)
    print("RPA PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Raw orders ingested : {quality['raw_count']}")
    print(f"Valid after cleaning: {quality['cleaned_count']}  (removed {quality['removed_total']})")
    print(f"Issues             : {quality['issue_counts']}")
    print(f"Total revenue      : {kpis['currency']} {kpis['total_revenue']:,.2f}")
    print(f"Order count        : {kpis['order_count']:,}")
    print(f"Avg order value    : {kpis['currency']} {kpis['avg_order_value']:,.2f}")
    print(f"Report             : {report_path}")
    print("=" * 60)


def main() -> int:
    args = build_parser().parse_args()
    return run_pipeline(args)


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.exit(main())
