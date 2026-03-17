"""T036: ブックマークタグ機能のユニットテスト。"""
from looplayer.bookmark_store import BookmarkStore, LoopBookmark


class TestTagStorage:
    def test_tags_saved_and_loaded(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, tags=["発音", "リズム"])
        store.add("/test.mp4", bm)
        store2 = BookmarkStore(storage_path=tmp_path / "bm.json")
        bms = store2.get_bookmarks("/test.mp4")
        assert bms[0].tags == ["発音", "リズム"]

    def test_update_tags(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.update_tags("/test.mp4", bm.id, ["文法", "イントネーション"])
        bms = store.get_bookmarks("/test.mp4")
        assert "文法" in bms[0].tags

    def test_tags_trimmed(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.update_tags("/test.mp4", bm.id, ["  発音  ", "  "])
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].tags == ["発音"]

    def test_empty_tags_removed(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.update_tags("/test.mp4", bm.id, ["", " ", "発音"])
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].tags == ["発音"]


class TestTagFilterLogic:
    def _make_bms(self):
        return [
            LoopBookmark(point_a_ms=0, point_b_ms=1000, tags=["発音"]),
            LoopBookmark(point_a_ms=1000, point_b_ms=2000, tags=["リズム"]),
            LoopBookmark(point_a_ms=2000, point_b_ms=3000, tags=["発音", "リズム"]),
            LoopBookmark(point_a_ms=3000, point_b_ms=4000, tags=[]),
        ]

    def _or_filter(self, bms, active_tags):
        if not active_tags:
            return bms
        return [bm for bm in bms if any(t in bm.tags for t in active_tags)]

    def test_empty_filter_returns_all(self):
        bms = self._make_bms()
        result = self._or_filter(bms, [])
        assert len(result) == 4

    def test_single_tag_filter(self):
        bms = self._make_bms()
        result = self._or_filter(bms, ["発音"])
        assert len(result) == 2  # bm[0] + bm[2]

    def test_or_logic_multiple_tags(self):
        bms = self._make_bms()
        result = self._or_filter(bms, ["発音", "リズム"])
        assert len(result) == 3  # bm[0] + bm[1] + bm[2]

    def test_unmatched_tag_returns_empty(self):
        bms = self._make_bms()
        result = self._or_filter(bms, ["存在しないタグ"])
        assert len(result) == 0
