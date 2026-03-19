"""test_speed_fine_adjustment: Shift+[/] 速度連続微調整のテスト（F-101 US1）。"""
import pytest
from unittest.mock import patch
from pathlib import Path
from pytestqt.qtbot import QtBot

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


class TestSpeedFineLogic:
    """速度微調整の算術ロジックテスト。"""

    def test_speed_fine_up_increments_by_0_05(self):
        new_rate = min(3.0, round(1.0 + 0.05, 2))
        assert new_rate == pytest.approx(1.05)

    def test_speed_fine_up_at_max_stays_at_3_0(self):
        new_rate = min(3.0, round(3.0 + 0.05, 2))
        assert new_rate == pytest.approx(3.0)

    def test_speed_fine_down_decrements_by_0_05(self):
        new_rate = max(0.25, round(1.0 - 0.05, 2))
        assert new_rate == pytest.approx(0.95)

    def test_speed_fine_down_at_min_stays_at_0_25(self):
        new_rate = max(0.25, round(0.25 - 0.05, 2))
        assert new_rate == pytest.approx(0.25)

    def test_speed_fine_up_clips_to_max(self):
        new_rate = min(3.0, round(2.98 + 0.05, 2))
        assert new_rate == pytest.approx(3.0)

    def test_speed_fine_down_clips_to_min(self):
        new_rate = max(0.25, round(0.27 - 0.05, 2))
        assert new_rate == pytest.approx(0.25)

    def test_speed_fine_up_float_rounding(self):
        """round(..., 2) がないと 0.28 + 0.05 = 0.32999... になることを確認。"""
        assert round(0.28 + 0.05, 2) == 0.33
        new_rate = min(3.0, round(0.28 + 0.05, 2))
        assert new_rate == pytest.approx(0.33)


class TestSpeedFineUpMethod:
    """VideoPlayer._speed_fine_up() メソッドのテスト。"""

    def test_speed_fine_up_increments_rate(self, player):
        player._set_playback_rate(1.0)
        player._speed_fine_up()
        assert player._playback_rate == pytest.approx(1.05)

    def test_speed_fine_up_at_max_stays_at_3_0(self, player):
        player._set_playback_rate(3.0)
        player._speed_fine_up()
        assert player._playback_rate == pytest.approx(3.0)

    def test_speed_fine_up_at_max_shows_max_speed_status(self, player):
        player._set_playback_rate(3.0)
        player._speed_fine_up()
        # ステータスバーに max_speed メッセージが表示される
        assert player.statusBar().currentMessage() != ""

    def test_speed_fine_up_shows_feedback_message(self, player):
        player._set_playback_rate(1.0)
        player._speed_fine_up()
        # 通常の微調整時は speed_fine_up メッセージが表示される
        from looplayer.i18n import t
        assert player.statusBar().currentMessage() == t("status.speed_fine_up")

    def test_speed_fine_up_clips_to_3_0(self, player):
        player._set_playback_rate(2.98)
        player._speed_fine_up()
        assert player._playback_rate == pytest.approx(3.0)


class TestSpeedFineDownMethod:
    """VideoPlayer._speed_fine_down() メソッドのテスト。"""

    def test_speed_fine_down_decrements_rate(self, player):
        player._set_playback_rate(1.0)
        player._speed_fine_down()
        assert player._playback_rate == pytest.approx(0.95)

    def test_speed_fine_down_at_min_stays_at_0_25(self, player):
        player._set_playback_rate(0.25)
        player._speed_fine_down()
        assert player._playback_rate == pytest.approx(0.25)

    def test_speed_fine_down_at_min_shows_min_speed_status(self, player):
        player._set_playback_rate(0.25)
        player._speed_fine_down()
        assert player.statusBar().currentMessage() != ""

    def test_speed_fine_down_shows_feedback_message(self, player):
        player._set_playback_rate(1.0)
        player._speed_fine_down()
        from looplayer.i18n import t
        assert player.statusBar().currentMessage() == t("status.speed_fine_down")

    def test_speed_fine_down_clips_to_0_25(self, player):
        player._set_playback_rate(0.27)
        player._speed_fine_down()
        assert player._playback_rate == pytest.approx(0.25)
