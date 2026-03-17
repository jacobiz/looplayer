"""T021: 連続再生モード（1周停止 / 無限ループ）の統合テスト。"""
from unittest.mock import patch, MagicMock
from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.sequential import SequentialPlayState
from looplayer.player import VideoPlayer


def _add_bookmarks(player: VideoPlayer, count: int = 2):
    player._current_video_path = "/test.mp4"
    player.bookmark_panel.load_video("/test.mp4")
    for i in range(count):
        bm = LoopBookmark(point_a_ms=i * 2000, point_b_ms=i * 2000 + 1000)
        player._store.add("/test.mp4", bm)
    player.bookmark_panel._refresh_list()


class TestOneRoundMode:
    def test_one_round_mode_stops_on_none(self, player: VideoPlayer, qtbot):
        """on_b_reached が None を返したとき連続再生が終了する。"""
        _add_bookmarks(player)
        bms = player._store.get_bookmarks("/test.mp4")
        state = SequentialPlayState(bookmarks=bms, one_round_mode=True)
        player._seq_state = state

        # bm[0] → bm[1] への遷移
        state.on_b_reached()
        # bm[1] 最終 → None
        result = state.on_b_reached()
        assert result is None

        # player は None を受け取って _stop_seq_play を呼ぶべき
        player._stop_seq_play()
        assert player._seq_state is None

    def test_infinite_mode_does_not_stop(self, player: VideoPlayer, qtbot):
        """無限ループモードでは on_b_reached が常に int を返す。"""
        _add_bookmarks(player)
        bms = player._store.get_bookmarks("/test.mp4")
        state = SequentialPlayState(bookmarks=bms, one_round_mode=False)
        player._seq_state = state
        # 複数周回しても None にならない
        for _ in range(4):
            result = state.on_b_reached()
            assert result is not None

    def test_seq_mode_persisted_to_settings(self, player: VideoPlayer, qtbot):
        """モード変更が app_settings に保存される。"""
        player._on_seq_mode_toggled(True)
        assert player._app_settings.sequential_play_mode == "one_round"
        player._on_seq_mode_toggled(False)
        assert player._app_settings.sequential_play_mode == "infinite"
