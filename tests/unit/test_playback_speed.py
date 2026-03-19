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


class TestSpeedUpDown:
    """T004: _speed_up / _speed_down の境界動作テスト（US1）。"""

    def test_speed_up_from_1_0_goes_to_1_25(self, player):
        player._set_playback_rate(1.0)
        player._speed_up()
        assert player._playback_rate == 1.25

    def test_speed_down_from_1_0_goes_to_0_75(self, player):
        player._set_playback_rate(1.0)
        player._speed_down()
        assert player._playback_rate == 0.75

    def test_speed_up_at_max_stays_at_max(self, player):
        player._set_playback_rate(3.0)
        player._speed_up()
        assert player._playback_rate == 3.0

    def test_speed_down_at_min_stays_at_min(self, player):
        player._set_playback_rate(0.25)
        player._speed_down()
        assert player._playback_rate == 0.25

    def test_speed_up_traverses_all_rates(self, player):
        from looplayer.player import _PLAYBACK_RATES
        player._set_playback_rate(_PLAYBACK_RATES[0])
        for expected in _PLAYBACK_RATES[1:]:
            player._speed_up()
            assert player._playback_rate == expected

    def test_speed_down_traverses_all_rates(self, player):
        from looplayer.player import _PLAYBACK_RATES
        player._set_playback_rate(_PLAYBACK_RATES[-1])
        for expected in reversed(_PLAYBACK_RATES[:-1]):
            player._speed_down()
            assert player._playback_rate == expected


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
