from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    print("=== [PHASE 1] CHAY BASELINE PIPELINE ===")

    # 1. Load hoac fetch raw records
    if settings.paths.raw_records_json.exists():
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        records = fetch_source_records(settings)
    print(f"-> 1. Da nap {len(records)} raw records.")

    # 2. Clean data
    df = build_clean_dataframe(records, now_utc())
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    print(f"-> 2. Da lam sach va xuat {len(df)} dong du lieu vao {settings.paths.clean_csv}.")

    # 3. Build Chroma Index cho Baseline
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    print(f"-> 3. Da nap Vector Store ChromaDB collection: {settings.baseline_collection_name}.")

    # 4. Build Test Set (10 cau hoi)
    test_set = build_test_set(df, settings.paths.eval_testset)
    print(f"-> 4. Da tao Test Set gom {len(test_set)} cau hoi vao {settings.paths.eval_testset}.")

    # 5. Evaluate Pipeline
    print("-> 5. Dang danh gia chat luong RAG (Hit rate, Token F1, LLM Judge)...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    hit_rate = eval_bundle.summary.get("retrieval_hit_rate", 0.0) * 100
    token_f1 = eval_bundle.summary.get("mean_token_f1", 0.0) * 100
    print(f"   -> Retrieval Hit Rate: {hit_rate:.1f}%")
    print(f"   -> Mean Token F1: {token_f1:.1f}%")

    # 6. Quality Checks & Freshness Report
    print("-> 6. Dang chay Great Expectations 1.x & Freshness SLA...")
    quality = run_data_quality_checks(df, settings, report_name="baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f"   -> Quality Gate Status: {quality.get('success')}, Freshness: {freshness.get('is_fresh')}")

    # 7. Generate Phase 1 Report
    print("-> 7. Dang sinh bao cao tong hop Markdown...")
    source_summary = {
        "provider": settings.source_api,
        "total_records": len(df),
        "source_query": settings.source_query,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"=== [PHASE 1] HOAN TAT THANH CONG! Bao cao: {settings.paths.baseline_report} ===")
