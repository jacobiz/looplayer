"""Tests for BookmarkPanel jump-to-A and duplicate handlers (US2)."""
import pytest
from unittest.mock import MagicMock, patch

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t


VIDEO = "/test/video.mp4"


def make_store(tmp_path):
    return BookmarkStore(storage_path=tmp_path / "bm.json")


def make_bm(a_ms=1000, b_ms=2000, name="bm", order=0):
    bm = LoopBookmark(point_a_ms=a_ms, point_b_ms=b_ms, name=name, order=order)
    return bm


def make_panel(store, qapp):
    from looplayer.widgets.bookmark_panel import BookmarkPanel
    panel = BookmarkPanel(store=store)
    return panel


class TestBookmarkPanelJumpToA:
    def test_on_jump_to_a_emits_seek_to_ms_requested(self, qapp, tmp_path):
        """_on_jump_to_a 呼び出し時に seek_to_ms_requested(a_ms) が emit されること。"""
        store = make_store(tmp_path)
        bm = make_bm(a_ms=3000, b_ms=5000, name="test")
        store.add(VIDEO, bm)

        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        received = []
        panel.seek_to_ms_requested.connect(lambda ms: received.append(ms))

        panel._on_jump_to_a(bm.id)

        assert received == [3000]

    def test_on_jump_to_a_does_nothing_when_no_video(self, qapp, tmp_path):
        """動画未ロード時は _on_jump_to_a が何もしないこと。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)
        # No load_video called

        received = []
        panel.seek_to_ms_requested.connect(lambda ms: received.append(ms))

        panel._on_jump_to_a("nonexistent-id")
        assert received == []

    def test_on_jump_to_a_does_nothing_for_unknown_id(self, qapp, tmp_path):
        """存在しない bookmark_id の場合は何もしないこと。"""
        store = make_store(tmp_path)
        bm = make_bm(a_ms=1000, b_ms=2000, name="bm")
        store.add(VIDEO, bm)
        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        received = []
        panel.seek_to_ms_requested.connect(lambda ms: received.append(ms))

        panel._on_jump_to_a("nonexistent-id")
        assert received == []


class TestBookmarkPanelDuplicate:
    def test_on_duplicate_adds_copy_to_store(self, qapp, tmp_path):
        """_on_duplicate 呼び出し時にストアに複製ブックマークが追加されること。"""
        store = make_store(tmp_path)
        bm = make_bm(a_ms=1000, b_ms=2000, name="original")
        store.add(VIDEO, bm)

        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        panel._on_duplicate(bm.id)

        result = store.get_bookmarks(VIDEO)
        assert len(result) == 2

    def test_on_duplicate_copy_has_copy_suffix_in_name(self, qapp, tmp_path):
        """複製ブックマークの name 末尾に「のコピー」が付くこと。"""
        store = make_store(tmp_path)
        bm = make_bm(a_ms=1000, b_ms=2000, name="original")
        store.add(VIDEO, bm)

        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        panel._on_duplicate(bm.id)

        result = store.get_bookmarks(VIDEO)
        copy_bm = next(b for b in result if b.id != bm.id)
        assert copy_bm.name == "original" + t("bookmark.copy_suffix")

    def test_on_duplicate_copy_inserted_after_original(self, qapp, tmp_path):
        """複製ブックマークが元の直後の order に挿入されること。"""
        store = make_store(tmp_path)
        bm1 = make_bm(a_ms=1000, b_ms=2000, name="first")
        bm2 = make_bm(a_ms=3000, b_ms=4000, name="second")
        store.add(VIDEO, bm1)
        store.add(VIDEO, bm2)

        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        panel._on_duplicate(bm1.id)

        result = store.get_bookmarks(VIDEO)
        assert len(result) == 3
        assert result[0].id == bm1.id
        # The copy should be at index 1 (directly after bm1)
        assert result[1].name == "first" + t("bookmark.copy_suffix")
        assert result[2].id == bm2.id

    def test_on_duplicate_resets_play_count(self, qapp, tmp_path):
        """複製ブックマークの play_count が 0 にリセットされること。"""
        store = make_store(tmp_path)
        bm = make_bm(a_ms=1000, b_ms=2000, name="played")
        store.add(VIDEO, bm)
        store.increment_play_count(VIDEO, bm.id)
        store.increment_play_count(VIDEO, bm.id)

        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        panel._on_duplicate(bm.id)

        result = store.get_bookmarks(VIDEO)
        copy_bm = next(b for b in result if b.id != bm.id)
        assert copy_bm.play_count == 0

    def test_on_duplicate_does_nothing_when_no_video(self, qapp, tmp_path):
        """動画未ロード時は _on_duplicate が何もしないこと。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)

        panel._on_duplicate("nonexistent-id")  # should not raise
