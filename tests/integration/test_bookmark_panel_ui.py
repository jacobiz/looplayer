"""021: ブックマークサイドパネル UI 統合テスト。"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pytestqt.qtbot import QtBot
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QCloseEvent

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
            widget.show()
            qtbot.waitExposed(widget)
            yield widget
            widget.timer.stop()
            widget._size_poll_timer.stop()
            # VLC メソッドをパッチして二重解放によるクラッシュを防ぐ
            with patch.object(widget.media_player, "stop"), \
                 patch.object(widget.media_player, "release"), \
                 patch.object(widget.instance, "release"):
                widget.close()


# ── US1: 表示・非表示切り替え ────────────────────────────────────────────

class TestPanelInitialState:
    def test_panel_hidden_on_startup(self, player):
        """起動直後はパネルが非表示。"""
        assert player._panel_tabs.isVisible() is False


class TestPanelToggleKey:
    def test_b_key_shortcut_is_registered(self, player):
        """B キーショートカットがアクションに設定されている。"""
        from PyQt6.QtGui import QKeySequence
        assert player._bookmark_panel_action.shortcut() == QKeySequence("B")

    def test_b_key_shows_panel(self, player, qtbot):
        """B キー相当のアクション実行でパネルが表示される。"""
        assert player._panel_tabs.isVisible() is False
        player._bookmark_panel_action.trigger()
        assert player._panel_tabs.isVisible() is True

    def test_b_key_hides_panel(self, player, qtbot):
        """パネル表示中にアクション実行で非表示になる。"""
        player._bookmark_panel_action.trigger()  # show
        assert player._panel_tabs.isVisible() is True
        player._bookmark_panel_action.trigger()  # hide
        assert player._panel_tabs.isVisible() is False


class TestPanelMenuAction:
    def test_menu_action_shows_panel(self, player):
        """メニューアクション triggered でパネルが表示される。"""
        assert player._panel_tabs.isVisible() is False
        player._bookmark_panel_action.trigger()
        assert player._panel_tabs.isVisible() is True

    def test_menu_action_hides_panel(self, player):
        """パネル表示中にメニューアクション triggered で非表示になる。"""
        player._panel_tabs.show()
        player._app_settings.bookmark_panel_visible = True
        player._bookmark_panel_action.setChecked(True)
        player._bookmark_panel_action.trigger()
        assert player._panel_tabs.isVisible() is False

    def test_menu_checkmark_syncs_with_panel(self, player):
        """パネル表示中はメニューにチェックマークが付く。"""
        player._bookmark_panel_action.trigger()
        assert player._bookmark_panel_action.isChecked() is True

        player._bookmark_panel_action.trigger()
        assert player._bookmark_panel_action.isChecked() is False


class TestControlsAlwaysVisible:
    def test_controls_visible_when_panel_shown(self, player):
        """パネル表示中も再生コントロールが表示されている（FR-009）。"""
        player._bookmark_panel_action.trigger()
        assert player.controls_panel.isVisible() is True

    def test_controls_visible_when_panel_hidden(self, player):
        """パネル非表示でも再生コントロールが表示されている（FR-009）。"""
        assert player.controls_panel.isVisible() is True


class TestMinimumPanelWidth:
    def test_panel_minimum_width_is_240(self, player):
        """パネルの最小幅が 240px（EC-2）。"""
        player._bookmark_panel_action.trigger()
        assert player._panel_tabs.minimumWidth() == 240


# ── US2: 幅の永続化 ─────────────────────────────────────────────────────

class TestPanelWidthPersistence:
    def test_width_saved_on_hide(self, player, qtbot):
        """パネル非表示化時に幅が AppSettings に保存される。"""
        player._bookmark_panel_action.trigger()  # show
        qtbot.waitExposed(player._panel_tabs)
        sizes = player._splitter.sizes()
        if len(sizes) >= 2 and sizes[1] > 0:
            original_width = sizes[1]
        else:
            original_width = None

        player._bookmark_panel_action.trigger()  # hide
        if original_width is not None:
            assert player._app_settings.bookmark_panel_width == original_width

    def test_width_saved_on_close(self, player, qtbot):
        """closeEvent でパネルが表示中なら幅が AppSettings に保存される。"""
        player._bookmark_panel_action.trigger()  # show
        qtbot.waitExposed(player._panel_tabs)
        # VLC cleanup をパッチして二重解放を防ぐ
        with patch.object(player.media_player, 'stop'), \
             patch.object(player.media_player, 'release'), \
             patch.object(player.instance, 'release'), \
             patch.object(player, '_playback_position'):
            event = QCloseEvent()
            player.closeEvent(event)
        # 幅が有効な値であること
        assert player._app_settings.bookmark_panel_width >= 240

    def test_width_not_changed_on_close_when_hidden(self, player):
        """closeEvent でパネルが非表示なら幅は変更されない。"""
        player._app_settings.bookmark_panel_width = 350
        player._app_settings.save()
        assert player._panel_tabs.isVisible() is False
        with patch.object(player.media_player, 'stop'), \
             patch.object(player.media_player, 'release'), \
             patch.object(player.instance, 'release'), \
             patch.object(player, '_playback_position'):
            event = QCloseEvent()
            player.closeEvent(event)
        assert player._app_settings.bookmark_panel_width == 350

    def test_stored_width_restored_on_show(self, player, qtbot):
        """AppSettings に幅 350px が設定されている場合、パネル表示後にその幅になる。"""
        player._app_settings.bookmark_panel_width = 350
        player._bookmark_panel_action.trigger()  # show
        qtbot.waitExposed(player._panel_tabs)
        sizes = player._splitter.sizes()
        if len(sizes) >= 2:
            assert sizes[1] == 350


# ── US3: フルスクリーン連動 ──────────────────────────────────────────────

class TestFullscreenPanelControl:
    def test_panel_hidden_on_fullscreen_enter(self, player):
        """フルスクリーン移行でパネルが非表示になる。"""
        player._bookmark_panel_action.trigger()  # show
        assert player._panel_tabs.isVisible() is True
        player.toggle_fullscreen()
        assert player._panel_tabs.isVisible() is False
        player.toggle_fullscreen()  # cleanup

    def test_panel_restored_on_fullscreen_exit(self, player):
        """フルスクリーン解除後にパネルが復元される（元々表示中だった場合）。"""
        player._bookmark_panel_action.trigger()  # show
        player.toggle_fullscreen()
        player.toggle_fullscreen()
        assert player._panel_tabs.isVisible() is True

    def test_panel_stays_hidden_after_fullscreen(self, player):
        """パネル非表示でフルスクリーン切り替えしても非表示のまま。"""
        assert player._panel_tabs.isVisible() is False
        player.toggle_fullscreen()
        player.toggle_fullscreen()
        assert player._panel_tabs.isVisible() is False
