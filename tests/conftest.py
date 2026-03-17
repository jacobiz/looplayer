import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pytestqt.qtbot import QtBot
from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    """VideoPlayer インスタンスを生成し、テスト後にクリーンアップする。
    tmp_path を使った BookmarkStore を渡すことで実環境を汚染しない。
    UpdateChecker はテスト中に実際のネットワーク通信を行わないようモックする。
    """
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.player.UpdateChecker") as mock_checker_cls:
        mock_checker_cls.return_value = MagicMock()
        widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()
