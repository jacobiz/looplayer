"""音量・ミュート状態の単体テスト（US2）。"""
import pytest
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


class TestVolumeInitialState:
    def test_initial_volume_is_80(self, player):
        assert player._volume == 80

    def test_initial_muted_is_false(self, player):
        assert player._is_muted is False

    def test_initial_pre_mute_volume_is_80(self, player):
        assert player._pre_mute_volume == 80


class TestSetVolume:
    def test_set_volume_normal(self, player):
        player._set_volume(50)
        assert player._volume == 50

    def test_set_volume_clamp_below_zero(self, player):
        player._set_volume(-10)
        assert player._volume == 0

    def test_set_volume_clamp_above_100(self, player):
        player._set_volume(150)
        assert player._volume == 100

    def test_set_volume_updates_label(self, player):
        player._set_volume(60)
        assert player.volume_label.text() == "60%"

    def test_set_volume_updates_slider(self, player):
        player._set_volume(70)
        assert player.volume_slider.value() == 70


class TestMuteToggle:
    def test_toggle_mute_sets_is_muted(self, player):
        player._set_volume(80)
        player._toggle_mute()
        assert player._is_muted is True

    def test_toggle_mute_saves_pre_mute_volume(self, player):
        player._set_volume(75)
        player._toggle_mute()
        assert player._pre_mute_volume == 75

    def test_toggle_mute_sets_volume_to_zero(self, player):
        player._set_volume(80)
        player._toggle_mute()
        assert player._volume == 0

    def test_toggle_unmute_restores_volume(self, player):
        player._set_volume(65)
        player._toggle_mute()   # mute
        player._toggle_mute()   # unmute
        assert player._volume == 65

    def test_toggle_unmute_clears_is_muted(self, player):
        player._toggle_mute()
        player._toggle_mute()
        assert player._is_muted is False
