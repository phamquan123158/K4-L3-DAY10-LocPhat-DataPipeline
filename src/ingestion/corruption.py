from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import now_utc, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 dang data corruption theo yeu cau cua bai lab (Checkpoint 4).

    1. Drop latest records: Bỏ rơi các bài báo mới nhất (mô phỏng mất dữ liệu tươi).
    2. Blank summary: Xóa trắng phần tóm tắt ở một số dòng (mô phỏng thiếu thông tin).
    3. Inject text noise: Chèn các chuỗi ký tự rác vô nghĩa vào text_for_embedding.
    4. Truncate title: Cắt ngắn tiêu đề bài báo xuống dưới 10 ký tự.
    5. Stale date: Đổi ngày xuất bản về 5 năm trước (mô phỏng dữ liệu bị mốc meo).
    6. Duplicate rows: Nhân đôi một số dòng để tạo bản ghi trùng lặp.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vào output_log_path.
    """
    df_corrupted = df.copy().reset_index(drop=True)
    initial_rows = len(df_corrupted)
    log_scenarios: list[dict[str, Any]] = []

    # -------------------------------------------------------------
    # 1. Drop latest records: Bỏ rơi 4 bài báo mới nhất (~20% dữ liệu)
    # -------------------------------------------------------------
    num_drop = 4
    dropped_df = df_corrupted.iloc[:num_drop].copy()
    df_corrupted = df_corrupted.iloc[num_drop:].copy().reset_index(drop=True)
    log_scenarios.append(
        {
            "scenario": "drop_latest_records",
            "description": "Bỏ rơi các bài báo mới nhất (mô phỏng mất dữ liệu tươi)",
            "affected_count": num_drop,
            "paper_ids": dropped_df["paper_id"].tolist(),
        }
    )

    # -------------------------------------------------------------
    # 2. Blank summary: Xóa trắng phần tóm tắt ở 3 dòng
    # -------------------------------------------------------------
    blank_indices = [0, 1, 2]
    blank_paper_ids: list[str] = []
    for idx in blank_indices:
        if idx < len(df_corrupted):
            df_corrupted.at[idx, "summary"] = ""
            if "summary_chars" in df_corrupted.columns:
                df_corrupted.at[idx, "summary_chars"] = 0
            blank_paper_ids.append(str(df_corrupted.at[idx, "paper_id"]))

    log_scenarios.append(
        {
            "scenario": "blank_summary",
            "description": "Xóa trắng phần tóm tắt ở một số dòng (mô phỏng thiếu thông tin)",
            "affected_count": len(blank_paper_ids),
            "paper_ids": blank_paper_ids,
        }
    )

    # -------------------------------------------------------------
    # 3. Inject text noise: Chèn các chuỗi ký tự rác vô nghĩa
    # -------------------------------------------------------------
    noise_indices = [3, 4, 5]
    noise_paper_ids: list[str] = []
    noise_payload = "\n[NOISE_INJECTION: #$@%&* INVALID_PAYLOAD_GARBAGE_TOKENS_CORRUPTED_TEXT #$@%&*]"
    for idx in noise_indices:
        if idx < len(df_corrupted):
            noise_paper_ids.append(str(df_corrupted.at[idx, "paper_id"]))

    log_scenarios.append(
        {
            "scenario": "inject_text_noise",
            "description": "Chèn các chuỗi ký tự rác vô nghĩa vào text_for_embedding",
            "affected_count": len(noise_paper_ids),
            "paper_ids": noise_paper_ids,
        }
    )

    # -------------------------------------------------------------
    # 4. Truncate title: Cắt ngắn tiêu đề bài báo xuống dưới 10 ký tự
    # -------------------------------------------------------------
    truncate_indices = [6, 7, 8, 9]
    truncated_paper_ids: list[str] = []
    for idx in truncate_indices:
        if idx < len(df_corrupted):
            orig_title = str(df_corrupted.at[idx, "title"])
            df_corrupted.at[idx, "title"] = orig_title[:8].strip()
            truncated_paper_ids.append(str(df_corrupted.at[idx, "paper_id"]))

    log_scenarios.append(
        {
            "scenario": "truncate_title",
            "description": "Cắt ngắn tiêu đề bài báo xuống dưới 10 ký tự",
            "affected_count": len(truncated_paper_ids),
            "paper_ids": truncated_paper_ids,
        }
    )

    # -------------------------------------------------------------
    # 5. Stale date: Đổi ngày xuất bản về 5 năm trước (lùi ~1825 ngày)
    #    Áp dụng cho 10 dòng để tỷ lệ bài báo quá hạn (>180 ngày) > 25% (vi phạm SLA)
    # -------------------------------------------------------------
    stale_indices = list(range(5, 15))
    stale_paper_ids: list[str] = []
    for idx in stale_indices:
        if idx < len(df_corrupted):
            orig_pub = str(df_corrupted.at[idx, "published"])[:10]
            try:
                year = int(orig_pub[:4]) - 5
                stale_pub = f"{year:04d}{orig_pub[4:]}"
            except Exception:
                stale_pub = "2021-01-01"

            df_corrupted.at[idx, "published"] = stale_pub
            if "age_days" in df_corrupted.columns:
                try:
                    df_corrupted.at[idx, "age_days"] = int(df_corrupted.at[idx, "age_days"]) + 1825
                except Exception:
                    df_corrupted.at[idx, "age_days"] = 1850
            stale_paper_ids.append(str(df_corrupted.at[idx, "paper_id"]))

    log_scenarios.append(
        {
            "scenario": "stale_date",
            "description": "Đổi ngày xuất bản về 5 năm trước (mô phỏng dữ liệu bị mốc meo)",
            "affected_count": len(stale_paper_ids),
            "paper_ids": stale_paper_ids,
        }
    )

    # -------------------------------------------------------------
    # 6. Duplicate rows: Nhân đôi 4 dòng để tạo bản ghi trùng lặp
    #    (Khôi phục tổng số dòng về 20 + 4 = 24 dòng)
    # -------------------------------------------------------------
    duplicated_df = df_corrupted.iloc[:num_drop].copy()
    df_corrupted = pd.concat([df_corrupted, duplicated_df], ignore_index=True)
    log_scenarios.append(
        {
            "scenario": "duplicate_rows",
            "description": "Nhân đôi một số dòng để tạo bản ghi trùng lặp",
            "affected_count": len(duplicated_df),
            "paper_ids": duplicated_df["paper_id"].tolist(),
        }
    )

    # -------------------------------------------------------------
    # 7. Rebuild text_for_embedding cho toàn bộ các dòng
    # -------------------------------------------------------------
    for idx in range(len(df_corrupted)):
        title = df_corrupted.at[idx, "title"]
        authors = df_corrupted.at[idx, "authors_joined"]
        published = df_corrupted.at[idx, "published"]
        categories = df_corrupted.at[idx, "categories_joined"]
        summary = df_corrupted.at[idx, "summary"]

        base_text = (
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Published: {published}\n"
            f"Categories: {categories}\n"
            f"Summary: {summary}"
        )
        if idx in noise_indices:
            base_text += noise_payload

        df_corrupted.at[idx, "text_for_embedding"] = base_text

    # -------------------------------------------------------------
    # 8. Ghi corruption log vào output_log_path
    # -------------------------------------------------------------
    log_payload: dict[str, Any] = {
        "timestamp": now_utc().isoformat(),
        "initial_rows": initial_rows,
        "final_rows": len(df_corrupted),
        "total_scenarios": len(log_scenarios),
        "scenarios": log_scenarios,
    }
    write_json(Path(output_log_path), log_payload)

    return df_corrupted
