"""US1: BookmarkSlider ユニットテスト。"""
import pytest
from PyQt6.QtCore import Qt, QRect

from looplayer.widgets.bookmark_slider import BookmarkSlider


@pytest.fixture
def slider(qtbot):
    s = BookmarkSlider(Qt.Orientation.Horizontal)
    s.setRange(0, 1000)
    s.resize(400, 20)
    qtbot.addWidget(s)
    return s


class TestMsToX:
    """ミリ秒→X座標変換のテスト。"""

    def test_zero_ms_returns_groove_left(self, slider):
        groove = QRect(10, 5, 380, 10)
        x = slider._ms_to_x(0, groove)
        assert x == groove.left()

    def test_full_duration_returns_groove_right(self, slider):
        groove = QRect(10, 5, 380, 10)
        x = slider._ms_to_x(10000, groove, duration_ms=10000)
        assert x == groove.left() + groove.width()

    def test_half_duration_returns_center(self, slider):
        groove = QRect(0, 0, 400, 10)
        x = slider._ms_to_x(5000, groove, duration_ms=10000)
        assert x == 200

    def test_clamps_below_zero(self, slider):
        groove = QRect(10, 0, 380, 10)
        x = slider._ms_to_x(-100, groove, duration_ms=10000)
        assert x == groove.left()

    def test_clamps_above_duration(self, slider):
        groove = QRect(10, 0, 380, 10)
        x = slider._ms_to_x(20000, groove, duration_ms=10000)
        assert x == groove.left() + groove.width()


class TestSetBookmarks:
    """set_bookmarks() のテスト。"""

    def test_set_bookmarks_stores_data(self, slider):
        from looplayer.bookmark_store import LoopBookmark
        bms = [LoopBookmark(point_a_ms=0, point_b_ms=1000)]
        slider.set_bookmarks(bms, duration_ms=10000)
        assert slider._duration_ms == 10000
        assert len(slider._bookmarks) == 1

    def test_set_empty_bookmarks(self, slider):
        slider.set_bookmarks([], duration_ms=10000)
        assert len(slider._bookmarks) == 0

    def test_set_current_id_stored(self, slider):
        from looplayer.bookmark_store import LoopBookmark
        bm = LoopBookmark(point_a_ms=0, point_b_ms=1000)
        slider.set_bookmarks([bm], duration_ms=10000, current_id=bm.id)
        assert slider._current_id == bm.id

    def test_set_bookmarks_clips_beyond_duration(self, slider):
        """動画長を超える区間は描画データがクリップされる（FR-005 / Edge Case）。"""
        from looplayer.bookmark_store import LoopBookmark
        bm = LoopBookmark(point_a_ms=9000, point_b_ms=15000)
        slider.set_bookmarks([bm], duration_ms=10000)
        # 描画リストに含まれていること（描画時にクリップ）
        assert len(slider._bookmarks) == 1


class TestMinimumBarWidth:
    """最小バー幅のテスト（FR-005）。"""

    def test_min_width_applied_for_tiny_region(self, slider):
        groove = QRect(0, 0, 1000, 10)
        # 1ms/10000ms → 0.1px になるが最小4px にクランプ
        x1, x2 = slider._bar_x_range(a_ms=0, b_ms=1, groove=groove, duration_ms=10000)
        assert x2 - x1 >= 4


class TestClickDetection:
    """クリック時のブックマーク特定テスト（重複時は後ろ優先）。"""

    def test_click_selects_correct_bookmark(self, slider, qtbot):
        """バーをクリックすると bookmark_bar_clicked シグナルが発火する。"""
        from looplayer.bookmark_store import LoopBookmark
        bm = LoopBookmark(point_a_ms=0, point_b_ms=5000)
        slider.set_bookmarks([bm], duration_ms=10000)
        slider.show()

        clicked_ids = []
        slider.bookmark_bar_clicked.connect(clicked_ids.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        hit_x = groove.left() + groove.width() // 4  # 0〜5000ms の範囲内
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(hit_x, slider.height() // 2))
        assert len(clicked_ids) >= 1

    def test_overlap_selects_last_registered(self, slider, qtbot):
        """重複区間では最後に登録されたブックマーク（最前面）が選択される。"""
        from looplayer.bookmark_store import LoopBookmark
        bm1 = LoopBookmark(point_a_ms=0, point_b_ms=10000)
        bm2 = LoopBookmark(point_a_ms=0, point_b_ms=10000)
        slider.set_bookmarks([bm1, bm2], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        hit_id = slider._find_bookmark_at_x(groove.left() + groove.width() // 2)
        assert hit_id == bm2.id


class TestClickSeek:
    """シークバートラッククリックで seek_requested シグナルが emit されるテスト（US1）。"""

    def test_click_on_track_emits_seek_requested(self, slider, qtbot):
        """トラック中央クリックで seek_requested が duration の 40〜60% の ms 値で emit される。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        emitted = []
        slider.seek_requested.connect(emitted.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        center_x = groove.left() + groove.width() // 2
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(center_x, slider.height() // 2))
        assert len(emitted) == 1
        assert 4000 <= emitted[0] <= 6000

    def test_click_at_left_emits_small_ms(self, slider, qtbot):
        """groove 左端クリックで emit される ms が duration の 5% 以下。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        emitted = []
        slider.seek_requested.connect(emitted.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(groove.left(), slider.height() // 2))
        assert len(emitted) == 1
        assert emitted[0] <= 500  # 5% 以下

    def test_click_at_right_emits_large_ms(self, slider, qtbot):
        """groove 右端クリックで emit される ms が duration の 95% 以上。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        emitted = []
        slider.seek_requested.connect(emitted.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        right_x = groove.left() + groove.width()
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(right_x, slider.height() // 2))
        assert len(emitted) == 1
        assert emitted[0] >= 9500  # 95% 以上

    def test_click_when_duration_zero_does_not_emit(self, slider, qtbot):
        """duration=0 の状態でクリックしても seek_requested が emit されない。"""
        slider.set_bookmarks([], duration_ms=0)
        slider.resize(500, 30)
        slider.show()

        emitted = []
        slider.seek_requested.connect(emitted.append)

        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(250, slider.height() // 2))
        assert len(emitted) == 0


class TestDragSeek:
    """ドラッグ中のシークテスト（US1）。"""

    def test_click_sets_dragging_flag(self, slider, qtbot):
        """トラッククリック後に _dragging が True になる。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        mid_x = groove.left() + groove.width() // 2
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=QPoint(mid_x, slider.height() // 2))
        assert slider._dragging is True
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(mid_x, slider.height() // 2))

    def test_release_clears_dragging_flag(self, slider, qtbot):
        """mouseReleaseEvent 後に _dragging が False になる。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        mid = QPoint(groove.left() + groove.width() // 2, slider.height() // 2)
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=mid)
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=mid)
        assert slider._dragging is False

    def test_drag_emits_seek_requested_on_move(self, slider, qtbot):
        """_dragging=True の状態で mouseMoveEvent を送ると seek_requested が emit される。"""
        slider.set_bookmarks([], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        emitted = []
        slider.seek_requested.connect(emitted.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        start = QPoint(groove.left() + groove.width() // 4, slider.height() // 2)
        end = QPoint(groove.left() + groove.width() * 3 // 4, slider.height() // 2)
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=start)
        initial_count = len(emitted)
        QTest.mouseMove(slider, pos=end)
        # ドラッグで seek_requested が追加 emit されること
        assert len(emitted) > initial_count


class TestBookmarkBarClickRegression:
    """ブックマークバークリックが US1 実装後も正常動作するリグレッションテスト（US2）。"""

    def test_bookmark_bar_click_emits_bookmark_signal_not_seek(self, slider, qtbot):
        """ブックマークバーをクリックすると bookmark_bar_clicked が emit され seek_requested は emit されない。"""
        from looplayer.bookmark_store import LoopBookmark
        bm = LoopBookmark(point_a_ms=0, point_b_ms=5000)
        slider.set_bookmarks([bm], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        bm_clicked = []
        seek_emitted = []
        slider.bookmark_bar_clicked.connect(bm_clicked.append)
        slider.seek_requested.connect(seek_emitted.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        # ブックマーク区間（0〜5000ms）の中央をクリック
        hit_x = groove.left() + groove.width() // 4
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(hit_x, slider.height() // 2))
        assert len(bm_clicked) >= 1
        assert len(seek_emitted) == 0

    def test_track_click_outside_bar_does_not_emit_bookmark_signal(self, slider, qtbot):
        """ブックマークバー外のトラッククリックで bookmark_bar_clicked が emit されない。"""
        from looplayer.bookmark_store import LoopBookmark
        bm = LoopBookmark(point_a_ms=0, point_b_ms=2000)
        slider.set_bookmarks([bm], duration_ms=10000)
        slider.resize(500, 30)
        slider.show()

        bm_clicked = []
        slider.bookmark_bar_clicked.connect(bm_clicked.append)

        groove = slider._groove_rect()
        if groove.width() == 0:
            pytest.skip("ヘッドレス環境のためグルーブ幅が 0 です")
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest
        # ブックマーク区間（0〜2000ms）の外側（80% 付近）をクリック
        hit_x = groove.left() + int(groove.width() * 0.8)
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(hit_x, slider.height() // 2))
        assert len(bm_clicked) == 0
