from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timezone
import json
from pathlib import Path
import re
import shutil
import urllib.request

from .metadata import apply_file_timestamp, write_image_exif, write_sidecar
from .parser import MemoryItem, sanitize_token


MEDIA_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".mp4",
    ".mov",
    ".m4v",
}

VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}
SNAPCHAT_MAIN_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_.+-main\.[^.]+$", re.IGNORECASE)


@dataclass(frozen=True)
class PreparedMemory:
    item: MemoryItem
    output_path: Path
    source_path: Path | None
    sidecar_path: Path
    exif_status: str


def prepare_memories(
    items: list[MemoryItem],
    output_dir: str | Path,
    media_dir: str | Path | None = None,
    download_missing: bool = False,
) -> list[PreparedMemory]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    media_files = list_media_files(Path(media_dir)) if media_dir else []
    used_sources: set[Path] = set()
    prepared: list[PreparedMemory] = []

    for item in items:
        source = find_source(item, media_files, used_sources)
        if source:
            used_sources.add(source)
        elif download_missing and item.download_url:
            source = download_to_temp(item, out)
            used_sources.add(source)
        else:
            continue

        extension = source.suffix.lower() or guess_extension(item)
        output_path = unique_path(out / f"{filename_stem(item)}{extension}")
        shutil.copy2(source, output_path)
        exif_status = write_image_exif(output_path, item.captured_at, item.latitude, item.longitude)
        apply_file_timestamp(output_path, item.captured_at)
        sidecar_path = write_sidecar(
            output_path,
            {
                "stableId": item.stable_id,
                "mediaType": item.media_type,
                "capturedAt": item.captured_at.astimezone(timezone.utc).isoformat() if item.captured_at else None,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "locationStatus": location_status(item),
                "downloadUrlPresent": bool(item.download_url),
                "sourcePath": str(source),
                "exifStatus": exif_status,
                "metadataSource": metadata_source(item),
                "original": item.original,
            },
        )
        prepared.append(PreparedMemory(item, output_path, source, sidecar_path, exif_status))

    write_run_manifest(out, items, prepared)
    return prepared


def list_media_files(media_dir: Path) -> list[Path]:
    if not media_dir.exists():
        return []
    files = [path for path in media_dir.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES]
    return sorted(files, key=media_sort_key)


def find_source(item: MemoryItem, media_files: list[Path], used_sources: set[Path]) -> Path | None:
    candidates = [path for path in media_files if path not in used_sources]
    stable = item.stable_id.lower()
    for path in candidates:
        if stable and stable in path.stem.lower():
            return path

    if item.captured_at:
        target = item.captured_at.timestamp()
        close = [
            path
            for path in candidates
            if abs(path.stat().st_mtime - target) <= 2
        ]
        if close:
            return close[0]

    if item.download_url:
        url_name = Path(item.download_url.split("?", 1)[0]).name.lower()
        for path in candidates:
            if path.name.lower() == url_name:
                return path

    snapchat_match = find_snapchat_archive_source(item, candidates)
    if snapchat_match:
        return snapchat_match
    return None


def find_snapchat_archive_source(item: MemoryItem, candidates: list[Path]) -> Path | None:
    if not item.captured_at:
        return None
    item_day = item.captured_at.strftime("%Y-%m-%d")
    for path in candidates:
        if snapchat_archive_day(path) == item_day and media_kind_matches(item, path):
            return path
    return None


def media_sort_key(path: Path) -> tuple[int, int, float, str]:
    archive_day = snapchat_archive_day(path)
    is_main_export = archive_day is not None and "-main." in path.name.lower()
    if is_main_export:
        newest_first = -int(archive_day.replace("-", ""))
        return (0, newest_first, 0, path.name.lower())
    return (1, 0, path.stat().st_mtime, str(path).lower())


def snapchat_archive_day(path: Path) -> str | None:
    match = SNAPCHAT_MAIN_RE.match(path.name)
    return match.group(1) if match else None


def media_kind_matches(item: MemoryItem, path: Path) -> bool:
    is_video_path = path.suffix.lower() in VIDEO_SUFFIXES
    return item.is_video == is_video_path


def location_status(item: MemoryItem) -> str:
    if item.has_location:
        return "real"
    raw = raw_location(item)
    if is_zero_zero_location(raw):
        return "placeholder:zero-zero"
    if raw:
        return "invalid"
    return "missing"


def raw_location(item: MemoryItem) -> str:
    for key in ("Location", "location", "GPS", "gps"):
        value = item.original.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def is_zero_zero_location(value: str) -> bool:
    numbers = re.findall(r"-?\d+(?:\.\d+)?", value)
    if len(numbers) < 2:
        return False
    try:
        return float(numbers[0]) == 0 and float(numbers[1]) == 0
    except ValueError:
        return False


def metadata_source(item: MemoryItem) -> dict[str, str]:
    return {
        "captureTime": "Snapchat export json/memories_history.json field: Date",
        "location": "Snapchat export json/memories_history.json field: Location",
        "mediaType": "Snapchat export json/memories_history.json field: Media Type",
        "mediaFile": "Official export memories/*-main media, matched by export ID/date/type",
        "rawRow": "Original Snapchat JSON row preserved in original",
        "locationStatus": location_status(item),
    }


def write_run_manifest(output_dir: Path, items: list[MemoryItem], prepared: list[PreparedMemory]) -> Path:
    sidecar_statuses = Counter(location_status(item) for item in items)
    exif_statuses = Counter(record.exif_status for record in prepared)
    manifest = {
        "source": "Snapchat official export",
        "metadataSource": {
            "json": "json/memories_history.json",
            "media": "memories/*-main.jpg and memories/*-main.mp4",
        },
        "counts": {
            "records": len(items),
            "prepared": len(prepared),
            "realLocations": sidecar_statuses["real"],
            "zeroZeroPlaceholders": sidecar_statuses["placeholder:zero-zero"],
            "missingLocations": sidecar_statuses["missing"],
            "invalidLocations": sidecar_statuses["invalid"],
            "dated": sum(1 for item in items if item.captured_at),
            "videos": sum(1 for item in items if item.is_video),
            "photosOrOther": sum(1 for item in items if not item.is_video),
        },
        "exifStatus": dict(sorted(exif_statuses.items())),
        "outputs": {
            "mediaFiles": "cleaned files in this folder",
            "sidecars": "*.memorybridge.json",
        },
    }
    path = output_dir / "memorybridge_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def filename_stem(item: MemoryItem) -> str:
    if item.captured_at:
        prefix = item.captured_at.strftime("%Y%m%d_%H%M%S")
    else:
        prefix = f"undated_{item.index:06d}"
    return f"{prefix}_{sanitize_token(item.stable_id)}"


def guess_extension(item: MemoryItem) -> str:
    return ".mp4" if item.is_video else ".jpg"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 10000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not create a unique output path for {path}")


def download_to_temp(item: MemoryItem, output_dir: Path) -> Path:
    temp_dir = output_dir / ".memorybridge-downloads"
    temp_dir.mkdir(exist_ok=True)
    destination = unique_path(temp_dir / f"{sanitize_token(item.stable_id)}{guess_extension(item)}")
    request = urllib.request.Request(item.download_url, headers={"User-Agent": "MemoryBridge/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())
    return destination
