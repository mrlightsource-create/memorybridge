from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess


PUBLIC_SEARCH_ROOTS = ("/sdcard/Download", "/sdcard/Documents")


@dataclass(frozen=True)
class AndroidDevice:
    serial: str
    state: str
    description: str


@dataclass(frozen=True)
class AndroidCandidate:
    path: str
    score: int
    reason: str


def find_adb(adb_path: str | Path | None = None) -> Path:
    candidates: list[str | Path | None] = [
        adb_path,
        shutil.which("adb"),
        os.environ.get("ADB"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        Path(os.environ.get("ANDROID_HOME", "")) / "platform-tools" / "adb.exe",
        Path(os.environ.get("ANDROID_SDK_ROOT", "")) / "platform-tools" / "adb.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise FileNotFoundError("adb was not found. Install Android platform-tools or pass --adb")


def list_devices(adb_path: str | Path | None = None) -> list[AndroidDevice]:
    adb = find_adb(adb_path)
    result = run_adb(adb, ["devices", "-l"])
    devices: list[AndroidDevice] = []
    for line in result.stdout.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 2)
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"
        description = parts[2] if len(parts) > 2 else ""
        devices.append(AndroidDevice(serial, state, description))
    return devices


def scan_public_exports(adb_path: str | Path | None = None, serial: str | None = None) -> list[AndroidCandidate]:
    adb = find_adb(adb_path)
    roots = " ".join(PUBLIC_SEARCH_ROOTS)
    # Keep this intentionally narrow. Google Takeout can contain thousands of
    # per-photo files with "Snapchat" in the name; those are not Snapchat
    # account exports and make the scan unusably noisy.
    name_expr = (
        r'\( -name "memories_history.json" -o -iname "*snapchat*.zip" '
        r'-o -iname "*mydata*.zip" -o -iname "*my_data*.zip" '
        r'-o -iname "*downloadmydata*.zip" \)'
    )
    command = f"find {roots} -maxdepth 6 -type f {name_expr} 2>/dev/null | head -200"
    result = run_adb(adb, with_serial(serial, ["shell", command]), check=False)
    paths = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
    return sorted((score_candidate(path) for path in paths), key=lambda item: (-item.score, item.path.lower()))


def pull_candidates(
    candidates: list[AndroidCandidate],
    output_dir: str | Path,
    adb_path: str | Path | None = None,
    serial: str | None = None,
) -> list[Path]:
    adb = find_adb(adb_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pulled: list[Path] = []
    for candidate in candidates:
        destination = out / Path(candidate.path).name
        run_adb(adb, with_serial(serial, ["pull", candidate.path, str(destination)]))
        pulled.append(destination)
    return pulled


def score_candidate(path: str) -> AndroidCandidate:
    name = Path(path).name.lower()
    if "memories_history" in name:
        return AndroidCandidate(path, 100, "memories history JSON")
    if "snapchat" in name and name.endswith(".zip"):
        return AndroidCandidate(path, 95, "Snapchat ZIP export candidate")
    if "snapchat" in name and name.endswith(".json"):
        return AndroidCandidate(path, 90, "Snapchat JSON candidate")
    if "downloadmydata" in name or "my_data" in name or "mydata" in name:
        return AndroidCandidate(path, 80, "account data export naming")
    return AndroidCandidate(path, 10, "possible export")


def run_adb(adb: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([str(adb), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"adb exited {result.returncode}")
    return result


def with_serial(serial: str | None, args: list[str]) -> list[str]:
    return ["-s", serial, *args] if serial else args
