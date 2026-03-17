"""tests/unit/test_updater.py — looplayer.updater モジュールのユニットテスト。"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import looplayer.updater as updater_mod
from looplayer.updater import _is_newer, UpdateChecker
from looplayer.app_settings import AppSettings


# ── T003: _is_newer() バージョン比較テスト ───────────────────────────────────


def test_is_newer_returns_true_when_latest_is_newer():
    assert _is_newer("1.1.0", "1.2.0") is True


def test_is_newer_returns_false_when_same():
    assert _is_newer("1.1.0", "1.1.0") is False


def test_is_newer_returns_false_when_older():
    assert _is_newer("1.2.0", "1.1.0") is False


def test_is_newer_handles_patch_version():
    assert _is_newer("1.1.0", "1.1.3") is True


def test_is_newer_strips_v_prefix():
    assert _is_newer("1.1.0", "v1.2.0") is True


# ── T004: UpdateChecker シグナルテスト ──────────────────────────────────────


def _make_urlopen_mock(api_response: dict):
    """urllib.request.urlopen のコンテキストマネージャモックを作成する。"""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(api_response).encode()
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_resp)
    mock_cm.__exit__ = MagicMock(return_value=False)
    mock_urlopen = MagicMock(return_value=mock_cm)
    return mock_urlopen


def test_update_checker_emits_update_available(qtbot):
    """新バージョンが存在する場合 update_available が発行される（Windows プラットフォームとしてテスト）。"""
    api_response = {
        "tag_name": "v1.2.0",
        "assets": [
            {"name": "LoopPlayer-Setup-1.2.0.exe",
             "browser_download_url": "https://github.com/jacobiz/looplayer/releases/download/v1.2.0/LoopPlayer-Setup-1.2.0.exe"},
        ],
    }
    with patch("looplayer.updater.urllib.request.urlopen", _make_urlopen_mock(api_response)), \
         patch("looplayer.updater.sys.platform", "win32"):
        checker = UpdateChecker("1.0.0")
        received = []
        checker.update_available.connect(lambda v, u: received.append((v, u)))
        with qtbot.waitSignal(checker.update_available, timeout=5000):
            checker.start()
        checker.wait()

    assert received[0][0] == "1.2.0"
    assert "LoopPlayer-Setup-1.2.0.exe" in received[0][1]


def test_update_checker_emits_up_to_date(qtbot):
    """最新バージョンの場合 up_to_date が発行される。"""
    api_response = {"tag_name": "v1.1.0", "assets": []}
    with patch("looplayer.updater.urllib.request.urlopen", _make_urlopen_mock(api_response)):
        checker = UpdateChecker("1.1.0")
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()


def test_update_checker_emits_check_failed_on_network_error(qtbot):
    """ネットワークエラー時に check_failed が発行される。"""
    with patch("looplayer.updater.urllib.request.urlopen", side_effect=OSError("network error")):
        checker = UpdateChecker("1.1.0")
        received = []
        checker.check_failed.connect(received.append)
        with qtbot.waitSignal(checker.check_failed, timeout=5000):
            checker.start()
        checker.wait()

    assert len(received) == 1


def test_update_checker_unsupported_platform_emits_update_available_with_empty_url(qtbot):
    """対応外 OS では download_url が空文字列で update_available が発行される。"""
    api_response = {
        "tag_name": "v1.2.0",
        "assets": [
            {"name": "LoopPlayer-Setup-1.2.0.exe",
             "browser_download_url": "https://example.com/LoopPlayer-Setup-1.2.0.exe"},
        ],
    }
    with patch("looplayer.updater.urllib.request.urlopen", _make_urlopen_mock(api_response)), \
         patch("looplayer.updater.sys.platform", "linux"):
        checker = UpdateChecker("1.0.0")
        received = []
        checker.update_available.connect(lambda v, u: received.append((v, u)))
        with qtbot.waitSignal(checker.update_available, timeout=5000):
            checker.start()
        checker.wait()

    assert received[0][1] == ""


# ── T005: AppSettings.check_update_on_startup テスト ────────────────────────


def test_check_update_on_startup_default_is_true(tmp_path):
    """デフォルト値は True。"""
    with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
        s = AppSettings()
        assert s.check_update_on_startup is True


def test_check_update_on_startup_save_and_reload(tmp_path):
    """False に設定して保存し、再読み込みしても False のまま。"""
    settings_file = tmp_path / "settings.json"
    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s = AppSettings()
        s.check_update_on_startup = False

    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s2 = AppSettings()
        assert s2.check_update_on_startup is False


def test_check_update_on_startup_true_after_reenable(tmp_path):
    """False → True に戻せる。"""
    settings_file = tmp_path / "settings.json"
    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s = AppSettings()
        s.check_update_on_startup = False
        s.check_update_on_startup = True

    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s2 = AppSettings()
        assert s2.check_update_on_startup is True
