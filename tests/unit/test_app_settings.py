"""T015: AppSettings のユニットテスト（US4）。"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


class TestAppSettingsDefaults:
    def test_default_end_of_playback_action_is_stop(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.end_of_playback_action == "stop"

    def test_invalid_value_in_json_falls_back_to_stop(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"end_of_playback_action": "invalid_value"}))
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.end_of_playback_action == "stop"

    def test_missing_file_does_not_raise(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "no_file.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.end_of_playback_action == "stop"

    def test_corrupt_json_falls_back_to_stop(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text("NOT JSON{{{")
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.end_of_playback_action == "stop"


class TestAppSettingsReadWrite:
    def test_set_rewind_persists(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.end_of_playback_action = "rewind"
            assert s.end_of_playback_action == "rewind"

    def test_set_loop_persists(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.end_of_playback_action = "loop"
            assert s.end_of_playback_action == "loop"

    def test_setting_survives_reload(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s1 = AppSettings()
            s1.end_of_playback_action = "rewind"

            s2 = AppSettings()
            assert s2.end_of_playback_action == "rewind"

    def test_invalid_setter_raises_value_error(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            with pytest.raises(ValueError):
                s.end_of_playback_action = "fly_away"


class TestAppSettingsAtomicWrite:
    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.end_of_playback_action = "loop"
            assert path.exists()

    def test_no_tmp_file_left_after_save(self, tmp_path):
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.end_of_playback_action = "stop"
            tmp = path.with_suffix(".json.tmp")
            assert not tmp.exists()
