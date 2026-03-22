"""021: AppSettings ブックマークパネルフィールドのユニットテスト（T004）。"""
import json
import pytest
from unittest.mock import patch


class TestBookmarkPanelVisible:
    """bookmark_panel_visible プロパティのテスト。"""

    def test_default_is_false(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.bookmark_panel_visible is False

    def test_setter_updates_value(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_visible = True
            assert s.bookmark_panel_visible is True

    def test_setter_false(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_visible = True
            s.bookmark_panel_visible = False
            assert s.bookmark_panel_visible is False

    def test_persistence_after_save_and_reload(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_visible = True
            s.save()
            s2 = AppSettings()
            assert s2.bookmark_panel_visible is True


class TestBookmarkPanelWidth:
    """bookmark_panel_width プロパティのテスト。"""

    def test_default_is_280(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.bookmark_panel_width == 280

    def test_setter_stores_valid_value(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 300
            assert s.bookmark_panel_width == 300

    def test_setter_clamps_below_240(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 100
            assert s.bookmark_panel_width == 240

    def test_setter_clamps_zero(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 0
            assert s.bookmark_panel_width == 240

    def test_setter_exact_minimum(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 240
            assert s.bookmark_panel_width == 240

    def test_setter_above_240_stored_as_is(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 350
            assert s.bookmark_panel_width == 350

    def test_persistence_after_save_and_reload(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.bookmark_panel_width = 350
            s.save()
            s2 = AppSettings()
            assert s2.bookmark_panel_width == 350
