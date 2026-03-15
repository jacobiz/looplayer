"""US5: ブックマーク削除 Undo ユニットテスト。"""
from pathlib import Path
from unittest.mock import patch

import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.widgets.bookmark_panel import BookmarkPanel


@pytest.fixture
def store(tmp_path: Path) -> BookmarkStore:
    return BookmarkStore(storage_path=tmp_path / "bookmarks.json")


@pytest.fixture
def panel(qtbot: QtBot, store: BookmarkStore) -> BookmarkPanel:
    widget = BookmarkPanel(store)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def video_path(tmp_path: Path) -> str:
    v = tmp_path / "test.mp4"
    v.touch()
    return str(v)


@pytest.fixture
def panel_with_bookmarks(panel, store, video_path):
    """動画をロードし、ブックマークを2件追加したパネル。"""
    panel.load_video(video_path)
    bm1 = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="ブックマーク1", order=0)
    bm2 = LoopBookmark(point_a_ms=6000, point_b_ms=10000, name="ブックマーク2", order=1)
    store.add(video_path, bm1)
    store.add(video_path, bm2)
    panel._refresh_list()
    return panel, bm1, bm2, video_path


class TestPendingDeleteOnDelete:
    """_on_delete(): 即時削除せず _pending_delete に保留する。"""

    def test_delete_sets_pending(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        assert panel._pending_delete is not None

    def test_delete_stores_bookmark_in_pending(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        assert panel._pending_delete["bookmark"].id == bm1.id

    def test_delete_stores_order_snapshot(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        # 削除前の全ID順序がスナップショットとして保存されている
        assert "order_snapshot" in panel._pending_delete
        assert bm1.id in panel._pending_delete["order_snapshot"]

    def test_delete_starts_undo_timer(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        assert panel._undo_timer.isActive()
        panel._undo_timer.stop()


class TestUndoDelete:
    """_undo_delete(): タイマー内に Undo で全属性込み復元。"""

    def test_undo_restores_bookmark(self, panel_with_bookmarks, store):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._undo_delete()
        bms = store.get_bookmarks(video_path)
        ids = [bm.id for bm in bms]
        assert bm1.id in ids

    def test_undo_when_no_pending_is_noop(self, panel):
        """_pending_delete が None のときは何もしない。"""
        panel._undo_delete()  # エラーにならないこと

    def test_undo_stops_timer(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._undo_delete()
        assert not panel._undo_timer.isActive()

    def test_undo_clears_pending(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._undo_delete()
        assert panel._pending_delete is None


class TestCommitDelete:
    """_commit_delete(): タイマー発火後の確定削除。"""

    def test_commit_clears_pending(self, panel_with_bookmarks):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._commit_delete()
        assert panel._pending_delete is None

    def test_commit_after_timer_bookmark_stays_deleted(self, panel_with_bookmarks, store):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._commit_delete()
        bms = store.get_bookmarks(video_path)
        ids = [bm.id for bm in bms]
        assert bm1.id not in ids


class TestConsecutiveDelete:
    """連続削除: 前の保留を確定してから新しい保留をセット。"""

    def test_second_delete_commits_first(self, panel_with_bookmarks, store):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        panel._on_delete(bm2.id)
        # 最初の削除はコミットされ復元不可
        bms = store.get_bookmarks(video_path)
        ids = [bm.id for bm in bms]
        assert bm1.id not in ids
        assert panel._pending_delete["bookmark"].id == bm2.id
        panel._undo_timer.stop()


class TestVideoSwitchClearsPending:
    """動画切替時に保留をコミット（クリア）する。"""

    def test_load_video_commits_pending(self, panel_with_bookmarks, store, tmp_path):
        panel, bm1, bm2, video_path = panel_with_bookmarks
        panel._on_delete(bm1.id)
        # 別の動画をロード
        new_video = tmp_path / "other.mp4"
        new_video.touch()
        panel.load_video(str(new_video))
        assert panel._pending_delete is None
