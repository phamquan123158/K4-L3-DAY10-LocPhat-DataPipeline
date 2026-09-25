from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


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
        date_parts = value.get("date-parts") or value.get("dateParts") or []
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
    items = payload.get("message", {}).get("items", []) if isinstance(payload, dict) else []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = _clean_text(item.get("DOI"))
        if not paper_id:
            continue

        title_candidates = item.get("title") or []
        title = normalize_whitespace(title_candidates[0]) if isinstance(title_candidates, list) and title_candidates else normalize_whitespace(str(title_candidates or ""))
        if not title:
            continue

        raw_abstract = item.get("abstract") or ""
        summary = normalize_whitespace(re.sub(r"<[^>]+>", " ", raw_abstract))

        authors: list[str] = []
        for author in item.get("author") or []:
            if isinstance(author, dict):
                given = _clean_text(author.get("given"))
                family = _clean_text(author.get("family"))
                name = f"{given} {family}".strip() if (given or family) else _clean_text(author.get("name"))
                if name:
                    authors.append(name)
            elif isinstance(author, str):
                author_name = _clean_text(author)
                if author_name:
                    authors.append(author_name)

        categories = [
            _clean_text(category) for category in (item.get("subject") or []) if _clean_text(category)
        ]
        primary_category = categories[0] if categories else "General"

        published = _parse_date(item.get("published")) or str(item.get("created", {}).get("date-time", ""))[:10] or "2026-01-01"
        updated = _parse_date(item.get("updated")) or published
        abs_url = _clean_text(item.get("URL")) or f"https://doi.org/{paper_id}"
        pdf_url = abs_url
        comment = f"Crossref record {paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
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
    """Fetch raw Crossref works, persist the raw payload, and return parsed PaperRecord objects."""
    payload: dict | None = None

    if settings.refresh_source:
        try:
            params = {
                "query.title": settings.source_query,
                "filter": settings.source_filter,
                "rows": settings.max_results,
                "select": "DOI,title,abstract,author,subject,published,created,URL",
            }
            query_string = urllib.parse.urlencode(params)
            url = f"https://api.crossref.org/works?{query_string}"
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
                    write_json(settings.paths.raw_api_response, payload)
        except Exception:
            payload = None

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise FileNotFoundError(f"Raw API response snapshot not found at {settings.paths.raw_api_response}")

    records = parse_crossref_payload(payload)
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a saved JSON snapshot and map it back to PaperRecord objects."""
    payload = read_json(path)

    if isinstance(payload, dict):
        if "message" in payload:
            return parse_crossref_payload(payload)
        if all(isinstance(item, dict) and "paper_id" in item for item in payload.get("items", [])):
            return [PaperRecord(**item) for item in payload["items"]]
        return []

    if isinstance(payload, list):
        return [PaperRecord(**item) for item in payload]

    return []
