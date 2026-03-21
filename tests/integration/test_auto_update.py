"""tests/integration/test_auto_update.py — 自動更新機能の統合テスト。"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.i18n import t
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    settings_path = tmp_path / "settings.json"
    with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
        widget = VideoPlayer(store=store)
        qtbot.addWidget(widget)
        widget.show()
        yield widget
        widget.timer.stop()

        widget._size_poll_timer.stop()
        widget.media_player.stop()


# ── T008/T009: US1 起動時チェック ────────────────────────────────────────────


class TestStartupUpdateCheck:
    def test_update_checker_starts_when_enabled(self, qtbot, tmp_path):
        """check_update_on_startup=True の場合 UpdateChecker が起動する（1回のみ）。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"check_update_on_startup": true}')

        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path), \
             patch("looplayer.player.UpdateChecker") as MockChecker:
            mock_instance = MagicMock()
            MockChecker.return_value = mock_instance
            widget = VideoPlayer(store=store)
            qtbot.addWidget(widget)
            widget.show()
            widget.timer.stop()

            widget._size_poll_timer.stop()
            widget.media_player.stop()

        # UpdateChecker が 1 回だけ起動されたことを確認（SC-005: 同一セッション中再通知なし）
        MockChecker.assert_called_once()
        mock_instance.start.assert_called_once()

    def test_update_checker_skipped_when_disabled(self, qtbot, tmp_path):
        """check_update_on_startup=False の場合 UpdateChecker が起動しない。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"check_update_on_startup": false}')

        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path), \
             patch("looplayer.player.UpdateChecker") as MockChecker:
            widget = VideoPlayer(store=store)
            qtbot.addWidget(widget)
            widget.show()
            widget.timer.stop()

            widget._size_poll_timer.stop()
            widget.media_player.stop()

        MockChecker.assert_not_called()


# ── T014/T015: US2 手動確認メニュー ──────────────────────────────────────────


class TestManualUpdateCheck:
    def _get_help_menu(self, player):
        help_title = t("menu.help").replace("&", "")
        for action in player.menuBar().actions():
            if help_title in action.text().replace("&", ""):
                return action.menu()
        return None

    def test_check_update_menu_item_exists(self, player):
        """ヘルプメニューに「更新を確認...」項目が存在する。"""
        menu = self._get_help_menu(player)
        assert menu is not None
        expected = t("menu.help.check_update").replace("&", "")
        texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
        assert any(expected in txt for txt in texts)

    def test_check_failed_shows_error_dialog(self, player, qtbot):
        """手動確認でネットワークエラー時にエラーダイアログが表示される。"""
        with patch("looplayer.player.UpdateChecker") as MockChecker, \
             patch("looplayer.player.QMessageBox.warning") as mock_warn:
            mock_instance = MagicMock()
            MockChecker.return_value = mock_instance

            # _check_for_updates_manually を呼び出してエラーシグナルを発行
            player._check_for_updates_manually()
            # check_failed シグナルのスロットを直接呼び出す
            player._on_check_failed("network error")

        mock_warn.assert_called_once()


# ── T018/T019: US3 起動時チェック ON/OFF 設定 ────────────────────────────────


class TestAutoCheckSetting:
    def _get_help_menu(self, player):
        help_title = t("menu.help").replace("&", "")
        for action in player.menuBar().actions():
            if help_title in action.text().replace("&", ""):
                return action.menu()
        return None

    def test_auto_check_menu_item_exists(self, player):
        """ヘルプメニューに「起動時に更新を確認する」チェック付き項目が存在する。"""
        menu = self._get_help_menu(player)
        assert menu is not None
        expected = t("menu.help.auto_check").replace("&", "")
        actions = [a for a in menu.actions() if not a.isSeparator()]
        auto_check_action = next(
            (a for a in actions if expected in a.text().replace("&", "")), None
        )
        assert auto_check_action is not None
        assert auto_check_action.isCheckable()

    def test_toggle_saves_false_to_settings(self, qtbot, tmp_path):
        """チェックを外すと AppSettings.check_update_on_startup が False に保存される。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"check_update_on_startup": true}')

        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            widget = VideoPlayer(store=store)
            qtbot.addWidget(widget)
            widget.show()
            widget._toggle_auto_check(False)
            widget.timer.stop()

            widget._size_poll_timer.stop()
            widget.media_player.stop()

        import json
        data = json.loads(settings_path.read_text())
        assert data["check_update_on_startup"] is False
