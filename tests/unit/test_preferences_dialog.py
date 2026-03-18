"""F-401: 設定画面（PreferencesDialog）ユニットテスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtWidgets import QDialog, QTabWidget, QComboBox, QCheckBox, QDialogButtonBox
from pytestqt.qtbot import QtBot

from looplayer.app_settings import AppSettings
from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    s = AppSettings.__new__(AppSettings)
    s._data = {}
    s.save = MagicMock()
    return s


@pytest.fixture
def dialog(qtbot: QtBot, settings: AppSettings):
    from looplayer.widgets.preferences_dialog import PreferencesDialog
    d = PreferencesDialog(settings=settings)
    qtbot.addWidget(d)
    return d


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


class TestPreferencesDialogInit:
    """ダイアログ初期化: AppSettings の現在値がウィジェットに反映される。"""

    def test_dialog_is_qdialog(self, dialog):
        """PreferencesDialog は QDialog のサブクラス。"""
        assert isinstance(dialog, QDialog)

    def test_dialog_has_tab_widget(self, dialog):
        """ダイアログに QTabWidget が含まれる。"""
        tab = dialog.findChild(QTabWidget)
        assert tab is not None

    def test_dialog_has_3_tabs(self, dialog):
        """タブが 3 枚（再生/表示/アップデート）ある。"""
        tab = dialog.findChild(QTabWidget)
        assert tab.count() == 3

    def test_dialog_loads_end_of_playback_action(self, settings, qtbot):
        """ダイアログ開時に end_of_playback_action の現在値が反映される。"""
        settings._data["end_of_playback_action"] = "loop"
        from looplayer.widgets.preferences_dialog import PreferencesDialog
        d = PreferencesDialog(settings=settings)
        qtbot.addWidget(d)
        combo = d._end_action_combo
        # "loop" が選択されているはず
        assert "loop" in combo.currentData() or "loop" in combo.currentText().lower() or combo.currentIndex() == 2

    def test_dialog_loads_check_update_on_startup(self, settings, qtbot):
        """ダイアログ開時に check_update_on_startup の現在値が反映される。"""
        settings._data["check_update_on_startup"] = False
        from looplayer.widgets.preferences_dialog import PreferencesDialog
        d = PreferencesDialog(settings=settings)
        qtbot.addWidget(d)
        assert not d._check_update_checkbox.isChecked()


class TestPreferencesDialogOK:
    """OK ボタン: 変更が AppSettings に保存される。"""

    def test_ok_saves_end_of_playback_action(self, dialog, settings):
        """OK 時に end_of_playback_action が settings に書き込まれる。"""
        # "rewind"(index=1) に変更
        dialog._end_action_combo.setCurrentIndex(1)
        dialog.accept()
        assert settings._data.get("end_of_playback_action") == "rewind"

    def test_ok_saves_sequential_play_mode(self, dialog, settings):
        """OK 時に sequential_play_mode が settings に書き込まれる。"""
        dialog._seq_mode_combo.setCurrentIndex(1)  # one_round
        dialog.accept()
        assert settings._data.get("sequential_play_mode") == "one_round"

    def test_ok_saves_export_encode_mode(self, dialog, settings):
        """OK 時に export_encode_mode が settings に書き込まれる。"""
        dialog._encode_mode_combo.setCurrentIndex(1)  # transcode
        dialog.accept()
        assert settings._data.get("export_encode_mode") == "transcode"

    def test_ok_saves_check_update_on_startup(self, dialog, settings):
        """OK 時に check_update_on_startup が settings に書き込まれる。"""
        dialog._check_update_checkbox.setChecked(False)
        dialog.accept()
        assert settings._data.get("check_update_on_startup") is False

    def test_ok_calls_save(self, dialog, settings):
        """OK 時に settings.save() が呼ばれる。"""
        dialog.accept()
        settings.save.assert_called()


class TestPreferencesDialogCancel:
    """Cancel ボタン: 変更が AppSettings に書き込まれない。"""

    def test_cancel_does_not_modify_settings(self, dialog, settings):
        """Cancel で settings._data が変更されない。"""
        original_data = dict(settings._data)
        dialog._end_action_combo.setCurrentIndex(2)  # "loop" に変更
        dialog.reject()
        assert settings._data == original_data

    def test_cancel_does_not_call_save(self, dialog, settings):
        """Cancel で settings.save() が呼ばれない。"""
        settings.save.reset_mock()
        dialog.reject()
        settings.save.assert_not_called()


class TestPreferencesMenuAction:
    """「ファイル > 設定...」メニューアクション。"""

    def test_preferences_menu_action_exists_in_file_menu(self, player):
        """ファイルメニューに「設定...」アクションが存在する。"""
        file_menu = player.menuBar().actions()[0].menu()
        action_texts = [a.text() for a in file_menu.actions()]
        assert any("設定" in text or "Preferences" in text for text in action_texts)
