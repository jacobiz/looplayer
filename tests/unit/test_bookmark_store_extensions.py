"""T002: LoopBookmark の新フィールド（pause_ms / play_count / tags）テスト。"""
import pytest
from looplayer.bookmark_store import LoopBookmark


class TestPauseMs:
    def test_default_is_zero(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        assert bm.pause_ms == 0

    def test_accepts_max_value(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, pause_ms=10000)
        assert bm.pause_ms == 10000

    def test_old_json_fallback_to_zero(self):
        d = {"id": "abc", "point_a_ms": 0, "point_b_ms": 1000}
        bm = LoopBookmark.from_dict(d)
        assert bm.pause_ms == 0

    def test_roundtrip(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, pause_ms=3000)
        bm2 = LoopBookmark.from_dict(bm.to_dict())
        assert bm2.pause_ms == 3000


class TestPlayCount:
    def test_default_is_zero(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        assert bm.play_count == 0

    def test_old_json_fallback_to_zero(self):
        d = {"id": "abc", "point_a_ms": 0, "point_b_ms": 1000}
        bm = LoopBookmark.from_dict(d)
        assert bm.play_count == 0

    def test_roundtrip(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, play_count=5)
        bm2 = LoopBookmark.from_dict(bm.to_dict())
        assert bm2.play_count == 5


class TestTags:
    def test_default_is_empty_list(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        assert bm.tags == []

    def test_old_json_fallback_to_empty_list(self):
        d = {"id": "abc", "point_a_ms": 0, "point_b_ms": 1000}
        bm = LoopBookmark.from_dict(d)
        assert bm.tags == []

    def test_roundtrip(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, tags=["発音", "リズム"])
        bm2 = LoopBookmark.from_dict(bm.to_dict())
        assert bm2.tags == ["発音", "リズム"]

    def test_different_instances_dont_share_list(self):
        bm1 = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        bm2 = LoopBookmark(point_a_ms=0, point_b_ms=2000)
        bm1.tags.append("test")
        assert bm2.tags == []
