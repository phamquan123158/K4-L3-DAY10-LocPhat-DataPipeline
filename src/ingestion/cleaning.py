from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Sequence

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_clean_dataframe(records: Sequence[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw records into a dataframe ready for embedding and evaluation."""
    if run_date.tzinfo is not None:
        run_date_dt = run_date.astimezone(timezone.utc).date()
    else:
        run_date_dt = run_date.date()

    rows: list[dict] = []
    for record in records:
        paper_id = normalize_whitespace(str(record.paper_id or ""))
        title = _normalize_text(record.title)
        summary = _normalize_text(record.summary)
        authors = [_normalize_text(author) for author in record.authors if _normalize_text(author)]
        categories = [_normalize_text(category) for category in record.categories if _normalize_text(category)]
        primary_category = _normalize_text(record.primary_category) or (categories[0] if categories else "General")
        published = str(record.published or "")[:10]
        updated = str(record.updated or published)[:10]
        abs_url = _normalize_text(record.abs_url)
        pdf_url = _normalize_text(record.pdf_url)
        comment = _normalize_text(record.comment)

        if not paper_id or not title:
            continue

        authors_joined = "; ".join(authors) if authors else "Unknown author"
        categories_joined = ", ".join(categories) if categories else "Uncategorized"
        summary_chars = len(summary)

        try:
            pub_date = datetime.strptime(published, "%Y-%m-%d").date()
            age_days = (run_date_dt - pub_date).days
        except Exception:
            age_days = 0

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published or 'Unknown'}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary or 'No summary available'}"
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="paper_id").copy()
    df = df[df["paper_id"].notna() & df["title"].notna()]
    df = df[df["summary"].astype(str).str.len().fillna(0).ge(30)] if "summary" in df.columns else df
    df = df.sort_values(["published", "paper_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    return df
