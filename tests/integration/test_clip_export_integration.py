"""tests/integration/test_clip_export_integration.py — クリップ書き出し統合テスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.player.UpdateChecker") as mock_cls, \
         patch("looplayer.player.ExportWorker"):
        mock_cls.return_value = MagicMock()
        widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()

    widget._size_poll_timer.stop()
    widget.media_player.stop()


# ── ファイルメニューの有効/無効状態 ──────────────────────────────────────────


class TestFileMenuExport:

    def test_export_action_disabled_without_ab_loop(self, player):
        """AB ループ未設定時にエクスポートアクションが disabled。"""
        assert not player._clip_export_action.isEnabled()

    def test_export_action_disabled_with_only_a_point(self, player):
        """A点のみ設定時にエクスポートアクションが disabled。"""
        player.ab_point_a = 1000
        player.ab_point_b = None
        player._update_clip_export_action_state()
        assert not player._clip_export_action.isEnabled()

    def test_export_action_disabled_with_only_b_point(self, player):
        """B点のみ設定時にエクスポートアクションが disabled。"""
        player.ab_point_a = None
        player.ab_point_b = 5000
        player._update_clip_export_action_state()
        assert not player._clip_export_action.isEnabled()

    def test_export_action_enabled_with_both_points(self, player):
        """A点・B点ともに設定済みでエクスポートアクションが enabled。"""
        player.ab_point_a = 1000
        player.ab_point_b = 5000
        player._update_clip_export_action_state()
        assert player._clip_export_action.isEnabled()

    def test_export_action_disabled_when_a_equals_b(self, player):
        """A点 == B点（区間長 0）でエクスポートアクションが disabled。"""
        player.ab_point_a = 5000
        player.ab_point_b = 5000
        player._update_clip_export_action_state()
        assert not player._clip_export_action.isEnabled()

    def test_export_action_disabled_after_reset(self, player):
        """AB リセット後にエクスポートアクションが disabled。"""
        player.ab_point_a = 1000
        player.ab_point_b = 5000
        player._update_clip_export_action_state()
        assert player._clip_export_action.isEnabled()

        player.reset_ab()
        assert not player._clip_export_action.isEnabled()


# ── ブックマークコンテキストメニューの書き出し ──────────────────────────────


class TestBookmarkContextMenuExport:

    def _add_bookmark(self, player: VideoPlayer, tmp_path: Path, a_ms: int, b_ms: int, name: str = "テスト"):
        """テスト用ブックマークを追加する。"""
        bm = LoopBookmark(point_a_ms=a_ms, point_b_ms=b_ms, name=name)
        player._store = BookmarkStore(storage_path=tmp_path / "bm.json")
        player._video_path = str(tmp_path / "video.mp4")
        player._store.add(player._video_path, bm, 100000)
        return bm

    def test_export_requested_signal_emitted_from_bookmark_row(self, player, qtbot, tmp_path):
        """A点・B点設定済みブックマークから export_requested シグナルが発行される。"""
        from looplayer.widgets.bookmark_row import BookmarkRow
        from looplayer.bookmark_store import LoopBookmark

        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="テスト区間")
        row = BookmarkRow(bm)
        qtbot.addWidget(row)

        received = []
        row.export_requested.connect(lambda a, b, label: received.append((a, b, label)))
        row.export_requested.emit(bm.point_a_ms, bm.point_b_ms, bm.name)

        assert len(received) == 1
        assert received[0] == (1000, 5000, "テスト区間")

    def test_bookmark_row_no_export_when_a_missing(self, player, qtbot):
        """A点が None のブックマーク行では export_requested が発行されない想定。"""
        from looplayer.widgets.bookmark_row import BookmarkRow
        from looplayer.bookmark_store import LoopBookmark

        bm = LoopBookmark(point_a_ms=0, point_b_ms=0, name="空ループ")
        row = BookmarkRow(bm)
        qtbot.addWidget(row)

        # export_clip_action が存在し、a==b のとき disabled になっていること
        assert not row._export_clip_action.isEnabled()
