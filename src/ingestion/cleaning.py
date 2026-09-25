from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw records into a cleaned dataframe ready for embedding and evaluation."""
    rows = []
    for record in records:
        title = _normalize_text(record.title)
        summary = _normalize_text(record.summary)
        authors = [_normalize_text(author) for author in record.authors if _normalize_text(author)]
        categories = [_normalize_text(category) for category in record.categories if _normalize_text(category)]
        primary_category = _normalize_text(record.primary_category) or (categories[0] if categories else "")
        published = pd.to_datetime(record.published, errors="coerce")
        updated = pd.to_datetime(record.updated or record.published, errors="coerce")

        if not record.paper_id or not title:
            continue

        age_days = (run_date.date() - published.date()).days if pd.notna(published) else None
        authors_joined = "; ".join(authors) if authors else "Unknown author"
        categories_joined = ", ".join(categories) if categories else "Uncategorized"
        summary_chars = len(summary)
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {record.published or 'Unknown'}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary or 'No summary available'}"
        )

        rows.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": record.published,
                "updated": record.updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset="paper_id").copy()
    df = df[df["paper_id"].notna() & df["title"].notna()]
    df = df[df["summary"].str.len().fillna(0).ge(30)] if "summary" in df else df
    df = df.sort_values(["published", "paper_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    return df
