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
            {"name": "looplay-Setup-1.2.0.exe",
             "browser_download_url": "https://github.com/jacobiz/looplayer/releases/download/v1.2.0/looplay-Setup-1.2.0.exe"},
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
    assert "looplay-Setup-1.2.0.exe" in received[0][1]


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
            {"name": "looplay-Setup-1.2.0.exe",
             "browser_download_url": "https://github.com/jacobiz/looplayer/releases/download/v1.2.0/looplay-Setup-1.2.0.exe"},
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


# ── T006: AppSettings キャッシュフィールドテスト ─────────────────────────────


def test_last_update_check_ts_default_is_zero(tmp_path):
    """last_update_check_ts のデフォルトは 0.0。"""
    with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
        s = AppSettings()
        assert s.last_update_check_ts == 0.0


def test_update_check_etag_default_is_empty(tmp_path):
    """update_check_etag のデフォルトは空文字列。"""
    with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
        s = AppSettings()
        assert s.update_check_etag == ""


def test_cache_fields_save_and_reload(tmp_path):
    """last_update_check_ts と update_check_etag を保存・再読み込みできる。"""
    settings_file = tmp_path / "settings.json"
    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s = AppSettings()
        s.last_update_check_ts = 1_700_000_000.0
        s.update_check_etag = '"abc123"'

    with patch("looplayer.app_settings._SETTINGS_PATH", settings_file):
        s2 = AppSettings()
        assert s2.last_update_check_ts == 1_700_000_000.0
        assert s2.update_check_etag == '"abc123"'


# ── T007: UpdateChecker キャッシュ・ETag テスト ──────────────────────────────


def _make_settings_mock(last_ts: float = 0.0, etag: str = "") -> MagicMock:
    """AppSettings のモックを作成する。"""
    m = MagicMock()
    m.last_update_check_ts = last_ts
    m.update_check_etag = etag
    return m


def test_update_checker_skips_when_checked_recently(qtbot):
    """前回チェックから 6h 未満の場合は API を叩かずに up_to_date を発行する。"""
    import time
    settings = _make_settings_mock(last_ts=time.time())  # 今チェック済み
    with patch("looplayer.updater.urllib.request.urlopen") as mock_urlopen:
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()
    mock_urlopen.assert_not_called()


def test_update_checker_sends_etag_header(qtbot):
    """保存済み ETag を If-None-Match ヘッダーに付与して送信する。"""
    import urllib.request as urllib_req
    api_response = {"tag_name": "v1.0.0", "assets": []}
    settings = _make_settings_mock(last_ts=0.0, etag='"saved-etag"')

    captured_headers = {}

    def fake_urlopen(req, timeout=None):
        captured_headers.update(req.headers)
        return _make_urlopen_mock(api_response)(req, timeout=timeout)

    with patch("looplayer.updater.urllib.request.urlopen", fake_urlopen):
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()

    assert "If-none-match" in captured_headers  # urllib は先頭大文字・残り小文字
    assert captured_headers["If-none-match"] == '"saved-etag"'


def test_update_checker_handles_304_as_up_to_date(qtbot):
    """304 Not Modified のとき up_to_date を発行し、タイムスタンプを更新する。"""
    import time
    import urllib.error
    settings = _make_settings_mock(last_ts=0.0)

    err_304 = urllib.error.HTTPError(
        url=None, code=304, msg="Not Modified", hdrs={}, fp=None
    )
    before = time.time()
    with patch("looplayer.updater.urllib.request.urlopen", side_effect=err_304):
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()

    # タイムスタンプが更新されていること（before 以降の値が設定される）
    assert settings.last_update_check_ts >= before


def test_update_checker_saves_etag_on_200(qtbot):
    """200 レスポンスで ETag ヘッダーがある場合、settings に保存する。"""
    api_response = {"tag_name": "v1.0.0", "assets": []}

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(api_response).encode()
    mock_resp.headers = {"ETag": '"new-etag"'}
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_resp)
    mock_cm.__exit__ = MagicMock(return_value=False)

    settings = _make_settings_mock(last_ts=0.0)
    with patch("looplayer.updater.urllib.request.urlopen", return_value=mock_cm):
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()

    assert settings.update_check_etag == '"new-etag"'


# ── 027: キャッシュ期間 6h テスト ────────────────────────────────────────────


def test_check_interval_is_6h():
    """_CHECK_INTERVAL_SECS が 6時間（21600 秒）であること（FR-001）。"""
    from looplayer.updater import _CHECK_INTERVAL_SECS
    assert _CHECK_INTERVAL_SECS == 21600


def test_update_checker_skips_within_6h(qtbot):
    """前回チェックから 5時間以内の場合は API を叩かずに up_to_date を発行する（FR-001）。"""
    import time
    settings = _make_settings_mock(last_ts=time.time() - 5 * 3600)  # 5時間前
    with patch("looplayer.updater.urllib.request.urlopen") as mock_urlopen:
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()
    mock_urlopen.assert_not_called()


def test_update_checker_runs_after_6h(qtbot):
    """前回チェックから 7時間経過した場合は GitHub API を呼び出す（FR-001）。"""
    import time
    api_response = {"tag_name": "v1.0.0", "assets": []}
    settings = _make_settings_mock(last_ts=time.time() - 7 * 3600)  # 7時間前

    with patch("looplayer.updater.urllib.request.urlopen",
               _make_urlopen_mock(api_response)) as mock_urlopen:
        checker = UpdateChecker("1.0.0", settings=settings)
        with qtbot.waitSignal(checker.up_to_date, timeout=5000):
            checker.start()
        checker.wait()
    mock_urlopen.assert_called_once()
