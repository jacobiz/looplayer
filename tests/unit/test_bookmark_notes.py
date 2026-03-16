"""T002a / US6: LoopBookmark.notes フィールドのユニットテスト。"""
import json

import pytest

from looplayer.bookmark_store import LoopBookmark, BookmarkStore
from looplayer.bookmark_io import export_bookmarks, import_bookmarks


class TestLoopBookmarkNotesField:
    """LoopBookmark.notes フィールドの基本動作。"""

    def test_notes_default_is_empty_string(self):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000)
        assert bm.notes == ""

    def test_notes_can_be_set(self):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, notes="テストメモ")
        assert bm.notes == "テストメモ"

    def test_notes_in_to_dict(self):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, notes="メモ内容")
        d = bm.to_dict()
        assert "notes" in d
        assert d["notes"] == "メモ内容"

    def test_notes_default_in_to_dict(self):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000)
        d = bm.to_dict()
        assert d["notes"] == ""


class TestLoopBookmarkNotesFromDict:
    """from_dict での notes フィールドの後方互換性。"""

    def test_from_dict_with_notes(self):
        d = {
            "id": "test-id",
            "point_a_ms": 1000,
            "point_b_ms": 5000,
            "notes": "メモあり",
        }
        bm = LoopBookmark.from_dict(d)
        assert bm.notes == "メモあり"

    def test_from_dict_without_notes_falls_back_to_empty(self):
        """旧 JSON（notes キーなし）からの読み込みで notes="" にフォールバックすること。"""
        d = {
            "id": "test-id",
            "point_a_ms": 1000,
            "point_b_ms": 5000,
        }
        bm = LoopBookmark.from_dict(d)
        assert bm.notes == ""


class TestBookmarkStorePersistenceWithNotes:
    """BookmarkStore の notes フィールドの保存・復元。"""

    def test_notes_saved_and_loaded(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, notes="保存テスト")
        store.add("/video.mp4", bm)

        store2 = BookmarkStore(storage_path=tmp_path / "bm.json")
        loaded = store2.get_bookmarks("/video.mp4")
        assert loaded[0].notes == "保存テスト"

    def test_old_json_without_notes_loads_as_empty(self, tmp_path):
        """notes フィールドがない旧 bookmarks.json から読み込んでも動作すること。"""
        old_json = {
            "/video.mp4": [
                {
                    "id": "abc",
                    "point_a_ms": 1000,
                    "point_b_ms": 5000,
                    "name": "旧ブックマーク",
                    "repeat_count": 1,
                    "order": 0,
                    "enabled": True,
                    # notes フィールドなし（旧フォーマット）
                }
            ]
        }
        path = tmp_path / "bm.json"
        path.write_text(json.dumps(old_json), encoding="utf-8")

        store = BookmarkStore(storage_path=path)
        loaded = store.get_bookmarks("/video.mp4")
        assert loaded[0].notes == ""


class TestBookmarkIOWithNotes:
    """bookmark_io の export/import で notes フィールドが保持されること。"""

    def test_export_includes_notes_field(self, tmp_path):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, notes="エクスポートテスト")
        dest = tmp_path / "export.json"
        export_bookmarks([bm], str(dest))
        data = json.loads(dest.read_text())
        assert "notes" in data["bookmarks"][0]
        assert data["bookmarks"][0]["notes"] == "エクスポートテスト"

    def test_export_notes_empty_string_included(self, tmp_path):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000)
        dest = tmp_path / "export.json"
        export_bookmarks([bm], str(dest))
        data = json.loads(dest.read_text())
        assert data["bookmarks"][0]["notes"] == ""

    def test_import_preserves_notes(self, tmp_path):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, notes="インポートテスト")
        dest = tmp_path / "round_trip.json"
        export_bookmarks([bm], str(dest))
        result = import_bookmarks(str(dest))
        assert result[0].get("notes") == "インポートテスト"

    def test_import_old_json_without_notes_falls_back_to_empty(self, tmp_path):
        """notes フィールドがない旧エクスポートファイルは notes="" にフォールバックすること。"""
        data = {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "bookmarks": [
                {"name": "旧データ", "point_a_ms": 1000, "point_b_ms": 5000,
                 "repeat_count": 1, "order": 0, "enabled": True}
            ],
        }
        dest = tmp_path / "old_format.json"
        dest.write_text(json.dumps(data))
        result = import_bookmarks(str(dest))
        assert result[0].get("notes", "") == ""
