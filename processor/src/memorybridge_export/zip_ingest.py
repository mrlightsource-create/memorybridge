from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo
import os

from .parser import MemoryItem, load_memories
from .processor import PreparedMemory, prepare_memories


@dataclass(frozen=True)
class ZipIngestResult:
    json_path: Path
    extracted_dir: Path
    items: list[MemoryItem]
    prepared: list[PreparedMemory]
    cleanup: TemporaryDirectory[str] | None = None


def prepare_zip_export(
    zip_paths: list[str | Path],
    output_dir: str | Path,
    work_dir: str | Path | None = None,
    keep_work: bool = False,
) -> ZipIngestResult:
    if not zip_paths:
        raise ValueError("At least one ZIP path is required")

    cleanup: TemporaryDirectory[str] | None = None
    if work_dir:
        extracted_dir = Path(work_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)
    else:
        cleanup = TemporaryDirectory(prefix="memorybridge_export_")
        extracted_dir = Path(cleanup.name)

    for index, zip_path in enumerate(zip_paths, start=1):
        destination = extracted_dir / f"zip_{index:03d}"
        destination.mkdir(parents=True, exist_ok=True)
        safe_extract_zip(Path(zip_path), destination)

    json_path = find_memories_history(extracted_dir)
    if not json_path:
        if cleanup and not keep_work:
            cleanup.cleanup()
        raise FileNotFoundError("No memories_history.json file was found inside the ZIP export")

    items = load_memories(json_path)
    prepared = prepare_memories(items=items, output_dir=output_dir, media_dir=extracted_dir)

    if cleanup and not keep_work:
        cleanup.cleanup()
        cleanup = None

    return ZipIngestResult(
        json_path=json_path,
        extracted_dir=extracted_dir,
        items=items,
        prepared=prepared,
        cleanup=cleanup,
    )


def find_memories_history(root: Path) -> Path | None:
    candidates = sorted(
        [path for path in root.rglob("*") if path.is_file() and path.name.lower() == "memories_history.json"],
        key=lambda path: (len(path.parts), str(path).lower()),
    )
    return candidates[0] if candidates else None


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    root = destination.resolve()
    with ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"Unsafe ZIP path rejected: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                output.write(source.read())
            apply_zip_timestamp(target, member)


def apply_zip_timestamp(path: Path, member: ZipInfo) -> None:
    try:
        year, month, day, hour, minute, second = member.date_time
        timestamp = __import__("datetime").datetime(year, month, day, hour, minute, second).timestamp()
        os.utime(path, (timestamp, timestamp))
    except Exception:
        return
