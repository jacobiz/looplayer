"""T003: SequentialPlayState の1周停止モードテスト。"""
import pytest
from looplayer.bookmark_store import LoopBookmark
from looplayer.sequential import SequentialPlayState


def make_bms(count: int, repeat: int = 1) -> list[LoopBookmark]:
    return [
        LoopBookmark(
            point_a_ms=i * 1000,
            point_b_ms=i * 1000 + 500,
            repeat_count=repeat,
        )
        for i in range(count)
    ]


class TestInfiniteMode:
    def test_default_is_infinite(self):
        state = SequentialPlayState(bookmarks=make_bms(2))
        assert state.one_round_mode is False

    def test_wraps_around_and_returns_int(self):
        bms = make_bms(2)
        state = SequentialPlayState(bookmarks=bms)
        # bm[0] B到達 → bm[1] の A を返す
        result = state.on_b_reached()
        assert result == bms[1].point_a_ms
        # bm[1] B到達 → bm[0] の A を返す（ラップアラウンド）
        result = state.on_b_reached()
        assert result == bms[0].point_a_ms
        assert result is not None


class TestOneRoundMode:
    def test_returns_int_for_non_final(self):
        bms = make_bms(2)
        state = SequentialPlayState(bookmarks=bms, one_round_mode=True)
        result = state.on_b_reached()
        assert isinstance(result, int)
        assert result == bms[1].point_a_ms

    def test_returns_none_at_end_of_round(self):
        bms = make_bms(2)
        state = SequentialPlayState(bookmarks=bms, one_round_mode=True)
        state.on_b_reached()   # bm[0] → bm[1]
        result = state.on_b_reached()  # bm[1] 最終 → None
        assert result is None

    def test_returns_none_with_single_bookmark(self):
        bms = make_bms(1)
        state = SequentialPlayState(bookmarks=bms, one_round_mode=True)
        result = state.on_b_reached()
        assert result is None

    def test_repeat_count_respected_before_none(self):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=500, repeat_count=2)
        state = SequentialPlayState(bookmarks=[bm], one_round_mode=True)
        # 1回目: まだ repeat が残るので int
        result = state.on_b_reached()
        assert isinstance(result, int)
        # 2回目: repeat が尽きて最終 → None
        result = state.on_b_reached()
        assert result is None
