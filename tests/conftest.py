import pytest
from pytestqt.qtbot import QtBot
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot) -> VideoPlayer:
    """VideoPlayer インスタンスを生成し、テスト後にクリーンアップする。"""
    widget = VideoPlayer()
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()
