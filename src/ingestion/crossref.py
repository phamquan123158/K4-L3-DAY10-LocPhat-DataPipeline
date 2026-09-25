from __future__ import annotations

<<<<<<< HEAD
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from time import sleep

import requests
=======
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0

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


<<<<<<< HEAD
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
=======
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
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
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
<<<<<<< HEAD
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
=======
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
>>>>>>> 0bb30be50231f26e568a247d74a7b952947f0ce0
