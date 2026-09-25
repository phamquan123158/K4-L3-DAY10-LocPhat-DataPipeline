from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
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

    if "age_days" not in df.columns and "published" in df.columns and total_rows > 0:
        df = df.copy()
        df["age_days"] = (
            pd.Timestamp.now(tz="UTC").date()
            - pd.to_datetime(df["published"], errors="coerce")
            .dt.date.map(lambda d: pd.Timestamp(d).tz_localize("UTC").date())
        ).apply(lambda d: (pd.Timestamp.now(tz="UTC").date() - d).days if pd.notna(d) else None)

    if "age_days" in df.columns and total_rows > 0:
        stale_rows = int((df["age_days"].fillna(-1) > threshold).sum())
        stale_ratio = float(stale_rows / total_rows)
    else:
        stale_rows = 0
        stale_ratio = 0.0

    # Freshness Check:
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


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chay tram kiem soat chat luong du lieu voi Great Expectations 1.x.

    Cau hinh ephemeral context va 4 Expectations:
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
