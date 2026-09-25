from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import write_json


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str | None = None) -> dict[str, Any]:
    """Summarize stale-record freshness and optionally write a JSON report."""
    if "age_days" not in df.columns:
        if "published" in df.columns:
            published = pd.to_datetime(df["published"], errors="coerce")
            today = pd.Timestamp.now(tz="UTC").date()
            age_days = []
            for value in published:
                if pd.isna(value):
                    age_days.append(None)
                else:
                    age_days.append((today - value.date()).days)
            df = df.copy()
            df["age_days"] = age_days
        else:
            df = df.copy()
            df["age_days"] = pd.NA

    published = pd.to_datetime(df["published"], errors="coerce")
    latest_published = published.max()
    oldest_published = published.min()
    stale_rows = int((df["age_days"].fillna(-1) > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 0.0

    payload: dict[str, Any] = {
        "latest_published": latest_published.strftime("%Y-%m-%d") if pd.notna(latest_published) else None,
        "oldest_published": oldest_published.strftime("%Y-%m-%d") if pd.notna(oldest_published) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "is_fresh": stale_ratio <= 0.25,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    if report_path is not None:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return payload


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run GX 1.x expectations and freshness checks on a dataframe."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
    data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name=f"papers_{report_name}_suite"))
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    validation_result = batch.validate(suite)
    gx_success = bool(validation_result.success)

    freshness_report_path = settings.paths.freshness_report if report_name == "baseline" else None
    freshness_data = build_freshness_report(df, settings, freshness_report_path)
    overall_success = bool(gx_success and freshness_data["is_fresh"])

    quality_report: dict[str, Any] = {
        "report_name": report_name,
        "success": overall_success,
        "gx_success": gx_success,
        "is_fresh": freshness_data["is_fresh"],
        "total_rows": len(df),
        "freshness": freshness_data,
        "validation_results": validation_result.to_json_dict(),
    }

    if report_name == "baseline":
        report_file = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        report_file = settings.paths.corrupted_quality_report
    else:
        report_file = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    write_json(report_file, quality_report)
    return quality_report
