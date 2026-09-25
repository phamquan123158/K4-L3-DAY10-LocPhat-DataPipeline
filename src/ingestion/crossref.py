from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


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

        titles = item.get("title", [])
        title_str = titles[0] if isinstance(titles, list) and titles else str(titles or "")
        title = normalize_whitespace(title_str)

        raw_abstract = item.get("abstract", "")
        summary = normalize_whitespace(re.sub(r"<[^>]+>", "", raw_abstract))

        authors: list[str] = []
        for auth in item.get("author", []):
            if isinstance(auth, dict):
                given = auth.get("given", "").strip()
                family = auth.get("family", "").strip()
                name = f"{given} {family}".strip() if (given or family) else auth.get("name", "").strip()
                if name:
                    authors.append(name)
            elif isinstance(auth, str) and auth.strip():
                authors.append(auth.strip())

        subjects = item.get("subject", []) or item.get("categories", [])
        categories = [normalize_whitespace(s) for s in subjects if s]
        primary_category = categories[0] if categories else "General"

        pub = item.get("published", {})
        date_parts = pub.get("date-parts", [[]])[0] if isinstance(pub, dict) else []
        if len(date_parts) >= 3:
            published = f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
        elif len(date_parts) == 2:
            published = f"{date_parts[0]:04d}-{date_parts[1]:02d}-01"
        elif len(date_parts) == 1:
            published = f"{date_parts[0]:04d}-01-01"
        else:
            published = str(item.get("created", {}).get("date-time", ""))[:10] or "2026-01-01"

        updated = published
        abs_url = item.get("URL", f"https://doi.org/{paper_id}")
        pdf_url = item.get("URL", f"https://doi.org/{paper_id}")
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
            query_params = urllib.parse.urlencode(
                {
                    "query": settings.source_query,
                    "filter": settings.source_filter,
                    "rows": settings.max_results,
                }
            )
            url = f"https://api.crossref.org/works?{query_params}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    write_json(settings.paths.raw_api_response, payload)
        except Exception:
            payload = None

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise FileNotFoundError(f"Raw API response snapshot not found at {settings.paths.raw_api_response}")

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    payload = read_json(path)
    if isinstance(payload, dict) and "message" in payload:
        return parse_crossref_payload(payload)
    if isinstance(payload, list):
        return [PaperRecord(**item) for item in payload]
    return []
