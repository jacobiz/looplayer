"""
SequentialPlayState の状態遷移ロジック単体テスト
"""
import pytest
from bookmark_store import LoopBookmark


# ── SequentialPlayState はまだ main.py に実装される予定のため
#    テスト実行時はインポートを遅延させる
def _import_state():
    from main import SequentialPlayState
    return SequentialPlayState


def _make_bookmarks(specs: list[tuple[int, int, int]]) -> list[LoopBookmark]:
    """(point_a_ms, point_b_ms, repeat_count) のリストからブックマークを作成。"""
    bms = []
    for i, (a, b, r) in enumerate(specs):
        bm = LoopBookmark(point_a_ms=a, point_b_ms=b, repeat_count=r, name=f"区間{i+1}")
        bm.order = i
        bms.append(bm)
    return bms


class TestSequentialPlayState:
    """T020: SequentialPlayState の状態遷移テスト。"""

    def test_初期状態が正しく設定される(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 2)])
        state = SequentialPlayState(bookmarks=bms)
        assert state.active is True
        assert state.current_index == 0
        assert state.remaining_repeats == 1

    def test_B点到達時に繰り返しが減算される(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 3)])
        state = SequentialPlayState(bookmarks=bms)
        # 1回目終了
        next_a = state.on_b_reached()
        assert state.remaining_repeats == 2
        assert state.current_index == 0
        assert next_a == 0  # 同じ区間のA点

    def test_繰り返しが0になったら次の区間に移動する(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        next_a = state.on_b_reached()
        assert state.current_index == 1
        assert state.remaining_repeats == 1
        assert next_a == 2000  # 次の区間のA点

    def test_最終区間終了後は先頭に戻る(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        state.on_b_reached()  # 区間2へ
        next_a = state.on_b_reached()  # 先頭に戻る
        assert state.current_index == 0
        assert state.remaining_repeats == 1
        assert next_a == 0  # 先頭のA点

    def test_stopを呼ぶとactiveがFalseになる(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        state.stop()
        assert state.active is False

    def test_current_bookmarkが現在の区間を返す(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        assert state.current_bookmark.point_a_ms == 0
        state.on_b_reached()
        assert state.current_bookmark.point_a_ms == 2000

    def test_next_bookmark_nameが次の区間名を返す(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        assert state.next_bookmark_name == "区間2"

    def test_最後の区間のnext_bookmark_nameは先頭の名前を返す(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        state.on_b_reached()  # 区間2へ
        assert state.next_bookmark_name == "区間1"  # 先頭に戻る

    def test_1件リストで連続再生すると単独ループとして動作する(self):
        """エッジケース: ブックマークが1件のみの場合。"""
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        next_a = state.on_b_reached()
        assert state.current_index == 0  # 先頭=同じ区間に戻る
        assert next_a == 0

    def test_repeat_count2の区間は2回繰り返してから次に進む(self):
        SequentialPlayState = _import_state()
        bms = _make_bookmarks([(0, 1000, 2), (2000, 3000, 1)])
        state = SequentialPlayState(bookmarks=bms)
        # 1回目終了: まだ区間1
        state.on_b_reached()
        assert state.current_index == 0
        assert state.remaining_repeats == 1
        # 2回目終了: 区間2へ
        state.on_b_reached()
        assert state.current_index == 1

    def test_空リストで初期化するとValueError(self):
        """C-1: 空リストで SequentialPlayState を作ると ValueError が発生すること。"""
        SequentialPlayState = _import_state()
        with pytest.raises(ValueError, match="1件以上"):
            SequentialPlayState(bookmarks=[])
