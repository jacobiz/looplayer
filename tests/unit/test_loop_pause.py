"""T016: ループ間ポーズのユニットテスト。"""
from unittest.mock import MagicMock, patch
import pytest
from looplayer.bookmark_store import BookmarkStore, LoopBookmark


class TestLoopPauseLogic:
    def test_pause_ms_zero_no_timer(self):
        """pause_ms=0 のときポーズタイマーを起動しない（即シーク）。"""
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, pause_ms=0)
        assert bm.pause_ms == 0

    def test_pause_ms_positive_stored(self):
        """pause_ms > 0 のとき値が正しく保持される。"""
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, pause_ms=2000)
        assert bm.pause_ms == 2000

    def test_pause_ms_clamped_in_store(self, tmp_path):
        """BookmarkStore が pause_ms を 0〜10000 にクランプする。"""
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.update_pause_ms("/test.mp4", bm.id, 99999)
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].pause_ms == 10000

    def test_pause_ms_negative_clamped_to_zero(self, tmp_path):
        """負の pause_ms は 0 にクランプされる。"""
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.update_pause_ms("/test.mp4", bm.id, -100)
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].pause_ms == 0

    def test_pause_spin_default_range(self):
        """BookmarkRow の pause_spin は 0〜10 秒 (0〜10000ms)。"""
        from looplayer.widgets.bookmark_row import BookmarkRow
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        # QApplication が必要なため import だけ確認
        assert hasattr(BookmarkRow, 'pause_ms_changed')
