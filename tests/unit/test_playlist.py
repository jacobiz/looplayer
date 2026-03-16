"""T025: Playlist のユニットテスト（US7）。"""
import pytest
from pathlib import Path


class TestPlaylistBasic:
    def test_current_returns_first_file(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
        pl = Playlist(files)
        assert pl.current() == files[0]

    def test_len(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4", tmp_path / "c.mp4"]
        pl = Playlist(files)
        assert len(pl) == 3

    def test_has_next_true_when_not_at_end(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
        pl = Playlist(files)
        assert pl.has_next() is True

    def test_has_next_false_when_at_end(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4"]
        pl = Playlist(files)
        assert pl.has_next() is False


class TestPlaylistAdvance:
    def test_advance_moves_to_next(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
        pl = Playlist(files)
        pl.advance()
        assert pl.current() == files[1]

    def test_advance_returns_true_when_successful(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
        pl = Playlist(files)
        assert pl.advance() is True

    def test_advance_returns_false_at_end(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4"]
        pl = Playlist(files)
        assert pl.advance() is False

    def test_has_next_false_after_last_advance(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
        pl = Playlist(files)
        pl.advance()
        assert pl.has_next() is False

    def test_advance_does_not_change_index_at_end(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "a.mp4"]
        pl = Playlist(files)
        pl.advance()
        assert pl.current() == files[0]


class TestPlaylistSingleFile:
    def test_single_file_current(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "only.mp4"]
        pl = Playlist(files)
        assert pl.current() == files[0]

    def test_single_file_has_no_next(self, tmp_path):
        from looplayer.playlist import Playlist
        files = [tmp_path / "only.mp4"]
        pl = Playlist(files)
        assert pl.has_next() is False
