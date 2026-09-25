from __future__ import annotations

<<<<<<< HEAD
import json
=======
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
from pathlib import Path
from typing import Any

import great_expectations as gx
<<<<<<< HEAD
=======
import great_expectations.expectations as gxe
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
import pandas as pd

from core.config import Settings
from core.utils import write_json


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str | None = None) -> dict[str, Any]:
    """Tong hop freshness report va kiem tra SLA do tuoi.

    1. Tim latest va oldest published date.
    2. Dem so dong stale (age_days > freshness_threshold_days).
    3. Tinh ti le stale. Canh bao neu ti le stale > 25% (is_fresh = False).
    4. Ghi JSON report neu co report_path.
    """
    total_rows = len(df)
    threshold = settings.freshness_threshold_days

    if "age_days" in df.columns and total_rows > 0:
        stale_rows = int((df["age_days"] > threshold).sum())
        stale_ratio = float(stale_rows / total_rows)
    else:
        stale_rows = 0
        stale_ratio = 0.0

    # Kiem tra do tuoi moi (Freshness Check):
    # Neu ti le bai bao cu (age_days > 180 ngay) vuot qua 25% thi canh bao du lieu bi moc
    is_fresh = bool(stale_ratio <= 0.25)

    latest_published = str(df["published"].max()) if not df.empty and "published" in df.columns else ""
    oldest_published = str(df["published"].min()) if not df.empty and "published" in df.columns else ""

    payload: dict[str, Any] = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 4),
        "threshold_days": threshold,
        "max_stale_ratio_allowed": 0.25,
        "is_fresh": is_fresh,
    }

    if report_path:
        write_json(Path(report_path), payload)

    return payload


<<<<<<< HEAD
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
=======
def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chay tram kiem soat chat luong du lieu voi Great Expectations 1.x.

    Cấu hình ephemeral context và 4 Expectations:
    1. ExpectTableRowCountToBeBetween: 5 den 5000.
    2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding.
    3. ExpectColumnValuesToBeUnique: paper_id.
    4. ExpectColumnValueLengthsToBeBetween: summary toi thieu 30 ky tu.
    5. Freshness Check: ti le bai bao cu (age_days > 180) <= 25%.
    """
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
    data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name=f"papers_{report_name}_suite"))

    # 4 Expectations bat buoc
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    validation_result = batch.validate(suite)
    gx_success = bool(validation_result.success)

    # Freshness Check
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
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
