"""020: 対応拡張子セットのユニットテスト（T001 / T004 / T014）。"""
import pytest
from pathlib import Path
from unittest.mock import patch


# VideoPlayer クラス属性のみ参照するため、Qt ウィジェットの生成は不要
from looplayer.player import VideoPlayer


# ── T001: 基本拡張子セット検証（T002 実装前は AttributeError で FAIL） ─────────

class TestSupportedExtensions:
    """_SUPPORTED_VIDEO_EXTENSIONS / _SUPPORTED_AUDIO_EXTENSIONS / _SUPPORTED_EXTENSIONS の検証。"""

    def test_audio_extensions_attribute_exists(self):
        assert hasattr(VideoPlayer, "_SUPPORTED_AUDIO_EXTENSIONS"), (
            "_SUPPORTED_AUDIO_EXTENSIONS が VideoPlayer クラスに存在しない"
        )

    def test_video_extensions_attribute_exists(self):
        assert hasattr(VideoPlayer, "_SUPPORTED_VIDEO_EXTENSIONS"), (
            "_SUPPORTED_VIDEO_EXTENSIONS が VideoPlayer クラスに存在しない"
        )

    def test_audio_extensions_contains_required_formats(self):
        required = {".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"}
        assert required <= VideoPlayer._SUPPORTED_AUDIO_EXTENSIONS, (
            f"不足している音楽拡張子: {required - VideoPlayer._SUPPORTED_AUDIO_EXTENSIONS}"
        )

    def test_supported_extensions_is_union_of_video_and_audio(self):
        expected = VideoPlayer._SUPPORTED_VIDEO_EXTENSIONS | VideoPlayer._SUPPORTED_AUDIO_EXTENSIONS
        assert VideoPlayer._SUPPORTED_EXTENSIONS == expected, (
            "_SUPPORTED_EXTENSIONS が動画と音楽の結合セットではない"
        )

    def test_audio_extensions_not_in_video_extensions(self):
        overlap = VideoPlayer._SUPPORTED_AUDIO_EXTENSIONS & VideoPlayer._SUPPORTED_VIDEO_EXTENSIONS
        assert overlap == set(), (
            f"音楽拡張子が動画拡張子セットに含まれている: {overlap}"
        )

    def test_existing_video_extensions_preserved(self):
        required_video = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
        assert required_video <= VideoPlayer._SUPPORTED_VIDEO_EXTENSIONS


# ── T004: ファイルダイアログフィルタ文字列の検証 ─────────────────────────────

class TestMediaFileFilter:
    """filter.media_file i18n 文字列に音楽・動画拡張子が含まれることを確認。"""

    def test_filter_media_file_key_exists(self):
        from looplayer.i18n import t
        result = t("filter.media_file")
        assert result, "filter.media_file i18n キーが空"

    def test_filter_media_file_contains_mp3(self):
        from looplayer.i18n import t
        assert "mp3" in t("filter.media_file")

    def test_filter_media_file_contains_mp4(self):
        from looplayer.i18n import t
        assert "mp4" in t("filter.media_file")

    def test_filter_media_file_contains_flac(self):
        from looplayer.i18n import t
        assert "flac" in t("filter.media_file")

    def test_filter_audio_file_key_exists(self):
        from looplayer.i18n import t
        result = t("filter.audio_file")
        assert result, "filter.audio_file i18n キーが空"

    def test_filter_audio_file_excludes_video(self):
        from looplayer.i18n import t
        # 音楽ファイルフィルタに動画拡張子が入っていないこと
        audio_filter = t("filter.audio_file")
        assert ".mp4" not in audio_filter


# ── T014: 音楽ファイルと既存サブシステムの互換性検証 ─────────────────────────

class TestBookmarkStoreWithAudio:
    """BookmarkStore が音楽ファイルパスを問題なく扱えることを確認（FR-006）。"""

    def test_bookmark_store_saves_audio_path(self, tmp_path):
        from looplayer.bookmark_store import BookmarkStore, LoopBookmark
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="サビ")
        audio_path = str(tmp_path / "song.mp3")
        store.add(audio_path, bm)
        loaded = store.get_bookmarks(audio_path)
        assert len(loaded) == 1
        assert loaded[0].point_a_ms == 1000

    def test_bookmark_store_works_for_multiple_audio_formats(self, tmp_path):
        from looplayer.bookmark_store import BookmarkStore, LoopBookmark
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            path = str(tmp_path / f"track{ext}")
            bm = LoopBookmark(point_a_ms=0, point_b_ms=3000, name=ext)
            store.add(path, bm)
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            path = str(tmp_path / f"track{ext}")
            assert len(store.get_bookmarks(path)) == 1


class TestPlaybackPositionWithAudio:
    """PlaybackPosition が音楽ファイルパスを問題なく扱えることを確認（FR-007）。"""

    def test_saves_and_loads_audio_position(self, tmp_path):
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"")
        with patch("looplayer.playback_position._PATH", tmp_path / "positions.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            pp.save(str(audio), 30000, 180000)
            pp2 = PlaybackPosition()
            assert pp2.load(str(audio)) == 30000

    def test_saves_position_for_all_audio_formats(self, tmp_path):
        with patch("looplayer.playback_position._PATH", tmp_path / "positions.json"):
            from looplayer.playback_position import PlaybackPosition
            pp = PlaybackPosition()
            for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
                audio = tmp_path / f"track{ext}"
                audio.write_bytes(b"")
                pp.save(str(audio), 10000, 60000)
            pp2 = PlaybackPosition()
            for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
                audio = tmp_path / f"track{ext}"
                assert pp2.load(str(audio)) == 10000


class TestRecentFilesWithAudio:
    """RecentFiles が音楽ファイルパスを問題なく扱えることを確認（FR-008）。"""

    def test_adds_audio_path_to_recent(self, tmp_path):
        from looplayer.recent_files import RecentFiles
        rf = RecentFiles(storage_path=tmp_path / "recent.json")
        rf.add("/music/song.mp3")
        assert "/music/song.mp3" in rf.files

    def test_adds_multiple_audio_formats(self, tmp_path):
        from looplayer.recent_files import RecentFiles
        rf = RecentFiles(storage_path=tmp_path / "recent.json")
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            rf.add(f"/music/track{ext}")
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            assert f"/music/track{ext}" in rf.files
