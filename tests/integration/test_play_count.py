"""T025: 練習カウンターの統合テスト。"""
from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.player import VideoPlayer


def _setup(player: VideoPlayer):
    player._current_video_path = "/test.mp4"
    player.bookmark_panel.load_video("/test.mp4")
    bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
    player._store.add("/test.mp4", bm)
    player.bookmark_panel._refresh_list()
    return bm


class TestPlayCount:
    def test_increment_play_count(self, player: VideoPlayer, qtbot, tmp_path):
        """B点到達で play_count が 1 増える。"""
        bm = _setup(player)
        player._store.increment_play_count("/test.mp4", bm.id)
        bms = player._store.get_bookmarks("/test.mp4")
        assert bms[0].play_count == 1

    def test_play_count_persisted(self, player: VideoPlayer, qtbot, tmp_path):
        """JSON に保存されて読み直しても play_count が保持される。"""
        bm = _setup(player)
        player._store.increment_play_count("/test.mp4", bm.id)
        player._store.increment_play_count("/test.mp4", bm.id)
        # 再読み込み
        from looplayer.bookmark_store import BookmarkStore
        store2 = BookmarkStore(storage_path=player._store._path)
        bms = store2.get_bookmarks("/test.mp4")
        assert bms[0].play_count == 2

    def test_reset_play_count(self, player: VideoPlayer, qtbot):
        """play_count_reset シグナルで play_count が 0 になる。"""
        bm = _setup(player)
        player._store.increment_play_count("/test.mp4", bm.id)
        player._on_play_count_reset(bm.id)
        bms = player._store.get_bookmarks("/test.mp4")
        assert bms[0].play_count == 0
