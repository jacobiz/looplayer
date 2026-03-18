"""016-p1-features: F-403 ウィンドウ位置・サイズの記憶 統合テスト。"""
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QPoint, QRect
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.i18n import t as _t
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


@pytest.fixture
def player_with_geo(qtbot: QtBot, tmp_path: Path):
    """window_geometry を事前に設定した設定ファイルを使う VideoPlayer。"""
    settings_path = tmp_path / "settings.json"
    import json
    settings_path.write_text(json.dumps({
        "window_geometry": {"x": 150, "y": 100, "width": 900, "height": 650}
    }))
    with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
        qtbot.addWidget(widget)
        yield widget, settings_path
        widget.timer.stop()
        widget.media_player.stop()


class TestWindowGeometryRestore:
    def test_geometry_restored_on_startup(self, player_with_geo):
        """保存済みジオメトリが起動時に復元される。"""
        widget, _ = player_with_geo
        geo = widget.geometry()
        assert geo.width() == 900
        assert geo.height() == 650

    def test_geometry_clamped_to_minimum_size(self, qtbot, tmp_path):
        """幅/高さが最小値以下の場合、最小値（800×600）に補正される。"""
        settings_path = tmp_path / "settings.json"
        import json
        settings_path.write_text(json.dumps({
            "window_geometry": {"x": 0, "y": 0, "width": 400, "height": 300}
        }))
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
            widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
            qtbot.addWidget(widget)
            try:
                geo = widget.geometry()
                assert geo.width() >= 800
                assert geo.height() >= 600
            finally:
                widget.timer.stop()
                widget.media_player.stop()


class TestWindowGeometrySave:
    def test_geometry_saved_on_close(self, qtbot, tmp_path):
        """終了時にウィンドウジオメトリが settings.json に保存される。"""
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
            widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
            qtbot.addWidget(widget)
            widget.resize(950, 700)
            widget.close()

            from looplayer.app_settings import AppSettings
            s = AppSettings()
            geo = s.window_geometry
            assert geo is not None
            assert geo["width"] == 950
            assert geo["height"] == 700

    def test_pre_fullscreen_geometry_saved_when_closing_in_fullscreen(self, qtbot, tmp_path):
        """フルスクリーン中に終了した場合、フルスクリーン前のジオメトリが保存される。"""
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
            widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
            qtbot.addWidget(widget)
            widget.resize(1000, 750)
            pre_geo = widget.geometry()
            # フルスクリーン突入をシミュレート（_pre_fullscreen_geometry を手動設定）
            widget._pre_fullscreen_geometry = pre_geo
            with patch.object(widget, "isFullScreen", return_value=True):
                widget.close()

            from looplayer.app_settings import AppSettings
            s = AppSettings()
            geo = s.window_geometry
            assert geo is not None
            assert geo["width"] == pre_geo.width()
            assert geo["height"] == pre_geo.height()


class TestWindowGeometryReset:
    def test_reset_window_action_exists_in_view_menu(self, player):
        """表示メニューに「ウィンドウ位置をリセット」QAction が存在する。"""
        view_title = _t("menu.view").replace("&", "")
        view_menu = None
        for action in player.menuBar().actions():
            if view_title in action.text().replace("&", ""):
                view_menu = action.menu()
                break
        assert view_menu is not None, "表示メニューが見つかりません"
        reset_text = _t("menu.view.reset_window")
        texts = [a.text() for a in view_menu.actions()]
        assert any(reset_text in txt for txt in texts), \
            f"ウィンドウ位置リセットアクションが見つかりません: {texts}"

    def test_reset_window_geometry_clears_setting(self, qtbot, tmp_path):
        """_reset_window_geometry() を呼ぶと window_geometry が None になる。"""
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
            widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
            qtbot.addWidget(widget)
            widget._app_settings.window_geometry = {"x": 0, "y": 0, "width": 800, "height": 600}
            widget._reset_window_geometry()
            assert widget._app_settings.window_geometry is None
            widget.timer.stop()
            widget.media_player.stop()


class TestFullscreenGeometryTracking:
    def test_pre_fullscreen_geometry_set_on_fullscreen_enter(self, player):
        """フルスクリーン突入時に _pre_fullscreen_geometry が設定される。"""
        player.resize(1000, 700)
        expected = player.geometry()
        with patch.object(player, "showFullScreen"):
            player.toggle_fullscreen()
        assert player._pre_fullscreen_geometry is not None
        assert player._pre_fullscreen_geometry.width() == expected.width()
        assert player._pre_fullscreen_geometry.height() == expected.height()
