"""メニュー・ショートカット統合テスト（US1）。"""
import pytest
from unittest.mock import patch, MagicMock
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QMenuBar
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore
from looplayer.i18n import t
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


class TestMenuBarExists:
    def test_menubar_exists(self, player):
        assert player.menuBar() is not None

    def test_file_menu_exists(self, player):
        menus = [a.text() for a in player.menuBar().actions()]
        assert any(t("menu.file").replace("&", "") in m.replace("&", "") for m in menus)

    def test_play_menu_exists(self, player):
        menus = [a.text() for a in player.menuBar().actions()]
        assert any(t("menu.playback").replace("&", "") in m.replace("&", "") for m in menus)

    def test_view_menu_exists(self, player):
        menus = [a.text() for a in player.menuBar().actions()]
        assert any(t("menu.view").replace("&", "") in m.replace("&", "") for m in menus)


class TestFileMenuActions:
    def _get_file_menu(self, player):
        file_title = t("menu.file").replace("&", "")
        for action in player.menuBar().actions():
            if file_title in action.text().replace("&", ""):
                return action.menu()
        return None

    def _get_all_actions(self, player):
        """全メニューの全アクションをフラットに返す。"""
        actions = []
        for menu_action in player.menuBar().actions():
            if menu_action.menu():
                actions.extend(menu_action.menu().actions())
        return actions

    def test_open_action_exists(self, player):
        menu = self._get_file_menu(player)
        assert menu is not None
        open_text = t("menu.file.open").replace("&", "")
        action_texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
        assert any(open_text in txt for txt in action_texts)

    def test_quit_action_exists(self, player):
        menu = self._get_file_menu(player)
        assert menu is not None
        quit_text = t("menu.file.quit").replace("&", "")
        action_texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
        assert any(quit_text in txt for txt in action_texts)

    def test_open_action_has_ctrl_o_shortcut(self, player):
        """Ctrl+O ショートカットが開くアクションに設定されていることを確認。"""
        actions = self._get_all_actions(player)
        open_text = t("menu.file.open").replace("&", "")
        open_action = next((a for a in actions if open_text in a.text().replace("&", "") and not a.isSeparator()), None)
        assert open_action is not None
        assert open_action.shortcut().toString() == "Ctrl+O"

    def test_ctrl_o_triggers_open_file(self, player, qtbot):
        """開くアクションを直接トリガーしてダイアログが呼ばれることを確認。"""
        with patch("looplayer.player.QFileDialog.getOpenFileName", return_value=("", "")) as mock_dialog:
            # アクションを直接トリガー
            actions = self._get_all_actions(player)
            open_text = t("menu.file.open").replace("&", "")
            open_action = next((a for a in actions if open_text in a.text().replace("&", "") and not a.isSeparator()), None)
            assert open_action is not None
            open_action.trigger()
            mock_dialog.assert_called_once()


class TestPlaybackShortcuts:
    def test_space_shortcut_connected_to_toggle_play(self, player):
        """Space ショートカットが再生/一時停止に接続されていることを確認。"""
        from PyQt6.QtGui import QKeySequence
        all_actions = []
        for menu_action in player.menuBar().actions():
            if menu_action.menu():
                all_actions.extend(menu_action.menu().actions())
        space_action = next((a for a in all_actions
                             if a.shortcut().toString() == "Space"), None)
        assert space_action is not None

    def test_left_arrow_action_exists(self, player):
        """←キーのアクションが存在することを確認。"""
        from PyQt6.QtGui import QKeySequence
        all_actions = list(player.actions())
        for menu_action in player.menuBar().actions():
            if menu_action.menu():
                all_actions.extend(menu_action.menu().actions())
        left_action = next((a for a in all_actions
                            if a.shortcut().toString() == "Left"), None)
        assert left_action is not None

    def test_right_arrow_action_exists(self, player):
        """→キーのアクションが存在することを確認。"""
        all_actions = list(player.actions())
        for menu_action in player.menuBar().actions():
            if menu_action.menu():
                all_actions.extend(menu_action.menu().actions())
        right_action = next((a for a in all_actions
                             if a.shortcut().toString() == "Right"), None)
        assert right_action is not None

    def test_seek_relative_backward(self, player):
        """_seek_relative(-5000) が左矢印アクションから呼ばれることを確認。"""
        all_actions = list(player.actions())
        left_action = next((a for a in all_actions
                            if a.shortcut().toString() == "Left"), None)
        assert left_action is not None
        with patch.object(player, "_seek_relative") as mock_seek:
            left_action.trigger()
            mock_seek.assert_called_once_with(-5000)

    def test_seek_relative_forward(self, player):
        """_seek_relative(5000) が右矢印アクションから呼ばれることを確認。"""
        all_actions = list(player.actions())
        right_action = next((a for a in all_actions
                             if a.shortcut().toString() == "Right"), None)
        assert right_action is not None
        with patch.object(player, "_seek_relative") as mock_seek:
            right_action.trigger()
            mock_seek.assert_called_once_with(5000)
