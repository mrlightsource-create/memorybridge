from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
from typing import Any


IMAGE_SUFFIXES = {".jpg", ".jpeg"}


def apply_file_timestamp(path: Path, captured_at: datetime | None) -> None:
    if not captured_at:
        return
    timestamp = captured_at.timestamp()
    os.utime(path, (timestamp, timestamp))


def write_sidecar(path: Path, metadata: dict[str, Any]) -> Path:
    sidecar = path.with_suffix(path.suffix + ".memorybridge.json")
    sidecar.write_text(json.dumps(metadata, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return sidecar


def write_image_exif(
    path: Path,
    captured_at: datetime | None,
    latitude: float | None,
    longitude: float | None,
) -> str:
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return "skipped:not-jpeg"
    if not captured_at:
        return "skipped:no-date"

    try:
        import piexif  # type: ignore
    except Exception:
        return "skipped:piexif-missing"

    try:
        exif_dict = piexif.load(str(path))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    date_value = captured_at.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")
    exif_dict.setdefault("Exif", {})[piexif.ExifIFD.DateTimeOriginal] = date_value
    exif_dict.setdefault("Exif", {})[piexif.ExifIFD.DateTimeDigitized] = date_value
    exif_dict.setdefault("0th", {})[piexif.ImageIFD.DateTime] = date_value

    if captured_at.utcoffset() is not None:
        offset = captured_at.strftime("%z")
        offset_value = f"{offset[:3]}:{offset[3:]}".encode("ascii")
        exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal] = offset_value
        exif_dict["Exif"][piexif.ExifIFD.OffsetTimeDigitized] = offset_value

    if latitude is not None and longitude is not None:
        exif_dict.setdefault("GPS", {})[piexif.GPSIFD.GPSLatitudeRef] = b"N" if latitude >= 0 else b"S"
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = to_dms(abs(latitude))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b"E" if longitude >= 0 else b"W"
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = to_dms(abs(longitude))

    try:
        piexif.insert(piexif.dump(exif_dict), str(path))
    except Exception:
        return "failed:exif-write"
    return "written"


def to_dms(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60 * 10000)
    return ((degrees, 1), (minutes, 1), (seconds, 10000))
