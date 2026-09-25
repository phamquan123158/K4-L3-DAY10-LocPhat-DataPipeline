from __future__ import annotations

<<<<<<< HEAD
import re
from datetime import datetime
=======
from datetime import datetime, timezone
from typing import Sequence
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


<<<<<<< HEAD
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
=======
def build_clean_dataframe(records: Sequence[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days = (run_date - published).days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates theo paper_id va filter row xau.
    6. Sort dataframe va return.
    """
    if run_date.tzinfo is not None:
        run_date_dt = run_date.astimezone(timezone.utc).date()
    else:
        run_date_dt = run_date.date()

    rows: list[dict] = []
    for r in records:
        paper_id = normalize_whitespace(str(r.paper_id or ""))
        title = normalize_whitespace(str(r.title or ""))
        summary = normalize_whitespace(str(r.summary or ""))
        authors = [normalize_whitespace(str(a)) for a in r.authors if normalize_whitespace(str(a))]
        categories = [normalize_whitespace(str(c)) for c in r.categories if normalize_whitespace(str(c))]
        primary_category = str(r.primary_category or (categories[0] if categories else "General"))
        published = str(r.published or "")[:10]
        updated = str(r.updated or published)[:10]
        abs_url = str(r.abs_url or "")
        pdf_url = str(r.pdf_url or "")
        comment = str(r.comment or "")

        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        summary_chars = len(summary)

        try:
            pub_date = datetime.strptime(published, "%Y-%m-%d").date()
            age_days = (run_date_dt - pub_date).days
        except Exception:
            age_days = 0

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
        )

        rows.append(
            {
<<<<<<< HEAD
                "paper_id": record.paper_id,
=======
                "paper_id": paper_id,
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
<<<<<<< HEAD
                "published": record.published,
                "updated": record.updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
=======
                "published": published,
                "updated": updated,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
                "age_days": age_days,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
                "text_for_embedding": text_for_embedding,
            }
        )

<<<<<<< HEAD
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset="paper_id").copy()
    df = df[df["paper_id"].notna() & df["title"].notna()]
    df = df[df["summary"].str.len().fillna(0).ge(30)] if "summary" in df else df
    df = df.sort_values(["published", "paper_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
=======
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
                "age_days",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "text_for_embedding",
            ]
        )

    df = pd.DataFrame(rows)

    # 4. Khử trùng lặp bản ghi theo khóa duy nhất paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Lọc bỏ các dòng không hợp lệ
    df = df.dropna(subset=["paper_id", "title", "text_for_embedding"])
    df = df[df["paper_id"].astype(str).str.strip() != ""]

    # Sắp xếp theo ngày xuất bản mới nhất trước
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
    return df
