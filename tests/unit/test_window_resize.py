"""ウィンドウサイズを動画サイズに合わせる機能のユニットテスト。"""
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    """VideoPlayer インスタンス（UpdateChecker モック済み）。"""
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.player.UpdateChecker") as mock_checker_cls:
        mock_checker_cls.return_value = MagicMock()
        widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


class TestResizeToVideo:
    """_resize_to_video のユニットテスト（US1）。"""

    def test_video_frame_height_matches_video(self, player: VideoPlayer):
        """_resize_to_video(1280, 720) が動画フレームの高さを 720 にするよう
        ウィンドウをリサイズすること。

        ui_h_offset を加算した高さで resize() が呼ばれることを確認する。
        これにより video_frame（動画エリア）は本来の 720px を受け取る。
        """
        ui_h_offset = player.height() - player.video_frame.height()

        with patch.object(player, 'isFullScreen', return_value=False):
            mock_screen = MagicMock()
            mock_screen.availableGeometry.return_value.width.return_value = 3840
            mock_screen.availableGeometry.return_value.height.return_value = 2160
            with patch.object(player, 'screen', return_value=mock_screen):
                with patch.object(player, 'resize') as mock_resize:
                    player._resize_to_video(1280, 720)

        # resize() が (w, 720 + ui_h_offset) で呼ばれること
        assert mock_resize.called
        _, target_h = mock_resize.call_args[0]
        # target_h = 720 + ui_h_offset により video_frame が 720px になる
        assert target_h == 720 + ui_h_offset

    def test_window_height_includes_ui_offset(self, player: VideoPlayer):
        """ウィンドウ高さが 720 + ui_h_offset になること。

        ui_h_offset = window.height() - video_frame.height() （コントロール分）
        """
        # リサイズ前のオフセットを計算
        ui_h_offset = player.height() - player.video_frame.height()

        with patch.object(player, 'isFullScreen', return_value=False):
            mock_screen = MagicMock()
            mock_screen.availableGeometry.return_value.width.return_value = 3840
            mock_screen.availableGeometry.return_value.height.return_value = 2160
            with patch.object(player, 'screen', return_value=mock_screen):
                player._resize_to_video(1280, 720)

        expected_h = 720 + ui_h_offset
        assert player.height() == expected_h

    def test_fullscreen_skips_resize(self, player: VideoPlayer):
        """isFullScreen() が True のとき resize が呼ばれないこと。"""
        original_size = player.size()
        with patch.object(player, 'isFullScreen', return_value=True):
            with patch.object(player, 'resize') as mock_resize:
                player._resize_to_video(1280, 720)
        mock_resize.assert_not_called()

    def test_no_video_skips_resize(self, player: VideoPlayer):
        """video_get_size が (0, 0) を返す状態で _poll_video_size を呼んでも
        _resize_to_video が呼ばれないこと（FR-008: 動画なしでクラッシュしない）。
        """
        with patch.object(player.media_player, 'video_get_size', return_value=(0, 0)):
            with patch.object(player, '_resize_to_video') as mock_resize:
                player._poll_video_size()
        mock_resize.assert_not_called()

    def test_window_size_clamped_to_screen(self, player: VideoPlayer):
        """動画解像度がスクリーンサイズを超える場合にクランプされること（FR-007）。

        9999×9999 の動画でも avail.width() / avail.height() 以下になる。
        """
        avail_w, avail_h = 1920, 1080
        with patch.object(player, 'isFullScreen', return_value=False):
            mock_screen = MagicMock()
            mock_screen.availableGeometry.return_value.width.return_value = avail_w
            mock_screen.availableGeometry.return_value.height.return_value = avail_h
            with patch.object(player, 'screen', return_value=mock_screen):
                player._resize_to_video(9999, 9999)
        assert player.width() <= avail_w
        assert player.height() <= avail_h


class TestPollTimeout:
    """_poll_video_size タイムアウトのユニットテスト（US2）。"""

    def test_timer_stops_after_100_polls(self, player: VideoPlayer):
        """video_get_size が (0,0) を返す状態で 100 回ポーリング後にタイマーが停止すること。"""
        player._size_poll_count = 0
        player._size_poll_timer.start()  # タイマーを起動してからポーリングする
        with patch.object(player.media_player, 'video_get_size', return_value=(0, 0)):
            for _ in range(100):
                player._poll_video_size()
        assert not player._size_poll_timer.isActive()

    def test_timer_stops_immediately_on_valid_size(self, player: VideoPlayer):
        """video_get_size が (1280, 720) を返すとき 1 回目でタイマーが停止すること。"""
        player._size_poll_count = 0
        player._size_poll_timer.start()
        with patch.object(player.media_player, 'video_get_size', return_value=(1280, 720)):
            with patch.object(player, '_resize_to_video'):
                player._poll_video_size()
        assert not player._size_poll_timer.isActive()

    def test_start_size_poll_resets_count(self, player: VideoPlayer):
        """_start_size_poll 後に _size_poll_count == 0 であること。"""
        player._size_poll_count = 99
        player._start_size_poll()
        assert player._size_poll_count == 0


class TestDeadCode:
    """デッドコード削除のユニットテスト（US3）。"""

    def test_user_resized_flag_does_not_exist(self, player: VideoPlayer):
        """_start_size_poll() 呼び出し後に _user_resized 属性が存在しないこと。

        _start_size_poll() 後に確認することで、メソッド内に
        self._user_resized = False が残っている場合に FAIL する。
        """
        player._start_size_poll()
        assert not hasattr(player, '_user_resized')

    def test_on_vlc_video_changed_does_not_exist(self, player: VideoPlayer):
        """_on_vlc_video_changed メソッドが存在しないこと。"""
        assert not hasattr(player, '_on_vlc_video_changed')
