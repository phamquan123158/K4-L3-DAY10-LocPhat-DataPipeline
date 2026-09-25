from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a benchmark dataset of 10 questions across the main paper metadata dimensions."""
    if df.empty:
        raise ValueError("Cannot build a test set from an empty dataframe.")

    sample = df.head(10).copy().reset_index(drop=True)
    output = []
    for idx, row in enumerate(sample.to_dict(orient="records"), start=1):
        title = str(row.get("title", "")).strip()
        paper_id = str(row.get("paper_id", "")).strip()
        summary = str(row.get("summary", "")).strip()
        authors = str(row.get("authors_joined", row.get("authors", ""))).strip()
        published = str(row.get("published", "")).strip()
        categories = str(row.get("categories_joined", row.get("categories", ""))).strip()

        if idx % 4 == 1:
            question_type = "summary"
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = summary
        elif idx % 4 == 2:
            question_type = "authors"
            question = f"Who authored the paper '{title}'?"
            ground_truth = authors
        elif idx % 4 == 3:
            question_type = "date"
            question = f"When was the paper '{title}' published?"
            ground_truth = published
        else:
            question_type = "categories"
            question = f"What categories apply to the paper '{title}'?"
            ground_truth = categories

        output.append(
            {
                "id": f"eval_{idx:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
