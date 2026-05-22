# MemoryBridge

Clean-room MVP for helping people move Snapchat Memories exports into storage they control.

This project intentionally does not copy code from `ethanwheatthin/Snapchat_Memories_Downloader_GUI`. It uses the same public product ideas:

- read Snapchat `memories_history.json`
- preserve date and location metadata
- process locally before cloud upload
- create an audit trail for each exported memory

## Project Layout

```text
memorybridge/
  src/                         React/Vite product surface
  public/                      Static visual assets
  processor/                   Python clean-room export processor
```

## Run The Website

```sh
cd memorybridge
npm install
npm run dev
```

## Run The Processor

```sh
cd memorybridge/processor
python -m pip install -e .
python -m memorybridge_export scan path/to/memories_history.json
python -m memorybridge_export prepare --json path/to/memories_history.json --media-dir path/to/export --out cleaned
python -m memorybridge_export prepare-zip path/to/snapchat-export.zip --out cleaned
python -m memorybridge_export android-scan
```

The processor keeps media local, sets file timestamps, writes JSON sidecars, and writes JPEG EXIF metadata when optional EXIF dependencies are installed.

## Metadata Source

MemoryBridge gets metadata from Snapchat's official `json/memories_history.json` export file:

- `Date` becomes the cleaned filename prefix, file modified time, and JPEG EXIF date.
- `Location` becomes JPEG GPS tags when coordinates are real.
- `Media Type` helps match each JSON row to the official `memories/*-main.jpg` or `memories/*-main.mp4` file.
- The original Snapchat row is preserved in each `.memorybridge.json` sidecar.

If Snapchat exports `Latitude, Longitude: 0.0, 0.0`, MemoryBridge treats that as a placeholder for missing GPS. It keeps the raw value in the sidecar but does not write fake GPS coordinates into the media file.

Each processor run writes `memorybridge_manifest.json` in the output folder with record counts, metadata coverage, EXIF status, and output notes.

## Product Boundary

MemoryBridge is designed around user-provided Snapchat data exports. It does not ask for Snapchat credentials, automate private login flows, or scrape account data.
