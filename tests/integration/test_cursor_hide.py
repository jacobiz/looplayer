"""US4: フルスクリーン中カーソル自動非表示 統合テスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()

    widget._size_poll_timer.stop()
    widget.media_player.stop()


class TestCursorHideTimer:
    """_cursor_hide_timer: 初期化・フルスクリーン中の動作確認。"""

    def test_cursor_hide_timer_exists(self, player):
        """_cursor_hide_timer が初期化されている。"""
        assert hasattr(player, "_cursor_hide_timer")

    def test_cursor_hide_timer_is_single_shot(self, player):
        """タイマーは singleShot=True。"""
        assert player._cursor_hide_timer.isSingleShot()

    def test_cursor_hide_timer_interval_3000ms(self, player):
        """タイマー間隔は 3000ms。"""
        assert player._cursor_hide_timer.interval() == 3000


class TestHideCursor:
    """_hide_cursor(): フルスクリーン時のみ BlankCursor をセット。"""

    def test_sets_blank_cursor_in_fullscreen(self, player):
        """フルスクリーン中に _hide_cursor() を呼ぶと BlankCursor がセットされる。"""
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "setCursor") as mock_set:
                player._hide_cursor()
                mock_set.assert_called_once_with(Qt.CursorShape.BlankCursor)

    def test_does_not_hide_cursor_when_not_fullscreen(self, player):
        """通常ウィンドウでは _hide_cursor() を呼んでも setCursor は呼ばれない。"""
        with patch.object(player, "isFullScreen", return_value=False):
            with patch.object(player, "setCursor") as mock_set:
                player._hide_cursor()
                mock_set.assert_not_called()


class TestShowCursor:
    """_show_cursor() または mouseMoveEvent(): フルスクリーン時にカーソルを復元。"""

    def test_mouse_move_in_fullscreen_unsets_cursor(self, player):
        """フルスクリーン中のマウス移動で unsetCursor が呼ばれる。"""
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "unsetCursor") as mock_unset:
                from PyQt6.QtCore import QPointF
                event = QMouseEvent(
                    QEvent.Type.MouseMove,
                    QPointF(100, 100),
                    Qt.MouseButton.NoButton,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                player.mouseMoveEvent(event)
                mock_unset.assert_called()

    def test_mouse_move_in_fullscreen_restarts_timer(self, player):
        """フルスクリーン中のマウス移動でタイマーが再起動される。"""
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player._cursor_hide_timer, "start") as mock_start:
                from PyQt6.QtCore import QPointF
                event = QMouseEvent(
                    QEvent.Type.MouseMove,
                    QPointF(100, 100),
                    Qt.MouseButton.NoButton,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                player.mouseMoveEvent(event)
                mock_start.assert_called()

    def test_mouse_move_outside_fullscreen_no_unset(self, player):
        """通常ウィンドウでのマウス移動では unsetCursor は呼ばれない。"""
        with patch.object(player, "isFullScreen", return_value=False):
            with patch.object(player, "unsetCursor") as mock_unset:
                from PyQt6.QtCore import QPointF
                event = QMouseEvent(
                    QEvent.Type.MouseMove,
                    QPointF(100, 200),
                    Qt.MouseButton.NoButton,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                player.mouseMoveEvent(event)
                mock_unset.assert_not_called()


class TestFullscreenToggle:
    """toggle_fullscreen/exit_fullscreen: タイマー連携。"""

    def test_toggle_fullscreen_starts_cursor_timer(self, player):
        """通常→フルスクリーン遷移でカーソル非表示タイマーが起動する。"""
        with patch.object(player, "isFullScreen", return_value=False):
            with patch.object(player, "showFullScreen"):
                with patch.object(player._cursor_hide_timer, "start") as mock_start:
                    player.toggle_fullscreen()
                    mock_start.assert_called()

    def test_exit_fullscreen_stops_cursor_timer(self, player):
        """フルスクリーン解除でタイマーが停止し unsetCursor が呼ばれる。"""
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "showNormal"):
                with patch.object(player._cursor_hide_timer, "stop") as mock_stop:
                    with patch.object(player, "unsetCursor") as mock_unset:
                        player._exit_fullscreen()
                        mock_stop.assert_called()
                        mock_unset.assert_called()
