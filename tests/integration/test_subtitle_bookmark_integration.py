"""字幕→ブックマーク生成→Undo の統合テスト。"""
from __future__ import annotations

from pathlib import Path

import pytest

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.subtitle_parser import parse_srt, entries_to_bookmarks


_VIDEO_PATH = "/tmp/test_video.mp4"

_SRT_TEXT = """\
1
00:00:01,000 --> 00:00:03,000
First subtitle

2
00:00:04,000 --> 00:00:06,000
Second subtitle

3
00:00:07,000 --> 00:00:07,000
Invalid (A=B)

"""


class TestSubtitleToBookmarkFlow:
    """字幕エントリを BookmarkStore に追加するフロー（FR-002, FR-006）。"""

    def test_bookmarks_added_to_store(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        entries = parse_srt(_SRT_TEXT)
        result = entries_to_bookmarks(entries)

        store.add_many(_VIDEO_PATH, result.bookmarks)

        bookmarks = store.get_bookmarks(_VIDEO_PATH)
        assert len(bookmarks) == 2
        assert bookmarks[0].point_a_ms == 1000
        assert bookmarks[0].point_b_ms == 3000
        assert bookmarks[0].name == "First subtitle"

    def test_appends_to_existing_bookmarks(self, tmp_path):
        """既存ブックマークの末尾に追記（FR-006）。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        existing = LoopBookmark(point_a_ms=500, point_b_ms=800, name="Existing")
        store.add(_VIDEO_PATH, existing)

        entries = parse_srt(_SRT_TEXT)
        result = entries_to_bookmarks(entries)
        store.add_many(_VIDEO_PATH, result.bookmarks)

        bookmarks = store.get_bookmarks(_VIDEO_PATH)
        assert len(bookmarks) == 3
        assert bookmarks[0].name == "Existing"
        assert bookmarks[1].name == "First subtitle"

    def test_invalid_entries_skipped(self, tmp_path):
        """start_ms >= end_ms のエントリはスキップ（FR-004）。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        entries = parse_srt(_SRT_TEXT)
        result = entries_to_bookmarks(entries)

        # 2件追加・1件スキップ
        assert result.added == 2
        assert result.skipped == 1
        store.add_many(_VIDEO_PATH, result.bookmarks)
        assert len(store.get_bookmarks(_VIDEO_PATH)) == 2

    def test_undo_removes_bulk_added_bookmarks(self, tmp_path):
        """一括生成したブックマークを全件削除できる（FR-008）。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        existing = LoopBookmark(point_a_ms=100, point_b_ms=200, name="Keep me")
        store.add(_VIDEO_PATH, existing)

        entries = parse_srt(_SRT_TEXT)
        result = entries_to_bookmarks(entries)
        store.add_many(_VIDEO_PATH, result.bookmarks)

        assert len(store.get_bookmarks(_VIDEO_PATH)) == 3

        # Undo: 追加したブックマークを全件削除
        for bm in result.bookmarks:
            store.delete(_VIDEO_PATH, bm.id)

        bookmarks = store.get_bookmarks(_VIDEO_PATH)
        assert len(bookmarks) == 1
        assert bookmarks[0].name == "Keep me"

    def test_persistence_after_add_many(self, tmp_path):
        """add_many 後に JSON に永続化されること。"""
        storage = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=storage)
        entries = parse_srt(_SRT_TEXT)
        result = entries_to_bookmarks(entries)
        store.add_many(_VIDEO_PATH, result.bookmarks)

        # 新しいストアインスタンスで読み直す
        store2 = BookmarkStore(storage_path=storage)
        assert len(store2.get_bookmarks(_VIDEO_PATH)) == 2
