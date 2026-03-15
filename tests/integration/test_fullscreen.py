"""フルスクリーン統合テスト（US3）。"""
import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    widget.show()
    yield widget
    widget.timer.stop()
    widget.media_player.stop()
    # フルスクリーンを確実に解除してからクリーンアップ
    if widget.isFullScreen():
        widget.showNormal()


class TestToggleFullscreen:
    def test_toggle_fullscreen_enters_fullscreen(self, player, qtbot):
        assert not player.isFullScreen()
        player.toggle_fullscreen()
        assert player.isFullScreen()

    def test_toggle_fullscreen_exits_fullscreen(self, player, qtbot):
        player.toggle_fullscreen()  # enter
        player.toggle_fullscreen()  # exit
        assert not player.isFullScreen()

    def test_controls_panel_hidden_in_fullscreen(self, player, qtbot):
        player.toggle_fullscreen()
        assert not player.controls_panel.isVisible()

    def test_controls_panel_shown_after_exit(self, player, qtbot):
        player.toggle_fullscreen()
        player.toggle_fullscreen()
        assert player.controls_panel.isVisible()

    def test_menubar_hidden_in_fullscreen(self, player, qtbot):
        player.toggle_fullscreen()
        assert not player.menuBar().isVisible()

    def test_menubar_shown_after_exit(self, player, qtbot):
        player.toggle_fullscreen()
        player.toggle_fullscreen()
        assert player.menuBar().isVisible()


class TestEscapeExitsFullscreen:
    def test_esc_exits_fullscreen(self, player, qtbot):
        player.toggle_fullscreen()
        assert player.isFullScreen()
        # Escape アクションを直接トリガー（ApplicationShortcut は QTest.keyClick では動作しない）
        esc_action = None
        for menu_action in player.menuBar().actions():
            if menu_action.menu():
                for sub in menu_action.menu().actions():
                    if sub.shortcut().toString() in ("Esc", "Escape"):
                        esc_action = sub
                        break
        assert esc_action is not None, "Esc ショートカットが表示メニューに存在しない"
        esc_action.trigger()
        assert not player.isFullScreen()


class TestABLoopPreservedInFullscreen:
    def test_ab_loop_state_preserved_through_fullscreen(self, player, qtbot):
        player.ab_point_a = 1000
        player.ab_point_b = 5000
        player.ab_loop_active = True
        player.toggle_fullscreen()
        player.toggle_fullscreen()
        assert player.ab_point_a == 1000
        assert player.ab_point_b == 5000
        assert player.ab_loop_active is True
