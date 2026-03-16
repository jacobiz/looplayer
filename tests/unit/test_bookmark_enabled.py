"""enabled フィールド: LoopBookmark / BookmarkStore のユニットテスト。"""
import pytest
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore, LoopBookmark


class TestLoopBookmarkEnabled:
    """LoopBookmark の enabled フィールド。"""

    def test_default_enabled_is_true(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        assert bm.enabled is True

    def test_enabled_false_can_be_set(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, enabled=False)
        assert bm.enabled is False

    def test_to_dict_includes_enabled(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, enabled=False)
        d = bm.to_dict()
        assert "enabled" in d
        assert d["enabled"] is False

    def test_from_dict_with_enabled(self):
        d = {
            "id": "abc",
            "point_a_ms": 0,
            "point_b_ms": 1000,
            "name": "test",
            "repeat_count": 1,
            "order": 0,
            "enabled": False,
        }
        bm = LoopBookmark.from_dict(d)
        assert bm.enabled is False

    def test_from_dict_without_enabled_defaults_true(self):
        """後方互換: enabled キーがない旧 JSON でも True にフォールバックする。"""
        d = {
            "id": "abc",
            "point_a_ms": 0,
            "point_b_ms": 1000,
            "name": "test",
            "repeat_count": 1,
            "order": 0,
        }
        bm = LoopBookmark.from_dict(d)
        assert bm.enabled is True

    def test_roundtrip_preserves_enabled_false(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, enabled=False)
        store.add("/video.mp4", bm)
        # 再読み込み
        store2 = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        loaded = store2.get_bookmarks("/video.mp4")
        assert loaded[0].enabled is False

    def test_new_bookmark_added_to_store_defaults_enabled_true(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/video.mp4", bm)
        loaded = store.get_bookmarks("/video.mp4")
        assert loaded[0].enabled is True


class TestBookmarkStoreUpdateEnabled:
    """BookmarkStore.update_enabled() のテスト。"""

    def test_update_enabled_false(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/video.mp4", bm)
        bm_id = store.get_bookmarks("/video.mp4")[0].id
        store.update_enabled("/video.mp4", bm_id, False)
        assert store.get_bookmarks("/video.mp4")[0].enabled is False

    def test_update_enabled_true(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, enabled=False)
        store.add("/video.mp4", bm)
        bm_id = store.get_bookmarks("/video.mp4")[0].id
        store.update_enabled("/video.mp4", bm_id, True)
        assert store.get_bookmarks("/video.mp4")[0].enabled is True

    def test_update_enabled_persists(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/video.mp4", bm)
        bm_id = store.get_bookmarks("/video.mp4")[0].id
        store.update_enabled("/video.mp4", bm_id, False)
        store2 = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        assert store2.get_bookmarks("/video.mp4")[0].enabled is False


class TestBookmarkOldJsonBackwardCompat:
    """旧 JSON（enabled フィールドなし）の後方互換テスト。"""

    def test_old_json_loads_with_enabled_true(self, tmp_path):
        import json
        old_data = {
            "/video.mp4": [
                {
                    "id": "abc123",
                    "name": "旧ブックマーク",
                    "point_a_ms": 1000,
                    "point_b_ms": 5000,
                    "repeat_count": 2,
                    "order": 0,
                }
            ]
        }
        p = tmp_path / "bookmarks.json"
        p.write_text(json.dumps(old_data))
        store = BookmarkStore(storage_path=p)
        bms = store.get_bookmarks("/video.mp4")
        assert len(bms) == 1
        assert bms[0].enabled is True
