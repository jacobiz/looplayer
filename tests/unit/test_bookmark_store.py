"""
LoopBookmark データクラスと BookmarkStore の単体テスト
"""
import pytest
import tempfile
from pathlib import Path

from bookmark_store import BookmarkStore, LoopBookmark


# ── LoopBookmark テスト ───────────────────────────────────────

class TestLoopBookmark:
    def test_正常に作成できる(self):
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="テスト")
        assert bm.point_a_ms == 1000
        assert bm.point_b_ms == 5000
        assert bm.name == "テスト"
        assert bm.repeat_count == 1
        assert bm.order == 0
        assert bm.id  # UUID が設定されている

    def test_repeat_countが0以下の場合はValueError(self):
        with pytest.raises(ValueError):
            LoopBookmark(point_a_ms=0, point_b_ms=1000, repeat_count=0)

    def test_repeat_countが負の場合はValueError(self):
        with pytest.raises(ValueError):
            LoopBookmark(point_a_ms=0, point_b_ms=1000, repeat_count=-1)

    def test_to_dictとfrom_dictで往復できる(self):
        bm = LoopBookmark(point_a_ms=2000, point_b_ms=8000, name="往復テスト", repeat_count=3, order=1)
        restored = LoopBookmark.from_dict(bm.to_dict())
        assert restored.id == bm.id
        assert restored.name == bm.name
        assert restored.point_a_ms == bm.point_a_ms
        assert restored.point_b_ms == bm.point_b_ms
        assert restored.repeat_count == bm.repeat_count
        assert restored.order == bm.order


# ── BookmarkStore インメモリ操作テスト ───────────────────────

@pytest.fixture
def store(tmp_path):
    """一時ディレクトリを使う BookmarkStore インスタンス。"""
    return BookmarkStore(storage_path=tmp_path / "bookmarks.json")


VIDEO = "/home/user/test.mp4"


class TestBookmarkStoreInMemory:
    def test_初期状態では空のリストを返す(self, store):
        assert store.get_bookmarks(VIDEO) == []

    def test_addでブックマークを追加できる(self, store):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=5000, name="追加テスト")
        store.add(VIDEO, bm)
        bms = store.get_bookmarks(VIDEO)
        assert len(bms) == 1
        assert bms[0].name == "追加テスト"

    def test_複数追加できる(self, store):
        store.add(VIDEO, LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A"))
        store.add(VIDEO, LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B"))
        assert len(store.get_bookmarks(VIDEO)) == 2

    def test_deleteでブックマークを削除できる(self, store):
        bm = LoopBookmark(point_a_ms=0, point_b_ms=5000, name="削除対象")
        store.add(VIDEO, bm)
        store.delete(VIDEO, bm.id)
        assert store.get_bookmarks(VIDEO) == []

    def test_存在しないIDを削除しても例外が発生しない(self, store):
        store.delete(VIDEO, "nonexistent-id")  # 例外が出ないこと

    def test_get_bookmarksはorder順で返す(self, store):
        bm_a = LoopBookmark(point_a_ms=0, point_b_ms=1000, name="最初")
        bm_b = LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="2番目")
        store.add(VIDEO, bm_a)
        store.add(VIDEO, bm_b)
        bms = store.get_bookmarks(VIDEO)
        assert bms[0].name == "最初"
        assert bms[1].name == "2番目"

    def test_名前が空の場合はデフォルト名が付く(self, store):
        store.add(VIDEO, LoopBookmark(point_a_ms=0, point_b_ms=1000, name=""))
        bms = store.get_bookmarks(VIDEO)
        assert bms[0].name == "ブックマーク 1"

    def test_deleteの後にorderが再採番される(self, store):
        bm_a = LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A")
        bm_b = LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B")
        bm_c = LoopBookmark(point_a_ms=4000, point_b_ms=5000, name="C")
        store.add(VIDEO, bm_a)
        store.add(VIDEO, bm_b)
        store.add(VIDEO, bm_c)
        store.delete(VIDEO, bm_b.id)
        bms = store.get_bookmarks(VIDEO)
        assert len(bms) == 2
        assert bms[0].order == 0
        assert bms[1].order == 1


# ── BookmarkStore FR-011 バリデーションテスト ────────────────

class TestBookmarkStoreValidation:
    """T016b: BookmarkStore.add() が無効な区間で ValueError を送出すること。"""

    def test_A点がB点以上の場合はValueError(self, store):
        with pytest.raises(ValueError, match="A点"):
            store.add(VIDEO, LoopBookmark(point_a_ms=5000, point_b_ms=5000))

    def test_A点がB点より後の場合はValueError(self, store):
        with pytest.raises(ValueError):
            store.add(VIDEO, LoopBookmark(point_a_ms=6000, point_b_ms=5000))

    def test_B点が動画長を超える場合はValueError(self, store):
        with pytest.raises(ValueError, match="動画長"):
            store.add(VIDEO, LoopBookmark(point_a_ms=0, point_b_ms=10000), video_length_ms=9000)

    def test_video_length_msが0の場合は動画長チェックをスキップ(self, store):
        # 例外が発生しないこと
        store.add(VIDEO, LoopBookmark(point_a_ms=0, point_b_ms=99999), video_length_ms=0)

    def test_バリデーション失敗後もストアに追加されない(self, store):
        try:
            store.add(VIDEO, LoopBookmark(point_a_ms=5000, point_b_ms=5000))
        except ValueError:
            pass
        assert store.get_bookmarks(VIDEO) == []


# ── BookmarkStore JSON 永続化テスト ──────────────────────────

class TestBookmarkStorePersistence:
    """T028: JSON 永続化の単体テスト。"""

    def test_保存したデータを再ロードで完全復元できる(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store1 = BookmarkStore(storage_path=path)
        bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="永続化テスト", repeat_count=2)
        store1.add(VIDEO, bm)

        # 別インスタンスで再ロード
        store2 = BookmarkStore(storage_path=path)
        bms = store2.get_bookmarks(VIDEO)
        assert len(bms) == 1
        assert bms[0].id == bm.id
        assert bms[0].name == "永続化テスト"
        assert bms[0].point_a_ms == 1000
        assert bms[0].point_b_ms == 5000
        assert bms[0].repeat_count == 2

    def test_複数動画のブックマークが分離される(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        video_a = "/videos/a.mp4"
        video_b = "/videos/b.mp4"
        store.add(video_a, LoopBookmark(point_a_ms=0, point_b_ms=1000, name="動画A"))
        store.add(video_b, LoopBookmark(point_a_ms=0, point_b_ms=2000, name="動画B"))

        store2 = BookmarkStore(storage_path=path)
        assert len(store2.get_bookmarks(video_a)) == 1
        assert store2.get_bookmarks(video_a)[0].name == "動画A"
        assert len(store2.get_bookmarks(video_b)) == 1
        assert store2.get_bookmarks(video_b)[0].name == "動画B"

    def test_ファイルが存在しない場合は空で初期化される(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "nonexistent.json")
        assert store.get_bookmarks(VIDEO) == []

    def test_update_orderで並び順を変更できる(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        bm_a = LoopBookmark(point_a_ms=0, point_b_ms=1000, name="A")
        bm_b = LoopBookmark(point_a_ms=2000, point_b_ms=3000, name="B")
        bm_c = LoopBookmark(point_a_ms=4000, point_b_ms=5000, name="C")
        store.add(VIDEO, bm_a)
        store.add(VIDEO, bm_b)
        store.add(VIDEO, bm_c)

        # C → A → B の順に並び替え
        store.update_order(VIDEO, [bm_c.id, bm_a.id, bm_b.id])

        store2 = BookmarkStore(storage_path=path)
        bms = store2.get_bookmarks(VIDEO)
        assert bms[0].name == "C"
        assert bms[1].name == "A"
        assert bms[2].name == "B"

    def test_update_nameで名前を変更して永続化される(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, name="旧名前")
        store.add(VIDEO, bm)
        store.update_name(VIDEO, bm.id, "新名前")

        store2 = BookmarkStore(storage_path=path)
        assert store2.get_bookmarks(VIDEO)[0].name == "新名前"

    def test_update_repeat_countで繰り返し回数を変更できる(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add(VIDEO, bm)
        store.update_repeat_count(VIDEO, bm.id, 5)

        store2 = BookmarkStore(storage_path=path)
        assert store2.get_bookmarks(VIDEO)[0].repeat_count == 5

    def test_update_repeat_countが0以下の場合はValueError(self, tmp_path):
        path = tmp_path / "bookmarks.json"
        store = BookmarkStore(storage_path=path)
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add(VIDEO, bm)
        with pytest.raises(ValueError):
            store.update_repeat_count(VIDEO, bm.id, 0)
