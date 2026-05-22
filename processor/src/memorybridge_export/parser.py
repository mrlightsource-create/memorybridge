from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S %Z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y, %H:%M:%S",
)


@dataclass(frozen=True)
class MemoryItem:
    index: int
    media_type: str
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    download_url: str
    original: dict[str, Any]

    @property
    def has_location(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def is_video(self) -> bool:
        return "video" in self.media_type.lower()

    @property
    def stable_id(self) -> str:
        candidates = (
            self.original.get("Snap ID"),
            self.original.get("Memory ID"),
            self.original.get("Media ID"),
            self.original.get("id"),
        )
        for candidate in candidates:
            if candidate:
                return sanitize_token(str(candidate))
        if self.download_url:
            filename = Path(self.download_url.split("?", 1)[0]).name
            if filename:
                return sanitize_token(Path(filename).stem)
        return f"memory-{self.index:06d}"


def load_memories(json_path: str | Path) -> list[MemoryItem]:
    path = Path(json_path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = extract_rows(payload)
    return [row_to_item(index, row) for index, row in enumerate(rows, start=1)]


def extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("Saved Media", "savedMedia", "memories", "media"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def row_to_item(index: int, row: dict[str, Any]) -> MemoryItem:
    latitude, longitude = parse_location(first_present(row, "Location", "location", "GPS", "gps"))
    return MemoryItem(
        index=index,
        media_type=str(first_present(row, "Media Type", "mediaType", "type") or "Media"),
        captured_at=parse_date(first_present(row, "Date", "date", "Created", "createdAt")),
        latitude=latitude,
        longitude=longitude,
        download_url=str(first_present(row, "Media Download Url", "downloadUrl", "Download URL") or ""),
        original=row,
    )


def first_present(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def parse_date(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return ensure_timezone(value)
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    normalized = raw.replace(" UTC", "+00:00")
    try:
        return ensure_timezone(datetime.fromisoformat(normalized.replace("Z", "+00:00")))
    except ValueError:
        pass

    for date_format in DATE_FORMATS:
        try:
            return ensure_timezone(datetime.strptime(raw, date_format))
        except ValueError:
            continue
    return None


def ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def parse_location(value: Any) -> tuple[float | None, float | None]:
    if not value:
        return None, None
    numbers = re.findall(r"-?\d+(?:\.\d+)?", str(value))
    if len(numbers) < 2:
        return None, None
    latitude = float(numbers[0])
    longitude = float(numbers[1])
    if abs(latitude) > 90 or abs(longitude) > 180:
        return None, None
    if latitude == 0 and longitude == 0:
        return None, None
    return latitude, longitude


def sanitize_token(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    return clean[:80] or "memory"
