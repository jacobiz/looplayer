"""US1: ドラッグ＆ドロップ統合テスト。"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtCore import QMimeData, QUrl, Qt, QPointF, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
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


class TestDragEnterEvent:
    """dragEnterEvent: 対応拡張子の URL を含む場合のみ acceptProposedAction。"""

    def test_accepts_video_file_url(self, player, tmp_path):
        """ローカル動画ファイルの URL を含む DragEnter は受け付ける。"""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(video_file))])

        pos = player.rect().center()
        event = QDragEnterEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        player.dragEnterEvent(event)
        assert event.isAccepted()

    def test_ignores_non_url_mime(self, player):
        """URL を含まない MimeData は無視する。"""
        mime = QMimeData()
        mime.setText("plain text")

        pos = player.rect().center()
        event = QDragEnterEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        player.dragEnterEvent(event)
        assert not event.isAccepted()


class TestDropEvent:
    """dropEvent: ドロップされたファイルを _open_path で開く。"""

    def test_opens_video_file_on_drop(self, player, tmp_path):
        """ローカル動画ファイルをドロップすると _open_path が呼ばれる。"""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(video_file))])

        pos = QPointF(player.rect().center())
        event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        with patch.object(player, "_open_path") as mock_open:
            player.dropEvent(event)
            mock_open.assert_called_once()
            called_path = mock_open.call_args[0][0]
            assert os.path.normpath(str(video_file)) == called_path

    def test_ignores_unsupported_extension(self, player, tmp_path):
        """非対応拡張子（.txt）はドロップしても _open_path が呼ばれない。"""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(txt_file))])

        pos = QPointF(player.rect().center())
        event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        with patch.object(player, "_open_path") as mock_open:
            player.dropEvent(event)
            mock_open.assert_not_called()

    def test_uses_first_file_when_multiple_dropped(self, player, tmp_path):
        """複数ファイルをドロップした場合、先頭ファイルのみ開く。"""
        file1 = tmp_path / "first.mp4"
        file2 = tmp_path / "second.mp4"
        file1.touch()
        file2.touch()

        mime = QMimeData()
        mime.setUrls([
            QUrl.fromLocalFile(str(file1)),
            QUrl.fromLocalFile(str(file2)),
        ])

        pos = QPointF(player.rect().center())
        event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        with patch.object(player, "_open_path") as mock_open:
            player.dropEvent(event)
            mock_open.assert_called_once()
            called_path = mock_open.call_args[0][0]
            assert os.path.normpath(str(file1)) == called_path

    def test_ignores_non_local_url(self, player):
        """非ローカル URL（http://）は無視する。"""
        mime = QMimeData()
        mime.setUrls([QUrl("http://example.com/video.mp4")])

        pos = QPointF(player.rect().center())
        event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        with patch.object(player, "_open_path") as mock_open:
            player.dropEvent(event)
            mock_open.assert_not_called()


class TestAcceptDropsEnabled:
    """setAcceptDrops(True) が __init__ で呼ばれていることを確認。"""

    def test_accept_drops_is_true(self, player):
        assert player.acceptDrops() is True
