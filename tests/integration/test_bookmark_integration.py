"""
ブックマーク機能の統合テスト（US1・US2・US3）

Note: PyQt6 の GUI ウィジェットを直接テストするのではなく、
BookmarkStore と VideoPlayer のロジック層をテストする。
統合テストはモックを使わず実際の依存を使用する（憲法 I）。
"""
import pytest
import tempfile
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore, LoopBookmark


VIDEO = "/home/user/test_video.mp4"
VIDEO_B = "/home/user/other_video.mp4"


@pytest.fixture
def store(tmp_path):
    return BookmarkStore(storage_path=tmp_path / "bookmarks.json")


# ── US1: ブックマーク登録・一覧表示・切り替え・削除 ─────────

class TestUS1BookmarkBasicFlow:
    """US1 統合テスト: ブックマーク保存・一覧表示・切り替え・削除フロー。"""

    def test_ブックマークを保存して一覧に表示できる(self, store):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="サビ")
        store.add(VIDEO, bm)
        bms = store.get_bookmarks(VIDEO)
        assert len(bms) == 1
        assert bms[0].name == "サビ"
        assert bms[0].point_a_ms == 1000
        assert bms[0].point_b_ms == 5000

    def test_一覧から別のブックマークを選択できる(self, store):
        bm1 = LoopBookmark(point_a_ms=0, point_b_ms=3000, name="イントロ")
        bm2 = LoopBookmark(point_a_ms=5000, point_b_ms=10000, name="サビ")
        store.add(VIDEO, bm1)
        store.add(VIDEO, bm2)
        bms = store.get_bookmarks(VIDEO)
        # 2番目を選択 → そのA点とB点が返ること
        selected = bms[1]
        assert selected.point_a_ms == 5000
        assert selected.point_b_ms == 10000

    def test_ブックマーク名を編集できる(self, store):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=3000, name="旧名前")
        store.add(VIDEO, bm)
        store.update_name(VIDEO, bm.id, "新名前")
        assert store.get_bookmarks(VIDEO)[0].name == "新名前"

    def test_ブックマークを削除できる(self, store):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=3000, name="削除対象")
        store.add(VIDEO, bm)
        store.delete(VIDEO, bm.id)
        assert store.get_bookmarks(VIDEO) == []

    def test_無効な区間は保存できない(self, store):
        with pytest.raises(ValueError):
            store.add(VIDEO, LoopBookmark(point_a_ms=5000, point_b_ms=5000))


# ── US2: 連続再生フロー ────────────────────────────────────

class TestUS2SequentialPlayFlow:
    """US2 統合テスト: 連続再生開始→複数区間の自動遷移→停止フロー。"""

    def test_連続再生で複数区間が順番に再生される(self):
        from looplayer.sequential import SequentialPlayState
        bms = [
            LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A"),
            LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B"),
            LoopBookmark(point_a_ms=4000, point_b_ms=5000, name="C"),
        ]
        for i, bm in enumerate(bms):
            bm.order = i

        state = SequentialPlayState(bookmarks=bms)
        assert state.current_bookmark.name == "A"
        state.on_b_reached()
        assert state.current_bookmark.name == "B"
        state.on_b_reached()
        assert state.current_bookmark.name == "C"

    def test_最終区間後は先頭に戻る(self):
        from looplayer.sequential import SequentialPlayState
        bms = [
            LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A"),
            LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B"),
        ]
        for i, bm in enumerate(bms):
            bm.order = i

        state = SequentialPlayState(bookmarks=bms)
        state.on_b_reached()  # A→B
        state.on_b_reached()  # B→先頭（A）
        assert state.current_bookmark.name == "A"

    def test_停止操作でactiveがFalseになる(self):
        from looplayer.sequential import SequentialPlayState
        bms = [LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A")]
        bms[0].order = 0
        state = SequentialPlayState(bookmarks=bms)
        state.stop()
        assert state.active is False


# ── US3: 永続化・動画切り替え ──────────────────────────────

class TestUS3PersistenceFlow:
    """US3 統合テスト: 動画オープン時の自動ロード・動画切り替え時の一覧切り替え・並び順永続化。"""

    def test_アプリ再起動後にブックマークが復元される(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        # セッション1: 保存
        store1 = BookmarkStore(storage_path=path)
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="復元テスト", repeat_count=3)
        store1.add(VIDEO, bm)

        # セッション2: 再起動シミュレーション（新インスタンス）
        store2 = BookmarkStore(storage_path=path)
        bms = store2.get_bookmarks(VIDEO)
        assert len(bms) == 1
        assert bms[0].name == "復元テスト"
        assert bms[0].point_a_ms == 1000
        assert bms[0].repeat_count == 3

    def test_異なる動画を開くと対応するブックマークのみ表示される(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        store.add(VIDEO, LoopBookmark(point_a_ms=0, point_b_ms=1000, name="動画A用"))
        store.add(VIDEO_B, LoopBookmark(point_a_ms=0, point_b_ms=2000, name="動画B用"))

        assert len(store.get_bookmarks(VIDEO)) == 1
        assert store.get_bookmarks(VIDEO)[0].name == "動画A用"
        assert len(store.get_bookmarks(VIDEO_B)) == 1
        assert store.get_bookmarks(VIDEO_B)[0].name == "動画B用"

    def test_並び替え後の順序が永続化される(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        bm_a = LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A")
        bm_b = LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B")
        store.add(VIDEO, bm_a)
        store.add(VIDEO, bm_b)

        # B→A の順に並び替え
        store.update_order(VIDEO, [bm_b.id, bm_a.id])

        store2 = BookmarkStore(storage_path=path)
        bms = store2.get_bookmarks(VIDEO)
        assert bms[0].name == "B"
        assert bms[1].name == "A"
