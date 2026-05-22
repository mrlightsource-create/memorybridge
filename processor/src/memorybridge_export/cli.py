from __future__ import annotations

import argparse
from pathlib import Path

from .android import list_devices, pull_candidates, scan_public_exports
from .parser import load_memories
from .processor import prepare_memories
from .zip_ingest import prepare_zip_export


def main() -> int:
    parser = argparse.ArgumentParser(prog="memorybridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Summarize a Snapchat memories_history.json file")
    scan_parser.add_argument("json", type=Path)

    prepare_parser = subparsers.add_parser("prepare", help="Prepare local media with restored metadata")
    prepare_parser.add_argument("--json", required=True, type=Path)
    prepare_parser.add_argument("--media-dir", type=Path)
    prepare_parser.add_argument("--out", required=True, type=Path)
    prepare_parser.add_argument("--download-missing", action="store_true")

    zip_parser = subparsers.add_parser("prepare-zip", help="Prepare media directly from one or more Snapchat export ZIPs")
    zip_parser.add_argument("zip", nargs="+", type=Path)
    zip_parser.add_argument("--out", required=True, type=Path)
    zip_parser.add_argument("--work-dir", type=Path)
    zip_parser.add_argument("--keep-work", action="store_true")

    android_scan_parser = subparsers.add_parser("android-scan", help="Find official export candidates on connected Android public storage")
    android_scan_parser.add_argument("--adb", type=Path)
    android_scan_parser.add_argument("--serial")

    android_pull_parser = subparsers.add_parser("android-pull", help="Pull official export candidates from connected Android public storage")
    android_pull_parser.add_argument("--adb", type=Path)
    android_pull_parser.add_argument("--serial")
    android_pull_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "scan":
        return run_scan(args.json)
    if args.command == "prepare":
        return run_prepare(args)
    if args.command == "prepare-zip":
        return run_prepare_zip(args)
    if args.command == "android-scan":
        return run_android_scan(args)
    if args.command == "android-pull":
        return run_android_pull(args)
    return 1


def run_scan(json_path: Path) -> int:
    items = load_memories(json_path)
    with_date = sum(1 for item in items if item.captured_at)
    with_location = sum(1 for item in items if item.has_location)
    with_url = sum(1 for item in items if item.download_url)
    videos = sum(1 for item in items if item.is_video)

    print(f"Memories: {len(items)}")
    print(f"With dates: {with_date}")
    print(f"With GPS: {with_location}")
    print(f"With download URLs: {with_url}")
    print(f"Videos: {videos}")
    print(f"Photos/other: {max(0, len(items) - videos)}")
    return 0


def run_prepare(args: argparse.Namespace) -> int:
    items = load_memories(args.json)
    prepared = prepare_memories(
        items=items,
        output_dir=args.out,
        media_dir=args.media_dir,
        download_missing=args.download_missing,
    )
    print(f"Prepared: {len(prepared)} of {len(items)}")
    print(f"Output: {args.out}")
    skipped = len(items) - len(prepared)
    if skipped:
        print(f"Skipped: {skipped} records had no matching local file or usable download URL")
    return 0


def run_prepare_zip(args: argparse.Namespace) -> int:
    result = prepare_zip_export(
        zip_paths=args.zip,
        output_dir=args.out,
        work_dir=args.work_dir,
        keep_work=args.keep_work,
    )
    print(f"JSON: {result.json_path}")
    print(f"Memories: {len(result.items)}")
    print(f"Prepared: {len(result.prepared)}")
    print(f"Output: {args.out}")
    if len(result.prepared) != len(result.items):
        print(f"Skipped: {len(result.items) - len(result.prepared)} records had no matching local file")
    return 0


def run_android_scan(args: argparse.Namespace) -> int:
    devices = list_devices(args.adb)
    if not devices:
        print("No Android devices found")
        return 2
    for device in devices:
        print(f"Device: {device.serial} {device.state} {device.description}".rstrip())
    candidates = scan_public_exports(args.adb, args.serial)
    if not candidates:
        print("No Snapchat export candidates found in Android public storage")
        return 2
    for candidate in candidates:
        print(f"{candidate.score:3d}  {safe_console(candidate.path)}  ({candidate.reason})")
    return 0


def run_android_pull(args: argparse.Namespace) -> int:
    candidates = scan_public_exports(args.adb, args.serial)
    if not candidates:
        print("No Snapchat export candidates found in Android public storage")
        return 2
    pulled = pull_candidates(candidates, args.out, args.adb, args.serial)
    for path in pulled:
        print(f"Pulled: {path}")
    return 0


def safe_console(value: object) -> str:
    text = str(value)
    return text.encode("ascii", "backslashreplace").decode("ascii")


if __name__ == "__main__":
    raise SystemExit(main())
