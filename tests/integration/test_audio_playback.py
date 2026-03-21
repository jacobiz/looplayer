"""020: 音楽ファイル再生の統合テスト（T012）。
ドラッグ&ドロップ・フォルダ読み込み・混在プレイリストを検証する。
"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtCore import QMimeData, QUrl, Qt, QPointF
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.player.UpdateChecker") as mock_checker_cls:
        mock_checker_cls.return_value = MagicMock()
        widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget._size_poll_timer.stop()
    widget.media_player.stop()


# ── ドラッグ&ドロップ ──────────────────────────────────────────────────────────

class TestAudioDragDrop:
    """音楽ファイルのドラッグ&ドロップが動作することを確認（FR-003）。"""

    def test_drag_enter_accepts_audio_file(self, player, tmp_path):
        """音楽ファイルの DragEnter は acceptProposedAction する。"""
        audio = tmp_path / "song.mp3"
        audio.touch()
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(audio))])
        event = QDragEnterEvent(
            player.rect().center(),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        player.dragEnterEvent(event)
        assert event.isAccepted()

    def test_drop_audio_file_calls_open_path(self, player, tmp_path):
        """音楽ファイルをドロップすると _open_path が呼ばれる。"""
        audio = tmp_path / "song.mp3"
        audio.touch()
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(audio))])
        event = QDropEvent(
            QPointF(player.rect().center()),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        with patch.object(player, "_open_path") as mock_open:
            player.dropEvent(event)
            mock_open.assert_called_once()
            assert os.path.normpath(str(audio)) == mock_open.call_args[0][0]

    def test_drop_all_audio_formats_accepted(self, player, tmp_path):
        """すべての対応音楽形式がドロップで受け付けられる。"""
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            audio = tmp_path / f"track{ext}"
            audio.touch()
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(audio))])
            event = QDropEvent(
                QPointF(player.rect().center()),
                Qt.DropAction.CopyAction,
                mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            with patch.object(player, "_open_path") as mock_open:
                player.dropEvent(event)
                mock_open.assert_called_once(), f"{ext} でドロップが _open_path を呼ばなかった"


# ── フォルダ読み込み ───────────────────────────────────────────────────────────

class TestAudioFolderLoading:
    """フォルダドロップで音楽ファイルがプレイリストに含まれることを確認（FR-004）。"""

    def test_audio_only_folder_creates_playlist(self, player, tmp_path):
        """音楽ファイルのみのフォルダを開くと Playlist が生成される。"""
        folder = tmp_path / "music"
        folder.mkdir()
        for name in ["b.mp3", "a.flac", "c.ogg"]:
            (folder / name).touch()

        with patch.object(player, "_open_path") as mock_open:
            player._open_folder(folder)
            # プレイリストが生成されていること
            assert player._playlist is not None
            assert len(player._playlist) == 3

    def test_audio_folder_sorted_by_filename(self, player, tmp_path):
        """フォルダ内の音楽ファイルがファイル名昇順で並ぶ。"""
        folder = tmp_path / "music"
        folder.mkdir()
        for name in ["c.mp3", "a.mp3", "b.mp3"]:
            (folder / name).touch()

        with patch.object(player, "_open_path") as mock_open:
            player._open_folder(folder)
            files = [f.name for f in player._playlist.files]
            assert files == ["a.mp3", "b.mp3", "c.mp3"]

    def test_mixed_folder_includes_both_types(self, player, tmp_path):
        """動画・音楽混在フォルダでは両方がプレイリストに含まれる。"""
        folder = tmp_path / "mixed"
        folder.mkdir()
        (folder / "b.mp4").touch()
        (folder / "a.mp3").touch()
        (folder / "c.mkv").touch()

        with patch.object(player, "_open_path") as mock_open:
            player._open_folder(folder)
            names = [f.name for f in player._playlist.files]
            assert "a.mp3" in names
            assert "b.mp4" in names
            assert "c.mkv" in names

    def test_mixed_folder_sorted_by_filename(self, player, tmp_path):
        """動画・音楽混在フォルダでもファイル名昇順で並ぶ。"""
        folder = tmp_path / "mixed"
        folder.mkdir()
        (folder / "c.mp4").touch()
        (folder / "a.mp3").touch()
        (folder / "b.flac").touch()

        with patch.object(player, "_open_path") as mock_open:
            player._open_folder(folder)
            names = [f.name for f in player._playlist.files]
            assert names == ["a.mp3", "b.flac", "c.mp4"]

    def test_empty_folder_shows_error(self, player, tmp_path):
        """対応ファイルのないフォルダはエラーメッセージを表示する。"""
        folder = tmp_path / "empty"
        folder.mkdir()
        (folder / "readme.txt").touch()  # 非対応ファイルのみ

        # _open_folder 内でローカルインポートされる QMessageBox をパッチする
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            player._open_folder(folder)
            mock_warn.assert_called_once()

    def test_single_audio_file_folder_no_playlist(self, player, tmp_path):
        """音楽ファイル 1 件のフォルダはプレイリストを生成しない。"""
        folder = tmp_path / "single"
        folder.mkdir()
        (folder / "only.mp3").touch()

        with patch.object(player, "_open_path") as mock_open:
            player._open_folder(folder)
            assert player._playlist is None
            mock_open.assert_called_once()
