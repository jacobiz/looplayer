"""021: ブックマークパネルトグルロジックのユニットテスト（T010）。"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
        with patch("looplayer.player.UpdateChecker") as mock_checker_cls:
            mock_checker_cls.return_value = MagicMock()
            widget = VideoPlayer(store=store)
            qtbot.addWidget(widget)
            yield widget
            widget.timer.stop()
            widget._size_poll_timer.stop()
            widget.media_player.stop()


class TestToggleBookmarkPanel:
    """_toggle_bookmark_panel() のロジックテスト。"""

    def test_toggle_shows_panel(self, player):
        """パネル非表示状態でトグルするとパネルが表示される（isHidden で検証）。"""
        player._panel_tabs.hide()
        player._toggle_bookmark_panel()
        assert player._panel_tabs.isHidden() is False

    def test_toggle_hides_panel(self, player):
        """パネル表示状態でトグルするとパネルが非表示になる（isHidden で検証）。"""
        player._panel_tabs.show()
        player._toggle_bookmark_panel()
        assert player._panel_tabs.isHidden() is True

    def test_toggle_updates_visible_false(self, player):
        """非表示化時に AppSettings.bookmark_panel_visible が False になる。"""
        player._panel_tabs.show()
        player._toggle_bookmark_panel()
        assert player._app_settings.bookmark_panel_visible is False

    def test_toggle_updates_visible_true(self, player):
        """表示化時に AppSettings.bookmark_panel_visible が True になる。"""
        player._panel_tabs.hide()
        player._toggle_bookmark_panel()
        assert player._app_settings.bookmark_panel_visible is True

    def test_action_checked_syncs_with_visibility(self, player):
        """_bookmark_panel_action.isChecked() がパネルの表示状態と同期する。"""
        player._panel_tabs.hide()
        player._toggle_bookmark_panel()
        assert player._bookmark_panel_action.isChecked() is True

        # 再度 hide してから toggle → hide になる
        player._panel_tabs.show()
        player._toggle_bookmark_panel()
        assert player._bookmark_panel_action.isChecked() is False
