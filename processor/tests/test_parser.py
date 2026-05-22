from datetime import timezone
import json

from memorybridge_export.parser import load_memories, parse_date, parse_location
from memorybridge_export.processor import filename_stem


def test_parse_location_accepts_snapchat_style_coordinates():
    assert parse_location("Latitude: 43.6532, Longitude: -79.3832") == (43.6532, -79.3832)


def test_parse_location_rejects_invalid_ranges():
    assert parse_location("999, -79") == (None, None)


def test_parse_location_treats_zero_zero_as_missing():
    assert parse_location("Latitude, Longitude: 0.0, 0.0") == (None, None)


def test_parse_date_normalizes_utc_suffix():
    parsed = parse_date("2024-01-02 03:04:05 UTC")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).hour == 3


def test_load_memories_from_saved_media(tmp_path):
    export = {
        "Saved Media": [
            {
                "Date": "2024-01-02 03:04:05 UTC",
                "Media Type": "Video",
                "Location": "43.6532, -79.3832",
                "Media Download Url": "https://example.com/file.mp4",
            }
        ]
    }
    path = tmp_path / "memories_history.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    items = load_memories(path)

    assert len(items) == 1
    assert items[0].is_video
    assert items[0].has_location
    assert items[0].download_url == "https://example.com/file.mp4"
    assert filename_stem(items[0]).startswith("20240102_030405_")


def test_load_memories_accepts_utf8_bom(tmp_path):
    path = tmp_path / "memories_history.json"
    path.write_text('\ufeff{"Saved Media": [{"Date": "2024-01-02 03:04:05 UTC"}]}', encoding="utf-8")

    items = load_memories(path)

    assert len(items) == 1
    assert items[0].captured_at is not None
