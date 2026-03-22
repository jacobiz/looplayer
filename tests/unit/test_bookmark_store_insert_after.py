"""Tests for BookmarkStore.insert_after() method."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from looplayer.bookmark_store import BookmarkStore, LoopBookmark


VIDEO = "/test/video.mp4"


def make_store(tmp_path: Path) -> BookmarkStore:
    return BookmarkStore(storage_path=tmp_path / "bookmarks.json")


def make_bm(order: int = 0, name: str = "") -> LoopBookmark:
    return LoopBookmark(point_a_ms=order * 1000, point_b_ms=order * 1000 + 500, name=name, order=order)


class TestInsertAfter:
    def test_insert_after_middle_reorders(self, tmp_path):
        """中間位置への挿入後の order が正しい。"""
        store = make_store(tmp_path)
        bm0 = make_bm(0, "first")
        bm1 = make_bm(1, "second")
        store.add(VIDEO, bm0)
        store.add(VIDEO, bm1)

        new_bm = LoopBookmark(point_a_ms=100, point_b_ms=200, name="inserted")
        store.insert_after(VIDEO, new_bm, after_id=bm0.id)

        result = store.get_bookmarks(VIDEO)
        assert len(result) == 3
        assert result[0].id == bm0.id
        assert result[1].id == new_bm.id
        assert result[2].id == bm1.id
        # orders must be 0, 1, 2
        assert [b.order for b in result] == [0, 1, 2]

    def test_insert_after_unknown_id_appends_to_end(self, tmp_path):
        """after_id が存在しない場合は末尾に追加される。"""
        store = make_store(tmp_path)
        bm0 = make_bm(0, "first")
        bm1 = make_bm(1, "second")
        store.add(VIDEO, bm0)
        store.add(VIDEO, bm1)

        new_bm = LoopBookmark(point_a_ms=100, point_b_ms=200, name="tail")
        store.insert_after(VIDEO, new_bm, after_id="nonexistent-id")

        result = store.get_bookmarks(VIDEO)
        assert len(result) == 3
        assert result[-1].id == new_bm.id

    def test_insert_after_saves_to_json(self, tmp_path):
        """insert_after() 後に _save_all() が呼ばれて JSON に永続化される。"""
        store = make_store(tmp_path)
        bm0 = make_bm(0, "first")
        store.add(VIDEO, bm0)

        new_bm = LoopBookmark(point_a_ms=100, point_b_ms=200, name="new")
        store.insert_after(VIDEO, new_bm, after_id=bm0.id)

        # Reload from disk to confirm persistence
        store2 = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        result = store2.get_bookmarks(VIDEO)
        assert len(result) == 2
        names = [b.name for b in result]
        assert "new" in names

    def test_insert_after_assigns_default_name_when_empty(self, tmp_path):
        """name が空のブックマークにはデフォルト名が付与される。"""
        store = make_store(tmp_path)
        bm0 = make_bm(0, "first")
        store.add(VIDEO, bm0)

        new_bm = LoopBookmark(point_a_ms=100, point_b_ms=200, name="")
        store.insert_after(VIDEO, new_bm, after_id=bm0.id)

        result = store.get_bookmarks(VIDEO)
        inserted = next(b for b in result if b.id == new_bm.id)
        assert inserted.name != ""
