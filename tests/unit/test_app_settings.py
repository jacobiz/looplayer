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


# ── 016-p1-features: F-403 window_geometry テスト ────────────────────────────


class TestWindowGeometry:
    def test_default_returns_none(self, tmp_path):
        """キーが存在しない場合 None を返す。"""
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.window_geometry is None

    def test_set_and_get_valid_geometry(self, tmp_path):
        """有効な dict をセットして同値が返る。"""
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            geo = {"x": 100, "y": 200, "width": 1280, "height": 720}
            s.window_geometry = geo
            assert s.window_geometry == geo

    def test_geometry_survives_reload(self, tmp_path):
        """保存→リロードで同値が返る。"""
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s1 = AppSettings()
            s1.window_geometry = {"x": 50, "y": 60, "width": 800, "height": 600}

            s2 = AppSettings()
            assert s2.window_geometry == {"x": 50, "y": 60, "width": 800, "height": 600}

    def test_set_none_removes_key(self, tmp_path):
        """None をセットするとキーが削除される。"""
        path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.window_geometry = {"x": 0, "y": 0, "width": 800, "height": 600}
            s.window_geometry = None
            assert s.window_geometry is None
            data = json.loads(path.read_text())
            assert "window_geometry" not in data

    def test_missing_field_returns_none(self, tmp_path):
        """必須フィールド欠損の dict は None を返す。"""
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"window_geometry": {"x": 0, "y": 0}}))
        with patch("looplayer.app_settings._SETTINGS_PATH", path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.window_geometry is None
