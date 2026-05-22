from __future__ import annotations

import json
from zipfile import ZipFile

from memorybridge_export.android import score_candidate
from memorybridge_export.zip_ingest import prepare_zip_export


def test_prepare_zip_export_finds_json_and_media(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "json").mkdir()
    (source / "memories").mkdir()
    (source / "json" / "memories_history.json").write_text(
        json.dumps(
            {
                "Saved Media": [
                    {
                        "Date": "2024-01-02 03:04:05 UTC",
                        "Media Type": "Photo",
                        "Location": "43.6532, -79.3832",
                        "Snap ID": "snap-test-001",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (source / "memories" / "snap-test-001.jpg").write_bytes(b"not-a-real-jpeg-but-good-enough")

    zip_path = tmp_path / "snapchat-export.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.write(source / "json" / "memories_history.json", "json/memories_history.json")
        archive.write(source / "memories" / "snap-test-001.jpg", "memories/snap-test-001.jpg")

    out = tmp_path / "out"
    result = prepare_zip_export([zip_path], out)

    assert len(result.items) == 1
    assert len(result.prepared) == 1
    assert (out / "20240102_030405_snap-test-001.jpg").exists()
    assert (out / "20240102_030405_snap-test-001.jpg.memorybridge.json").exists()
    assert (out / "memorybridge_manifest.json").exists()


def test_prepare_zip_export_matches_official_snapchat_memory_layout(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "json").mkdir()
    (source / "memories").mkdir()
    (source / "json" / "memories_history.json").write_text(
        json.dumps(
            {
                "Saved Media": [
                    {
                        "Date": "2021-12-03 01:10:37 UTC",
                        "Media Type": "Video",
                        "Location": "43.63736, -79.41838",
                        "Download Link": "",
                        "Media Download Url": "",
                    },
                    {
                        "Date": "2021-12-03 01:10:07 UTC",
                        "Media Type": "Image",
                        "Location": "43.63736, -79.41838",
                        "Download Link": "",
                        "Media Download Url": "",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (source / "memories" / "2021-12-03_001-main.mp4").write_bytes(b"video")
    (source / "memories" / "2021-12-03_002-main.jpg").write_bytes(b"image")
    (source / "memories" / "2021-12-03_002-overlay.png").write_bytes(b"overlay")

    zip_path = tmp_path / "mydata.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.write(source / "json" / "memories_history.json", "json/memories_history.json")
        archive.write(source / "memories" / "2021-12-03_001-main.mp4", "memories/2021-12-03_001-main.mp4")
        archive.write(source / "memories" / "2021-12-03_002-main.jpg", "memories/2021-12-03_002-main.jpg")
        archive.write(source / "memories" / "2021-12-03_002-overlay.png", "memories/2021-12-03_002-overlay.png")

    out = tmp_path / "out"
    result = prepare_zip_export([zip_path], out)

    assert len(result.items) == 2
    assert len(result.prepared) == 2
    assert (out / "20211203_011037_memory-000001.mp4").read_bytes() == b"video"
    assert (out / "20211203_011007_memory-000002.jpg").read_bytes() == b"image"
    sidecar = json.loads((out / "20211203_011007_memory-000002.jpg.memorybridge.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "memorybridge_manifest.json").read_text(encoding="utf-8"))
    assert sidecar["metadataSource"]["location"] == "Snapchat export json/memories_history.json field: Location"
    assert sidecar["locationStatus"] == "real"
    assert manifest["counts"]["records"] == 2
    assert manifest["counts"]["realLocations"] == 2


def test_android_candidate_scoring_prioritizes_snapchat_export_names():
    assert score_candidate("/sdcard/Download/memories_history.json").score == 100
    assert score_candidate("/sdcard/Download/snapchat-export.zip").score == 95
    assert score_candidate("/sdcard/Download/mydata.zip").score == 80
