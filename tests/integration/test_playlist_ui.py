"""T031: プレイリスト UI パネルの統合テスト。"""
from unittest.mock import patch, MagicMock
from pathlib import Path
from PyQt6.QtGui import QShortcut
from looplayer.player import VideoPlayer
from looplayer.playlist import Playlist
from looplayer.widgets.playlist_panel import PlaylistPanel


def _make_playlist(tmp_path: Path, count: int = 3) -> Playlist:
    files = []
    for i in range(count):
        f = tmp_path / f"video_{i:02d}.mp4"
        f.write_bytes(b"")
        files.append(f)
    return Playlist(sorted(files))


class TestPlaylistPanel:
    def test_set_playlist_shows_panel(self, qtbot, tmp_path):
        """set_playlist で動画がセットされるとパネルに項目が表示される。"""
        panel = PlaylistPanel()
        qtbot.addWidget(panel)
        playlist = _make_playlist(tmp_path)
        panel.set_playlist(playlist)
        assert panel.list_widget.count() == 3

    def test_set_playlist_none_clears(self, qtbot, tmp_path):
        """set_playlist(None) でリストがクリアされる。"""
        panel = PlaylistPanel()
        qtbot.addWidget(panel)
        playlist = _make_playlist(tmp_path)
        panel.set_playlist(playlist)
        panel.set_playlist(None)
        assert panel.list_widget.count() == 0

    def test_click_emits_file_requested(self, qtbot, tmp_path):
        """リスト項目クリックで file_requested シグナルが emit される。"""
        panel = PlaylistPanel()
        qtbot.addWidget(panel)
        playlist = _make_playlist(tmp_path)
        panel.set_playlist(playlist)
        received = []
        panel.file_requested.connect(lambda p: received.append(p))
        panel.list_widget.item(1).setSelected(True)
        panel.list_widget.itemClicked.emit(panel.list_widget.item(1))
        assert len(received) == 1

    def test_update_current_highlights_item(self, qtbot, tmp_path):
        """update_current で現在ファイルがハイライトされる。"""
        panel = PlaylistPanel()
        qtbot.addWidget(panel)
        playlist = _make_playlist(tmp_path)
        panel.set_playlist(playlist)
        current_path = str(playlist.files[1])
        panel.update_current(current_path)
        assert panel.list_widget.currentRow() == 1


class TestPlaylistShortcuts:
    def _find_shortcut(self, player, key):
        for s in player.findChildren(QShortcut):
            if s.key().toString() == key:
                return s
        return None

    def test_alt_right_shortcut_registered(self, player: VideoPlayer):
        """Alt+→ ショートカットが登録されている。"""
        assert self._find_shortcut(player, "Alt+Right") is not None

    def test_alt_left_shortcut_registered(self, player: VideoPlayer):
        """Alt+← ショートカットが登録されている。"""
        assert self._find_shortcut(player, "Alt+Left") is not None


class TestPlaylistNavigation:
    def test_retreat_method(self, tmp_path):
        """Playlist.retreat() で index が 1 減る。"""
        playlist = _make_playlist(tmp_path)
        playlist.index = 2
        playlist.retreat()
        assert playlist.index == 1

    def test_retreat_does_not_go_below_zero(self, tmp_path):
        """Playlist.retreat() は index を 0 以下にしない。"""
        playlist = _make_playlist(tmp_path)
        playlist.index = 0
        playlist.retreat()
        assert playlist.index == 0
