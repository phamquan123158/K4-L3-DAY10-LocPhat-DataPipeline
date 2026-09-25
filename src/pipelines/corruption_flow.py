from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    print("=== [PHASE 2] CHAY CORRUPTION -> REPAIR -> COMPARISON FLOW ===")

    # 1. Load baseline metrics va clean dataset
    if not settings.paths.clean_json.exists() or not settings.paths.baseline_metrics.exists():
        raise FileNotFoundError("Chua tim thay Baseline artifacts. Hay chay 'python script/run_phase1.py' truoc!")

    df_clean = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"-> 1. Da nap {len(df_clean)} dong du lieu sach va baseline metrics.")

    # 2. Tao corrupted dataframe & luu artifacts
    print("-> 2. Dang tiem 6 kich ban data corruption...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))
    print(f"   -> Da xuat du lieu loi ({len(df_corrupted)} dong) va ghi log: {settings.paths.corruption_log}")

    # 3. Rebuild index va evaluate tren corrupted data
    print("-> 3. Rebuilding Chroma index cho du lieu bi corrupted...")
    corrupted_index = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)
    print("   -> Dang danh gia suy giam hieu nang cua RAG Agent tren du lieu ban...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    c_hit = corrupted_bundle.summary.get("retrieval_hit_rate", 0.0) * 100
    c_f1 = corrupted_bundle.summary.get("mean_token_f1", 0.0) * 100
    print(f"   -> [Corrupted] Hit Rate: {c_hit:.1f}% | Token F1: {c_f1:.1f}%")

    # 4. Run quality checks & freshness tren corrupted data
    print("-> 4. Chay Data Observability tren du lieu corrupted...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(df_corrupted, settings)
    print(f"   -> Quality Gate Status: {corrupted_quality.get('success')} (Expectation fail du kien)")
    print(f"   -> Freshness Status: {corrupted_freshness.get('is_fresh')} (SLA violation du kien)")

    # 5. Idempotent Repair tu raw snapshot ban dau
    print("-> 5. Kich hoat co che Idempotent Repair tu ban thô data/raw/...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, now_utc())
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))
    print(f"   -> Da phuc hoi {len(df_repaired)} ban ghi sach tu raw snapshot.")

    # 6. Evaluate repaired dataset
    print("-> 6. Rebuilding Chroma index va danh gia tap du lieu sau phuc hoi...")
    repaired_index = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(df_repaired, settings)
    r_hit = repaired_bundle.summary.get("retrieval_hit_rate", 0.0) * 100
    r_f1 = repaired_bundle.summary.get("mean_token_f1", 0.0) * 100
    print(f"   -> [Repaired] Hit Rate: {r_hit:.1f}% | Token F1: {r_f1:.1f}%")

    # 7. Generate comparison report 3 trang thai
    print("-> 7. Dang sinh bao cao Markdown doi chieu 3 trang thai...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"=== [PHASE 2] HOAN TAT THANH CONG! Bao cao: {settings.paths.comparison_report} ===")
