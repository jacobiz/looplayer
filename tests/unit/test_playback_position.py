"""T019: PlaybackPosition のユニットテスト（US5）。"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


def make_pp(tmp_path):
    """PlaybackPosition を tmp_path の positions.json に向けて作成する。"""
    path = tmp_path / "positions.json"
    with patch("looplayer.playback_position._PATH", path):
        from looplayer.playback_position import PlaybackPosition
        return PlaybackPosition(), path


class TestPlaybackPositionSave:
    def test_save_stores_position(self, tmp_path):
        video = tmp_path / "video.mp4"
        video.write_bytes(b"")
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save(str(video), 30000, 120000)
            pp2 = PlaybackPosition()
            assert pp2.load(str(video)) == 30000

    def test_save_skips_if_under_5s(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save("/video.mp4", 4999, 120000)
            assert pp.load("/video.mp4") is None

    def test_save_skips_if_duration_zero(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save("/video.mp4", 30000, 0)
            assert pp.load("/video.mp4") is None

    def test_save_removes_entry_at_95_percent(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save("/video.mp4", 30000, 60000)
            pp.save("/video.mp4", 57000, 60000)  # 95%
            assert pp.load("/video.mp4") is None

    def test_save_keeps_entry_at_94_percent(self, tmp_path):
        video = tmp_path / "video.mp4"
        video.write_bytes(b"")
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save(str(video), 56000, 60000)  # 93.3%
            assert pp.load(str(video)) == 56000


class TestPlaybackPositionLimit:
    def test_max_10_entries(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            for i in range(12):
                pp.save(f"/video{i}.mp4", 10000, 60000)
            data = json.loads((tmp_path / "p.json").read_text())
            assert len(data) <= 10

    def test_oldest_entry_removed_when_over_limit(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            for i in range(11):
                pp.save(f"/video{i}.mp4", 10000, 60000)
            assert pp.load("/video0.mp4") is None


class TestPlaybackPositionLoad:
    def test_load_returns_none_for_unknown_path(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            assert pp.load("/nonexistent.mp4") is None

    def test_load_returns_none_if_file_does_not_exist(self, tmp_path):
        fake_video = tmp_path / "ghost.mp4"
        # ファイルは存在しない
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            assert pp.load(str(fake_video)) is None

    def test_load_returns_position_for_existing_file(self, tmp_path):
        video = tmp_path / "real.mp4"
        video.write_bytes(b"")  # ファイルを作成
        with patch("looplayer.playback_position._PATH", tmp_path / "p.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save(str(video), 15000, 60000)
            pp2 = PlaybackPosition()
            assert pp2.load(str(video)) == 15000

    def test_load_handles_corrupt_json(self, tmp_path):
        path = tmp_path / "p.json"
        path.write_text("NOT JSON")
        with patch("looplayer.playback_position._PATH", path):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            assert pp.load("/any.mp4") is None
