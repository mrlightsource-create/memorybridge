# MemoryBridge

Clean-room MVP for helping people turn Snapchat Memories downloads into a clean folder they control.

This project intentionally does not copy code from `ethanwheatthin/Snapchat_Memories_Downloader_GUI`. It uses the same public product ideas:

- read Snapchat's memory list
- match photos and videos to the dates and places Snapchat included
- process locally on the user's machine
- create a simple receipt for each run

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

The processor keeps media local, sets file dates, writes small helper receipt files, and produces a run summary.

## Where Dates And Places Come From

MemoryBridge gets dates and places from Snapchat's official `json/memories_history.json` export file:

- `Date` becomes part of the cleaned filename and file date.
- `Location` is kept when Snapchat provides a real place.
- `Media Type` helps match each row to the official `memories/*-main.jpg` or `memories/*-main.mp4` file.
- The original Snapchat row is preserved in each `.memorybridge.json` helper file.

If Snapchat exports `Latitude, Longitude: 0.0, 0.0`, MemoryBridge treats that as a blank place. It keeps the raw value in the helper file but does not pretend it is real.

Each processor run writes `memorybridge_manifest.json` in the output folder with counts and notes.

## Product Boundary

MemoryBridge is designed around user-provided Snapchat data exports. It does not ask for Snapchat credentials, automate private login flows, or scrape account data.
