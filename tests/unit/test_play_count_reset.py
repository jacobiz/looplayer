"""T026: 再生回数リセットのユニットテスト。"""
from looplayer.bookmark_store import BookmarkStore, LoopBookmark


class TestPlayCountReset:
    def test_reset_sets_to_zero(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.increment_play_count("/test.mp4", bm.id)
        store.increment_play_count("/test.mp4", bm.id)
        store.reset_play_count("/test.mp4", bm.id)
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].play_count == 0

    def test_reset_persisted(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        store.add("/test.mp4", bm)
        store.increment_play_count("/test.mp4", bm.id)
        store.reset_play_count("/test.mp4", bm.id)
        store2 = BookmarkStore(storage_path=tmp_path / "bm.json")
        bms = store2.get_bookmarks("/test.mp4")
        assert bms[0].play_count == 0
