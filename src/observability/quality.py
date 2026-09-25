from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize stale-record freshness and write the report JSON."""
    if "age_days" not in df.columns:
        if "published" in df.columns:
            df = df.copy()
            df["age_days"] = (pd.Timestamp.now(tz="UTC").date() - pd.to_datetime(df["published"], errors="coerce").dt.date.map(lambda d: pd.Timestamp(d).tz_localize("UTC").date())).apply(lambda d: (pd.Timestamp.now(tz="UTC").date() - d).days if pd.notna(d) else None)
        else:
            df = df.copy()
            df["age_days"] = pd.NA

    published = pd.to_datetime(df["published"], errors="coerce")
    latest_published = published.max()
    oldest_published = published.min()
    stale_rows = int((df["age_days"].fillna(-1) > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 0.0
    payload = {
        "latest_published": latest_published.strftime("%Y-%m-%d") if pd.notna(latest_published) else None,
        "oldest_published": oldest_published.strftime("%Y-%m-%d") if pd.notna(oldest_published) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "is_fresh": stale_ratio <= 0.25,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run GX 1.x expectations and freshness checks on a dataframe."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    validator = batch.get_validator()

    row_count_expectation = validator.expect_table_row_count_to_be_between(min_value=5, max_value=5000)
    null_paper_id = validator.expect_column_values_to_not_be_null(column="paper_id")
    null_title = validator.expect_column_values_to_not_be_null(column="title")
    null_text = validator.expect_column_values_to_not_be_null(column="text_for_embedding")
    unique_paper_id = validator.expect_column_values_to_be_unique(column="paper_id")
    summary_length = validator.expect_column_value_lengths_to_be_between(column="summary", min_value=30)

    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    if "age_days" not in df.columns:
        df = df.copy()
        df["age_days"] = (pd.Timestamp.now(tz="UTC").date() - pd.to_datetime(df["published"], errors="coerce").dt.date.map(lambda d: pd.Timestamp(d).tz_localize("UTC").date())).apply(lambda d: (pd.Timestamp.now(tz="UTC").date() - d).days if pd.notna(d) else None)

    stale_ratio = ((df["age_days"].fillna(0) > settings.freshness_threshold_days).mean()) if "age_days" in df.columns else 0.0
    quality_success = (
        row_count_expectation.success
        and null_paper_id.success
        and null_title.success
        and null_text.success
        and unique_paper_id.success
        and summary_length.success
        and stale_ratio <= 0.25
    )

    report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "report_name": report_name,
        "success": bool(quality_success),
        "expectations": {
            "row_count": row_count_expectation.to_json_dict(),
            "paper_id_not_null": null_paper_id.to_json_dict(),
            "title_not_null": null_title.to_json_dict(),
            "text_for_embedding_not_null": null_text.to_json_dict(),
            "paper_id_unique": unique_paper_id.to_json_dict(),
            "summary_min_length": summary_length.to_json_dict(),
        },
        "freshness": freshness,
        "stale_ratio": stale_ratio,
        "is_fresh": stale_ratio <= 0.25,
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_payload
