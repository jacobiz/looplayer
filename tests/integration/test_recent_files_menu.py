"""US2: 最近開いたファイル メニュー統合テスト。"""
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QMenu
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


class TestRecentMenuExists:
    """ファイルメニューに「最近開いたファイル」サブメニューが存在する。"""

    def test_recent_submenu_exists(self, player):
        file_menu = None
        for action in player.menuBar().actions():
            if "ファイル" in action.text():
                file_menu = action.menu()
                break
        assert file_menu is not None
        recent_menu = None
        for action in file_menu.actions():
            if action.menu() and "最近" in action.text():
                recent_menu = action.menu()
                break
        assert recent_menu is not None, "「最近開いたファイル」サブメニューが見つかりません"


class TestRecentMenuItems:
    """メニュー項目: ファイル名のみ表示・ツールチップにフルパス。"""

    def test_menu_shows_filename_only(self, player, tmp_path):
        video = tmp_path / "mytest.mp4"
        video.touch()
        with patch.object(player.media_player, "play"):
            with patch.object(player.media_player, "set_media"):
                player._open_path(str(video))
        recent_menu = _get_recent_menu(player)
        assert recent_menu is not None
        actions = [a for a in recent_menu.actions() if a.text()]
        assert len(actions) >= 1
        assert actions[0].text() == "mytest.mp4"

    def test_menu_tooltip_shows_full_path(self, player, tmp_path):
        video = tmp_path / "mytest.mp4"
        video.touch()
        with patch.object(player.media_player, "play"):
            with patch.object(player.media_player, "set_media"):
                player._open_path(str(video))
        recent_menu = _get_recent_menu(player)
        actions = [a for a in recent_menu.actions() if a.text()]
        assert str(video) in actions[0].toolTip()


class TestOpenRecentFile:
    """最近開いたファイルを選択すると _open_path が呼ばれる。"""

    def test_selecting_recent_calls_open_path(self, player, tmp_path):
        video = tmp_path / "test_recent.mp4"
        video.touch()
        with patch.object(player.media_player, "play"):
            with patch.object(player.media_player, "set_media"):
                player._open_path(str(video))
        recent_menu = _get_recent_menu(player)
        actions = [a for a in recent_menu.actions() if a.text()]
        assert len(actions) >= 1
        with patch.object(player, "_open_path") as mock_open:
            actions[0].trigger()
            mock_open.assert_called_once()


class TestMissingFileRemoval:
    """存在しないファイルを選択するとリストから削除される。"""

    def test_missing_file_removed_from_recent(self, player, tmp_path):
        video = tmp_path / "ghost.mp4"
        video.touch()
        with patch.object(player.media_player, "play"):
            with patch.object(player.media_player, "set_media"):
                player._open_path(str(video))
        # ファイルを削除して存在しない状態にする
        video.unlink()
        recent_menu = _get_recent_menu(player)
        actions = [a for a in recent_menu.actions() if a.text()]
        assert len(actions) >= 1
        # 選択時に削除される（QMessageBox をモック）
        with patch("looplayer.player.QMessageBox"):
            actions[0].trigger()
        recent_menu_after = _get_recent_menu(player)
        texts_after = [a.text() for a in recent_menu_after.actions() if a.text()]
        assert "ghost.mp4" not in texts_after


def _get_recent_menu(player: VideoPlayer):
    for action in player.menuBar().actions():
        if "ファイル" in action.text():
            file_menu = action.menu()
            if file_menu:
                for sub in file_menu.actions():
                    if sub.menu() and "最近" in sub.text():
                        return sub.menu()
    return None
