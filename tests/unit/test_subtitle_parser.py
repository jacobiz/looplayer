"""字幕パーサー (subtitle_parser.py) のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from looplayer.subtitle_parser import (
    SubtitleEntry,
    BulkAddResult,
    parse_srt,
    parse_ass,
    parse_subtitle_file,
    entries_to_bookmarks,
)


# ── SRT パース ────────────────────────────────────────────────

class TestParseSrt:
    def test_basic_parse(self):
        srt = "1\n00:00:01,000 --> 00:00:03,000\nHello, world!\n\n"
        result = parse_srt(srt)
        assert len(result) == 1
        assert result[0].start_ms == 1000
        assert result[0].end_ms == 3000
        assert result[0].text == "Hello, world!"

    def test_timestamp_ms_conversion(self):
        srt = "1\n01:02:03,456 --> 01:02:05,789\nTest\n\n"
        result = parse_srt(srt)
        assert result[0].start_ms == (1 * 3600 + 2 * 60 + 3) * 1000 + 456
        assert result[0].end_ms == (1 * 3600 + 2 * 60 + 5) * 1000 + 789

    def test_multiple_entries(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:02,000\nFirst\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\nSecond\n\n"
            "3\n00:00:05,000 --> 00:00:06,000\nThird\n\n"
        )
        result = parse_srt(srt)
        assert len(result) == 3
        assert result[1].text == "Second"

    def test_multiline_text_joined(self):
        srt = "1\n00:00:01,000 --> 00:00:03,000\nLine one\nLine two\n\n"
        result = parse_srt(srt)
        assert result[0].text == "Line one Line two"

    def test_empty_string_returns_empty(self):
        assert parse_srt("") == []

    def test_malformed_entry_skipped(self):
        srt = "bad data without timestamps\n\n1\n00:00:01,000 --> 00:00:02,000\nOK\n\n"
        result = parse_srt(srt)
        assert len(result) == 1
        assert result[0].text == "OK"

    def test_overlapping_entries_both_registered(self):
        """重複・入れ子字幕区間は各エントリを独立したブックマーク候補として返す（EC-003）。"""
        srt = (
            "1\n00:00:01,000 --> 00:00:05,000\nOuter\n\n"
            "2\n00:00:02,000 --> 00:00:04,000\nInner\n\n"
        )
        result = parse_srt(srt)
        assert len(result) == 2
        assert result[0].text == "Outer"
        assert result[1].text == "Inner"


# ── ASS パース ────────────────────────────────────────────────

_ASS_HEADER = """\
[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


class TestParseAss:
    def test_basic_parse(self):
        ass = _ASS_HEADER + "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello\n"
        result = parse_ass(ass)
        assert len(result) == 1
        assert result[0].start_ms == 1000
        assert result[0].end_ms == 3000
        assert result[0].text == "Hello"

    def test_timestamp_centisecond_conversion(self):
        ass = _ASS_HEADER + "Dialogue: 0,1:02:03.45,1:02:05.67,Default,,0,0,0,,T\n"
        result = parse_ass(ass)
        assert result[0].start_ms == (1 * 3600 + 2 * 60 + 3) * 1000 + 450
        assert result[0].end_ms == (1 * 3600 + 2 * 60 + 5) * 1000 + 670

    def test_decoration_tags_removed(self):
        ass = _ASS_HEADER + "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\an8}{\\b1}こんにちは{\\b0}\n"
        result = parse_ass(ass)
        assert result[0].text == "こんにちは"

    def test_multiple_tags_removed(self):
        ass = _ASS_HEADER + "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,{\\c&H00FF00&}Green{\\r}\n"
        result = parse_ass(ass)
        assert result[0].text == "Green"

    def test_comment_lines_ignored(self):
        ass = _ASS_HEADER + "Comment: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,Should be ignored\n"
        result = parse_ass(ass)
        assert len(result) == 0

    def test_empty_returns_empty(self):
        assert parse_ass("") == []

    def test_overlapping_entries_both_registered(self):
        """重複・入れ子字幕区間は各エントリを独立して返す（EC-003）。"""
        ass = (
            _ASS_HEADER
            + "Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,Outer\n"
            + "Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,Inner\n"
        )
        result = parse_ass(ass)
        assert len(result) == 2


# ── entries_to_bookmarks ──────────────────────────────────────

class TestEntriesToBookmarks:
    def test_valid_entries_converted(self):
        entries = [SubtitleEntry(1000, 3000, "Hello")]
        result = entries_to_bookmarks(entries)
        assert result.added == 1
        assert result.skipped == 0
        assert result.bookmarks[0].point_a_ms == 1000
        assert result.bookmarks[0].point_b_ms == 3000
        assert result.bookmarks[0].name == "Hello"

    def test_invalid_entry_skipped(self):
        """start_ms >= end_ms のエントリはスキップ（FR-004）。"""
        entries = [
            SubtitleEntry(1000, 3000, "Valid"),
            SubtitleEntry(5000, 5000, "Equal - invalid"),
            SubtitleEntry(7000, 6000, "Reversed - invalid"),
        ]
        result = entries_to_bookmarks(entries)
        assert result.added == 1
        assert result.skipped == 2

    def test_text_truncated_at_80_chars(self):
        """80文字超は先頭80文字 + '...' に切り詰め（FR-005）。"""
        long_text = "あ" * 90
        entries = [SubtitleEntry(0, 1000, long_text)]
        result = entries_to_bookmarks(entries)
        assert result.bookmarks[0].name == "あ" * 80 + "..."
        assert len(result.bookmarks[0].name) == 83

    def test_text_exactly_80_chars_not_truncated(self):
        text = "x" * 80
        entries = [SubtitleEntry(0, 1000, text)]
        result = entries_to_bookmarks(entries)
        assert result.bookmarks[0].name == text

    def test_start_order_applied(self):
        entries = [
            SubtitleEntry(0, 1000, "A"),
            SubtitleEntry(1000, 2000, "B"),
        ]
        result = entries_to_bookmarks(entries, start_order=5)
        assert result.bookmarks[0].order == 5
        assert result.bookmarks[1].order == 6

    def test_bookmark_defaults(self):
        entries = [SubtitleEntry(0, 1000, "Test")]
        result = entries_to_bookmarks(entries)
        bm = result.bookmarks[0]
        assert bm.enabled is True
        assert bm.repeat_count == 1
        assert bm.pause_ms == 0
        assert bm.play_count == 0
        assert bm.tags == []
        assert bm.notes == ""

    def test_empty_entries(self):
        result = entries_to_bookmarks([])
        assert result.added == 0
        assert result.skipped == 0
        assert result.bookmarks == []


# ── パフォーマンス（SC-001・EC-006）────────────────────────────

class TestPerformance:
    def test_500_entries_under_5_seconds(self):
        """500件超の字幕エントリを 5 秒以内に処理できること（SC-001・EC-006）。"""
        import time
        # 500件の SRT テキストを生成
        lines = []
        for i in range(600):
            start_ms = i * 5000
            end_ms = start_ms + 3000
            start = f"{start_ms // 3600000:02d}:{(start_ms % 3600000) // 60000:02d}:{(start_ms % 60000) // 1000:02d},{start_ms % 1000:03d}"
            end = f"{end_ms // 3600000:02d}:{(end_ms % 3600000) // 60000:02d}:{(end_ms % 60000) // 1000:02d},{end_ms % 1000:03d}"
            lines.append(f"{i + 1}\n{start} --> {end}\nSubtitle text {i}\n")
        srt_text = "\n".join(lines)

        t0 = time.monotonic()
        entries = parse_srt(srt_text)
        result = entries_to_bookmarks(entries)
        elapsed = time.monotonic() - t0

        assert result.added == 600
        assert elapsed < 5.0, f"処理時間 {elapsed:.2f}s が 5 秒を超えました"


# ── parse_subtitle_file ───────────────────────────────────────

class TestParseSubtitleFile:
    def test_srt_file_parsed(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        srt_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello\n\n", encoding="utf-8")
        result = parse_subtitle_file(srt_file)
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_ass_file_parsed(self, tmp_path):
        ass_file = tmp_path / "test.ass"
        content = _ASS_HEADER + "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,World\n"
        ass_file.write_text(content, encoding="utf-8")
        result = parse_subtitle_file(ass_file)
        assert len(result) == 1
        assert result[0].text == "World"

    def test_ssa_file_parsed(self, tmp_path):
        ssa_file = tmp_path / "test.ssa"
        content = _ASS_HEADER + "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,SSA\n"
        ssa_file.write_text(content, encoding="utf-8")
        result = parse_subtitle_file(ssa_file)
        assert len(result) == 1

    def test_utf8_encoding(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        srt_file.write_text("1\n00:00:01,000 --> 00:00:02,000\n日本語テスト\n\n", encoding="utf-8")
        result = parse_subtitle_file(srt_file)
        assert result[0].text == "日本語テスト"

    def test_cp932_encoding_fallback(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        srt_file.write_bytes(
            "1\n00:00:01,000 --> 00:00:02,000\n".encode("utf-8")
            + "日本語テスト".encode("cp932")
            + "\n\n".encode("utf-8")
        )
        result = parse_subtitle_file(srt_file)
        assert "日本語テスト" in result[0].text

    def test_unsupported_encoding_raises(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        # \x81\x40 は UTF-8 で不正、かつ cp932 の 2 バイト文字として不完全なシーケンス
        srt_file.write_bytes(b"\x81\x81\x81\x81\x81\x81\x81\x81\x81")
        with pytest.raises(ValueError, match="encoding"):
            parse_subtitle_file(srt_file)

    def test_unsupported_extension_raises(self, tmp_path):
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text("WEBVTT\n\n", encoding="utf-8")
        with pytest.raises(ValueError):
            parse_subtitle_file(vtt_file)
