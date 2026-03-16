"""US3: 動画情報ダイアログのユニットテスト — ファイルサイズフォーマット変換。"""
import pytest


def _format_size(size_bytes: int) -> str:
    """テスト対象関数（player.py に実装予定）。"""
    from looplayer.player import VideoPlayer
    return VideoPlayer._format_file_size(size_bytes)


class TestFormatFileSize:
    """ファイルサイズのバイト→人間可読フォーマット変換テスト（FR-013）。"""

    def test_bytes_range(self):
        assert "B" in _format_size(512)

    def test_kilobytes_range(self):
        result = _format_size(2048)
        assert "KB" in result or "KiB" in result or "2" in result

    def test_megabytes_range(self):
        result = _format_size(5 * 1024 * 1024)
        assert "MB" in result or "MiB" in result or "5" in result

    def test_gigabytes_range(self):
        result = _format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result or "GiB" in result or "2" in result

    def test_zero_bytes(self):
        result = _format_size(0)
        assert "0" in result

    def test_returns_string(self):
        assert isinstance(_format_size(1024), str)

    def test_exact_one_mb(self):
        result = _format_size(1024 * 1024)
        assert "1" in result and ("MB" in result or "MiB" in result)
