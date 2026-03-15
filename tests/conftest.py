import pytest
from pathlib import Path
from pytestqt.qtbot import QtBot
from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    """VideoPlayer インスタンスを生成し、テスト後にクリーンアップする。
    tmp_path を使った BookmarkStore を渡すことで実環境を汚染しない。
    """
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()
