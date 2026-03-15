"""US3: ウィンドウリサイズ統合テスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
from PyQt6.QtCore import QSize
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


class TestResizeToVideo:
    """_resize_to_video(): アスペクト比を維持したリサイズ。"""

    def test_resize_to_video_calls_resize(self, player):
        """_resize_to_video(w, h) が呼ばれるとウィンドウサイズが変わる。"""
        with patch.object(player, "resize") as mock_resize:
            player._resize_to_video(1920, 1080)
            mock_resize.assert_called_once()

    def test_resize_clamps_to_minimum_800x600(self, player):
        """低解像度動画（例: 320×240）は 800×600 以上にクランプされる。"""
        with patch.object(player, "resize") as mock_resize:
            player._resize_to_video(320, 240)
            args = mock_resize.call_args[0]
            w, h = args[0], args[1]
            assert w >= 800
            assert h >= 600

    def test_resize_clamps_to_screen_size(self, player, qtbot):
        """スクリーンサイズを超える動画は上限クランプされる。"""
        screen = player.screen()
        if screen is None:
            pytest.skip("スクリーンが利用不可")
        screen_w = screen.availableGeometry().width()
        screen_h = screen.availableGeometry().height()

        with patch.object(player, "resize") as mock_resize:
            player._resize_to_video(screen_w * 3, screen_h * 3)
            args = mock_resize.call_args[0]
            w, h = args[0], args[1]
            assert w <= screen_w
            assert h <= screen_h

    def test_resize_skipped_in_fullscreen(self, player):
        """フルスクリーン中は _resize_to_video が何もしない。"""
        with patch.object(player, "isFullScreen", return_value=True):
            with patch.object(player, "resize") as mock_resize:
                player._resize_to_video(1920, 1080)
                mock_resize.assert_not_called()


class TestSizePollTimer:
    """_size_poll_timer: 動画変更後に _poll_video_size をポーリングする。"""

    def test_size_poll_timer_exists(self, player):
        """_size_poll_timer が初期化されている。"""
        assert hasattr(player, "_size_poll_timer")

    def test_start_size_poll_starts_timer(self, player):
        """_start_size_poll() を呼ぶとタイマーが起動する。"""
        player._size_poll_timer.stop()
        player._start_size_poll()
        assert player._size_poll_timer.isActive()
        player._size_poll_timer.stop()

    def test_poll_video_size_calls_resize_when_size_available(self, player):
        """動画サイズが非ゼロで返ってきたら _resize_to_video を呼ぶ。"""
        player._size_poll_timer.start()
        with patch.object(player.media_player, "video_get_size", return_value=(1280, 720)):
            with patch.object(player, "_resize_to_video") as mock_resize:
                player._poll_video_size()
                mock_resize.assert_called_once_with(1280, 720)
        assert not player._size_poll_timer.isActive()

    def test_poll_video_size_keeps_polling_when_zero(self, player):
        """サイズが (0, 0) の場合はタイマーを止めない。"""
        player._size_poll_timer.start()
        with patch.object(player.media_player, "video_get_size", return_value=(0, 0)):
            with patch.object(player, "_resize_to_video") as mock_resize:
                player._poll_video_size()
                mock_resize.assert_not_called()
        assert player._size_poll_timer.isActive()
        player._size_poll_timer.stop()


class TestManualResizeStopsAutoResize:
    """ユーザー手動リサイズ後は _size_poll_timer が再発動しない。"""

    def test_resize_event_stops_poll_timer(self, player, qtbot):
        """resizeEvent が呼ばれると _size_poll_timer が停止する。"""
        player._size_poll_timer.start()
        # resizeEvent をシミュレート
        from PyQt6.QtGui import QResizeEvent
        old_size = player.size()
        new_size = QSize(old_size.width() + 50, old_size.height() + 50)
        event = QResizeEvent(new_size, old_size)
        player.resizeEvent(event)
        assert not player._size_poll_timer.isActive()


class TestManualResizeMenuAction:
    """表示メニューに「ウィンドウを動画サイズに合わせる」QAction が存在する。"""

    def test_fit_window_action_exists(self, player):
        view_menu = None
        for action in player.menuBar().actions():
            if "表示" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        texts = [a.text() for a in view_menu.actions()]
        assert any("動画サイズ" in t for t in texts), f"動画サイズアクションが見つかりません: {texts}"
