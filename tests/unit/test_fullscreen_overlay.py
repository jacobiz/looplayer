"""F-503: フルスクリーン中コントロールオーバーレイ ユニットテスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtCore import Qt, QEvent, QPointF
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
    widget.media_player.stop()


class TestOverlayTimerInit:
    """_overlay_hide_timer の初期化確認。"""

    def test_overlay_hide_timer_exists(self, player):
        """_overlay_hide_timer が VideoPlayer に存在する。"""
        assert hasattr(player, "_overlay_hide_timer")

    def test_overlay_hide_timer_is_single_shot(self, player):
        """タイマーは singleShot=True。"""
        assert player._overlay_hide_timer.isSingleShot()

    def test_overlay_hide_timer_interval_3000ms(self, player):
        """タイマー間隔は 3000ms。"""
        assert player._overlay_hide_timer.interval() == 3000


class TestEnterFullscreenOverlayMode:
    """_enter_fullscreen_overlay_mode(): controls_panel をレイアウトから外して絶対配置。"""

    def test_enter_overlay_mode_removes_panel_from_layout(self, player):
        """_enter_fullscreen_overlay_mode() を呼ぶと controls_panel がレイアウトから除去される。"""
        layout = player.centralWidget().layout()
        # 事前: controls_panel はレイアウト内にある
        assert layout.indexOf(player.controls_panel) >= 0
        player._enter_fullscreen_overlay_mode()
        # 事後: controls_panel はレイアウトから取り外されている
        assert layout.indexOf(player.controls_panel) == -1

    def test_enter_overlay_mode_hides_controls_panel(self, player):
        """_enter_fullscreen_overlay_mode() 後は controls_panel が非表示（hidden 状態）。"""
        player._enter_fullscreen_overlay_mode()
        assert player.controls_panel.isHidden()

    def test_enter_overlay_mode_controls_panel_parent_unchanged(self, player):
        """_enter_fullscreen_overlay_mode() 後も controls_panel の parent は player。"""
        player._enter_fullscreen_overlay_mode()
        assert player.controls_panel.parent() is player


class TestExitFullscreenOverlayMode:
    """_exit_fullscreen_overlay_mode(): controls_panel をレイアウトに戻す。"""

    def test_exit_overlay_mode_reinserts_panel_into_layout(self, player):
        """enter → exit で controls_panel がレイアウトに戻る。"""
        layout = player.centralWidget().layout()
        player._enter_fullscreen_overlay_mode()
        assert layout.indexOf(player.controls_panel) == -1
        player._exit_fullscreen_overlay_mode()
        assert layout.indexOf(player.controls_panel) >= 0

    def test_exit_overlay_mode_shows_controls_panel(self, player):
        """_exit_fullscreen_overlay_mode() 後は controls_panel が hidden でない。"""
        player._enter_fullscreen_overlay_mode()
        player._exit_fullscreen_overlay_mode()
        assert not player.controls_panel.isHidden()

    def test_exit_overlay_mode_stops_timer(self, player):
        """_exit_fullscreen_overlay_mode() で _overlay_hide_timer が停止する。"""
        player._overlay_hide_timer.start(3000)
        player._exit_fullscreen_overlay_mode()
        assert not player._overlay_hide_timer.isActive()


class TestMouseMoveOverlayTrigger:
    """mouseMoveEvent(): 画面下端10%でコントロールパネルを表示。"""

    def _make_mouse_event(self, x: int, y: int):
        """ダミーの mouseMoveEvent を作成する。"""
        return QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(x, y),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_mouse_in_bottom_10_percent_shows_controls(self, player):
        """フルスクリーン中に画面下端10%にマウスが入ると controls_panel が hidden でなくなる。"""
        player._enter_fullscreen_overlay_mode()
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "height", return_value=1080):
                # y=1000 > 1080 * 0.9 = 972 → 下端10%
                event = self._make_mouse_event(960, 1000)
                player.mouseMoveEvent(event)
        assert not player.controls_panel.isHidden()

    def test_mouse_outside_bottom_does_not_show_controls(self, player):
        """フルスクリーン中でも画面中央付近では controls_panel は hidden のまま。"""
        player._enter_fullscreen_overlay_mode()
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "height", return_value=1080):
                # y=500 < 1080 * 0.9 = 972 → 中央付近
                event = self._make_mouse_event(960, 500)
                player.mouseMoveEvent(event)
        assert player.controls_panel.isHidden()

    def test_overlay_timer_starts_when_controls_shown(self, player):
        """コントロールが表示されると _overlay_hide_timer が起動する。"""
        player._enter_fullscreen_overlay_mode()
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "height", return_value=1080):
                event = self._make_mouse_event(960, 1000)
                player.mouseMoveEvent(event)
        assert player._overlay_hide_timer.isActive()

    def test_overlay_timer_timeout_hides_controls(self, player, qtbot):
        """_overlay_hide_timer タイムアウトで controls_panel が非表示になる。"""
        player._enter_fullscreen_overlay_mode()
        player.controls_panel.show()
        # タイマーを直接 emit して即時テスト
        player._overlay_hide_timer.timeout.emit()
        assert not player.controls_panel.isVisible()


class TestCursorCoordination:
    """cursor hide との連動: controls_panel 表示中はカーソルを非表示にしない。"""

    def test_cursor_unset_when_overlay_visible(self, player):
        """controls_panel が shown (not hidden) のとき _hide_cursor() ではカーソルを非表示にしない。"""
        player._enter_fullscreen_overlay_mode()
        player.controls_panel.show()  # isHidden() == False
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "setCursor") as mock_set:
                player._hide_cursor()
                mock_set.assert_not_called()

    def test_cursor_hidden_when_overlay_not_visible(self, player):
        """controls_panel が hidden のとき _hide_cursor() でカーソルが非表示になる。"""
        player._enter_fullscreen_overlay_mode()
        # controls_panel は hide 状態 (isHidden() == True)
        assert player.controls_panel.isHidden()
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "setCursor") as mock_set:
                player._hide_cursor()
                mock_set.assert_called_once_with(Qt.CursorShape.BlankCursor)
