from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from time import sleep

import requests

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(value: object) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, dict):
        date_parts = value.get("date-parts") or value.get("dateParts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
            parts = [int(part) for part in date_parts[0][:3] if part is not None]
            if len(parts) >= 3:
                return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            if len(parts) >= 2:
                return f"{parts[0]:04d}-{parts[1]:02d}-01"
            if len(parts) == 1:
                return f"{parts[0]:04d}-01-01"
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into a list of normalized PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = _clean_text(item.get("DOI"))
        title = _clean_text((item.get("title") or [""])[0])
        if not doi or not title:
            continue

        abstract = item.get("abstract") or ""
        summary = _clean_text(abstract)

        authors = []
        for author in item.get("author") or []:
            given = _clean_text(author.get("given"))
            family = _clean_text(author.get("family"))
            name = " ".join(part for part in [given, family] if part)
            if name:
                authors.append(name)

        categories = [
            _clean_text(category)
            for category in (item.get("subject") or [])
            if _clean_text(category)
        ]
        primary_category = categories[0] if categories else ""
        published = _parse_date(item.get("published"))
        updated = _parse_date(item.get("updated") or item.get("created")) or published
        abs_url = _clean_text(item.get("URL")) or f"https://doi.org/{doi}"
        pdf_url = abs_url
        comment = f"Crossref record {doi}"

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call the Crossref API, save the raw payload, and parse it into PaperRecord objects."""
    url = "https://api.crossref.org/works"
    params = {
        "query.title": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,created,URL",
    }

    last_error: Exception | None = None
    for _ in range(4):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code in {200, 201}:
                payload = response.json()
                settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
                settings.paths.raw_api_response.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                records = parse_crossref_payload(payload)
                settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
                settings.paths.raw_records_json.write_text(
                    json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return records
            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = RuntimeError(f"Crossref responded with HTTP {response.status_code}.")
                sleep(2)
                continue
            raise RuntimeError(f"Crossref request failed with HTTP {response.status_code}: {response.text[:200]}")
        except requests.RequestException as exc:  # pragma: no cover - network path fallback
            last_error = exc
            sleep(2)

    fallback_path = settings.paths.raw_api_response
    if fallback_path.exists():
        payload = json.loads(fallback_path.read_text(encoding="utf-8"))
        records = parse_crossref_payload(payload)
        settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
        settings.paths.raw_records_json.write_text(
            json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return records

    if last_error is not None:
        raise RuntimeError(f"Failed to fetch Crossref records: {last_error}")
    raise RuntimeError("Failed to fetch Crossref records.")


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a JSON snapshot and map it back to PaperRecord objects."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("message", {}).get("items", []) if isinstance(raw, dict) else raw

    if isinstance(items, dict):
        items = items.get("items", [])

    if not items:
        return []

    if all(isinstance(item, PaperRecord) for item in items):
        return list(items)

    if all(isinstance(item, dict) and "paper_id" in item for item in items):
        return [
            PaperRecord(
                paper_id=_clean_text(item.get("paper_id")),
                title=_clean_text(item.get("title")),
                summary=_clean_text(item.get("summary")),
                authors=[_clean_text(author) for author in (item.get("authors") or []) if _clean_text(author)],
                categories=[_clean_text(category) for category in (item.get("categories") or []) if _clean_text(category)],
                primary_category=_clean_text(item.get("primary_category")),
                published=_clean_text(item.get("published")),
                updated=_clean_text(item.get("updated")),
                abs_url=_clean_text(item.get("abs_url")),
                pdf_url=_clean_text(item.get("pdf_url")),
                comment=_clean_text(item.get("comment")),
            )
            for item in items
            if item.get("paper_id") and item.get("title")
        ]

    return parse_crossref_payload(raw if isinstance(raw, dict) else {"message": {"items": items}})
