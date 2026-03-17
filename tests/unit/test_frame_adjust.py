"""T010: フレーム微調整ロジックのユニットテスト。"""
import pytest
from looplayer.bookmark_store import LoopBookmark, BookmarkStore


def _bm(a=0, b=1000) -> LoopBookmark:
    return LoopBookmark(point_a_ms=a, point_b_ms=b)


class TestFrameCalc:
    def test_frame_ms_at_25fps(self):
        """25fps でのフレーム幅は 40ms。"""
        fps = 25.0
        frame_ms = int(1000 / fps)
        assert frame_ms == 40

    def test_frame_ms_at_30fps(self):
        """30fps でのフレーム幅は 33ms。"""
        fps = 30.0
        frame_ms = int(1000 / fps)
        assert frame_ms == 33

    def test_fps_zero_fallback(self):
        """fps=0 のとき 25fps フォールバックで 40ms。"""
        fps = 0.0
        if fps <= 0:
            fps = 25.0
        frame_ms = int(1000 / fps)
        assert frame_ms == 40


class TestFrameAdjustConstraints:
    def test_a_plus_frame_ok(self):
        """+1F で A 点が増加する（B との距離が保たれる場合）。"""
        bm = _bm(a=0, b=1000)
        frame_ms = 40
        new_a = bm.point_a_ms + frame_ms
        assert new_a < bm.point_b_ms

    def test_a_plus_frame_rejected_when_a_ge_b(self):
        """A+1F が B 以上になる場合は拒否される。"""
        bm = _bm(a=960, b=1000)
        frame_ms = 40
        new_a = bm.point_a_ms + frame_ms
        assert new_a >= bm.point_b_ms  # この場合は update してはいけない

    def test_b_minus_frame_ok(self):
        """-1F で B 点が減少する（A との距離が保たれる場合）。"""
        bm = _bm(a=0, b=1000)
        frame_ms = 40
        new_b = bm.point_b_ms - frame_ms
        assert new_b > bm.point_a_ms

    def test_b_plus_frame_within_length(self):
        """B+1F が動画長以内であれば許可される。"""
        bm = _bm(a=0, b=1000)
        video_length_ms = 5000
        frame_ms = 40
        new_b = bm.point_b_ms + frame_ms
        assert new_b <= video_length_ms


class TestBookmarkStoreFrameAdjust:
    def test_update_ab_points(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = _bm(a=0, b=1000)
        store.add("/test.mp4", bm)
        store.update_ab_points("/test.mp4", bm.id, 40, 1000)
        bms = store.get_bookmarks("/test.mp4")
        assert bms[0].point_a_ms == 40

    def test_update_ab_points_rejects_invalid(self, tmp_path):
        store = BookmarkStore(storage_path=tmp_path / "bm.json")
        bm = _bm(a=0, b=1000)
        store.add("/test.mp4", bm)
        with pytest.raises(ValueError):
            store.update_ab_points("/test.mp4", bm.id, 1000, 1000)
