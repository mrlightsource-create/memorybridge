# MemoryBridge Processor

Local clean-room processor for Snapchat Memories exports.

## Commands

```sh
python -m pip install -e .
python -m memorybridge_export scan path/to/memories_history.json
python -m memorybridge_export prepare --json path/to/memories_history.json --media-dir path/to/export --out cleaned
python -m memorybridge_export prepare --json path/to/memories_history.json --out cleaned --download-missing
python -m memorybridge_export prepare-zip path/to/snapchat-export.zip --out cleaned
python -m memorybridge_export android-scan
python -m memorybridge_export android-pull --out pulled-exports
```

## What It Writes

- renamed media files based on exported capture dates
- file modification timestamps
- `.memorybridge.json` sidecars with original metadata
- JPEG EXIF dates and GPS when `piexif` and `Pillow` are installed

Video metadata is currently preserved in sidecars. Cloud upload adapters should use those sidecars when a provider cannot read embedded video metadata reliably.
