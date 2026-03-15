"""再生速度状態の単体テスト（US2）。"""
import pytest
from unittest.mock import patch, MagicMock
from pytestqt.qtbot import QtBot
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


class TestPlaybackRateInitialState:
    def test_initial_rate_is_1_0(self, player):
        assert player._playback_rate == 1.0


class TestSetPlaybackRate:
    def test_set_rate_half(self, player):
        player._set_playback_rate(0.5)
        assert player._playback_rate == 0.5

    def test_set_rate_2x(self, player):
        player._set_playback_rate(2.0)
        assert player._playback_rate == 2.0

    def test_set_rate_1_25(self, player):
        player._set_playback_rate(1.25)
        assert player._playback_rate == 1.25

    def test_set_rate_valid_values(self, player):
        for rate in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            player._set_playback_rate(rate)
            assert player._playback_rate == rate


class TestOpenFileResetsRate:
    def test_open_file_resets_rate_to_1_0(self, player):
        """open_file() が _set_playback_rate(1.0) を呼び出すことを確認。"""
        player._set_playback_rate(1.5)
        assert player._playback_rate == 1.5
        # ダイアログをモックして空パスを返す（open_file は空パスでは何もしない）
        # 代わりに _set_playback_rate が open_file のパスで呼ばれることを確認
        with patch.object(player, "_set_playback_rate") as mock_set_rate:
            with patch("looplayer.player.QFileDialog.getOpenFileName",
                       return_value=("/fake/video.mp4", "")):
                with patch.object(player.media_player, "set_media"):
                    with patch.object(player.media_player, "play"):
                        with patch.object(player.bookmark_panel, "load_video"):
                            player.open_file()
            # open_file の最後に _set_playback_rate(1.0) が呼ばれることを確認
            mock_set_rate.assert_called_with(1.0)
