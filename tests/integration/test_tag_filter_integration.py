"""T037: タグフィルタ UI の統合テスト。"""
from unittest.mock import patch
from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.player import VideoPlayer
from looplayer.widgets.bookmark_row import BookmarkRow


def _setup(player: VideoPlayer):
    player._current_video_path = "/test.mp4"
    player.bookmark_panel.load_video("/test.mp4")
    bm1 = LoopBookmark(point_a_ms=0, point_b_ms=1000, tags=["発音"])
    bm2 = LoopBookmark(point_a_ms=1000, point_b_ms=2000, tags=["リズム"])
    player._store.add("/test.mp4", bm1)
    player._store.add("/test.mp4", bm2)
    player.bookmark_panel._refresh_list()
    return bm1, bm2


class TestTagFilterUI:
    def test_tags_changed_signal_updates_store(self, player: VideoPlayer, qtbot):
        """タグ編集シグナルで bookmark_store が更新される。"""
        bm1, bm2 = _setup(player)
        # タグ変更をシミュレート
        player.bookmark_panel._on_tags_changed(bm1.id, ["文法"])
        bms = player._store.get_bookmarks("/test.mp4")
        bm = next(b for b in bms if b.id == bm1.id)
        assert "文法" in bm.tags

    def test_tag_filter_reduces_visible_count(self, player: VideoPlayer, qtbot):
        """タグフィルタで BookmarkPanel の表示件数が変わる。"""
        bm1, bm2 = _setup(player)
        # 全件表示
        assert player.bookmark_panel.list_widget.count() == 2
        # 「発音」でフィルタ
        player.bookmark_panel._active_tag_filter = ["発音"]
        player.bookmark_panel._refresh_list()
        assert player.bookmark_panel.list_widget.count() == 1

    def test_clear_filter_restores_all(self, player: VideoPlayer, qtbot):
        """フィルタクリアで全件に戻る。"""
        bm1, bm2 = _setup(player)
        player.bookmark_panel._active_tag_filter = ["発音"]
        player.bookmark_panel._refresh_list()
        player.bookmark_panel._active_tag_filter = []
        player.bookmark_panel._refresh_list()
        assert player.bookmark_panel.list_widget.count() == 2
