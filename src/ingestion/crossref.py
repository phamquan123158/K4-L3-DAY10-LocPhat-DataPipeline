from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

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


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = item.get("DOI", "").strip()
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
    """Goi source API, luu raw response, parse thanh records. Co che fallback offline."""
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
