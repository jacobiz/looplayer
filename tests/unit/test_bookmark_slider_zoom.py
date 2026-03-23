"""F-105: ABループ区間のズーム表示（BookmarkSlider zoom）ユニットテスト。"""
import pytest
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from looplayer.widgets.bookmark_slider import BookmarkSlider


@pytest.fixture
def slider(qtbot: QtBot) -> BookmarkSlider:
    s = BookmarkSlider(Qt.Orientation.Horizontal)
    s.setMinimum(0)
    s.setMaximum(100000)
    s._duration_ms = 100000
    qtbot.addWidget(s)
    s.resize(800, 30)
    return s


class TestBookmarkSliderZoomInit:
    """ズームフィールドの初期化確認。"""

    def test_zoom_enabled_false_by_default(self, slider):
        """初期状態では zoom_enabled は False。"""
        assert slider.zoom_enabled is False

    def test_zoom_start_ms_zero_by_default(self, slider):
        """初期状態では _zoom_start_ms は 0。"""
        assert slider._zoom_start_ms == 0

    def test_zoom_end_ms_zero_by_default(self, slider):
        """初期状態では _zoom_end_ms は 0。"""
        assert slider._zoom_end_ms == 0


class TestBookmarkSliderSetZoom:
    """set_zoom() / clear_zoom() の動作確認。"""

    def test_set_zoom_enables_zoom_mode(self, slider):
        """set_zoom() 後に zoom_enabled == True。"""
        slider.set_zoom(10000, 20000)
        assert slider.zoom_enabled is True

    def test_set_zoom_stores_range(self, slider):
        """set_zoom() で _zoom_start_ms と _zoom_end_ms が設定される。"""
        slider.set_zoom(5000, 15000)
        assert slider._zoom_start_ms == 5000
        assert slider._zoom_end_ms == 15000

    def test_clear_zoom_disables_zoom_mode(self, slider):
        """clear_zoom() 後に zoom_enabled == False。"""
        slider.set_zoom(10000, 20000)
        slider.clear_zoom()
        assert slider.zoom_enabled is False

    def test_set_zoom_invalid_range_raises_value_error(self, slider):
        """start_ms >= end_ms の場合に ValueError が発生する。"""
        with pytest.raises(ValueError):
            slider.set_zoom(20000, 10000)

    def test_set_zoom_equal_range_raises_value_error(self, slider):
        """start_ms == end_ms の場合にも ValueError が発生する。"""
        with pytest.raises(ValueError):
            slider.set_zoom(10000, 10000)


class TestBookmarkSliderZoomCoordinates:
    """ズームモード中の座標変換確認。"""

    def test_ms_to_x_maps_zoom_start_to_groove_left(self, slider):
        """ズームモード中、zoom_start_ms が groove の左端にマップされる。"""
        slider.set_zoom(20000, 40000)
        groove = slider._groove_rect()
        x = slider._ms_to_x(20000, groove)
        assert x == groove.left()

    def test_ms_to_x_maps_zoom_end_to_groove_right(self, slider):
        """ズームモード中、zoom_end_ms が groove の右端にマップされる。"""
        slider.set_zoom(20000, 40000)
        groove = slider._groove_rect()
        x = slider._ms_to_x(40000, groove)
        assert x == groove.left() + groove.width()

    def test_ms_to_x_normal_mode_uses_full_duration(self, slider):
        """通常モードでは duration_ms 全体がマップ対象。"""
        groove = slider._groove_rect()
        x_end = slider._ms_to_x(100000, groove)
        assert x_end == groove.left() + groove.width()

    def test_x_to_ms_inverts_ms_to_x_in_zoom_mode(self, slider):
        """ズームモード中: x_to_ms(ms_to_x(ms)) ≈ ms（誤差1ms 以内）。"""
        slider.set_zoom(20000, 40000)
        groove = slider._groove_rect()
        for ms in [20000, 25000, 30000, 35000, 40000]:
            x = slider._ms_to_x(ms, groove)
            recovered = slider._x_to_ms(x, groove)
            assert abs(recovered - ms) <= 1, f"ms={ms}, recovered={recovered}"

    def test_zoom_mode_higher_resolution_than_normal(self, slider):
        """ズームモードでは同じピクセル幅でより細かい ms 単位を表現できる。"""
        groove = slider._groove_rect()
        if groove.width() <= 0:
            pytest.skip("グルーブ幅が 0 — 描画環境なし")
        # 通常モードでの 1px あたりの ms
        normal_ms_per_px = 100000 / groove.width()
        # ズームモード（20000ms 区間）での 1px あたりの ms
        slider.set_zoom(10000, 30000)
        zoom_range = slider._zoom_end_ms - slider._zoom_start_ms  # 20000
        zoom_ms_per_px = zoom_range / groove.width()
        assert zoom_ms_per_px < normal_ms_per_px


class TestBookmarkSliderZoomPlayerIntegration:
    """VideoPlayer との統合: ズームボタンの存在確認。"""

    def test_zoom_btn_exists_on_player(self, qtbot):
        """VideoPlayer に _zoom_btn が存在する。"""
        from pathlib import Path
        from looplayer.bookmark_store import BookmarkStore
        from looplayer.player import VideoPlayer
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(storage_path=Path(tmp) / "bookmarks.json")
            player = VideoPlayer(store=store, recent_storage=Path(tmp) / "recent.json")
            qtbot.addWidget(player)
            assert hasattr(player, "_zoom_btn")
            player.timer.stop()
            player.media_player.stop()

    def test_zoom_btn_disabled_without_ab(self, qtbot):
        """AB 点未設定時はズームボタンが無効。"""
        from pathlib import Path
        from looplayer.bookmark_store import BookmarkStore
        from looplayer.player import VideoPlayer
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(storage_path=Path(tmp) / "bookmarks.json")
            player = VideoPlayer(store=store, recent_storage=Path(tmp) / "recent.json")
            qtbot.addWidget(player)
            assert not player._zoom_btn.isEnabled()
            player.timer.stop()
            player.media_player.stop()


# ── 024: set_position_ms テスト ──────────────────────────────────────────────

@pytest.fixture
def slider_pos(qtbot: QtBot) -> BookmarkSlider:
    """本番環境と同じ range (0-1000) を使う set_position_ms 専用フィクスチャ。"""
    s = BookmarkSlider(Qt.Orientation.Horizontal)
    s.setMinimum(0)
    s.setMaximum(1000)
    s._duration_ms = 100000
    qtbot.addWidget(s)
    s.resize(800, 30)
    return s


class TestSetPositionMs:
    """set_position_ms() のユニットテスト。"""

    def test_zoom_active_position_in_range(self, slider_pos):
        """ズームモード中、範囲内の中間位置が value == 500 にマップされる。"""
        slider_pos.set_zoom(20000, 40000)
        slider_pos.set_position_ms(30000)
        assert slider_pos.value() == 500

    def test_zoom_active_position_at_start(self, slider_pos):
        """ズームモード中、zoom_start_ms → value == 0（左端）。"""
        slider_pos.set_zoom(20000, 40000)
        slider_pos.set_position_ms(20000)
        assert slider_pos.value() == 0

    def test_zoom_active_position_at_end(self, slider_pos):
        """ズームモード中、zoom_end_ms → value == 1000（右端）。"""
        slider_pos.set_zoom(20000, 40000)
        slider_pos.set_position_ms(40000)
        assert slider_pos.value() == 1000

    def test_zoom_active_position_before_range(self, slider_pos):
        """ズームモード中、範囲より前 → Qt が value を 0 にクリップ（左端固定）。"""
        slider_pos.set_zoom(20000, 40000)
        slider_pos.set_position_ms(10000)
        assert slider_pos.value() == 0

    def test_zoom_active_position_after_range(self, slider_pos):
        """ズームモード中、範囲より後 → Qt が value を 1000 にクリップ（右端固定）。"""
        slider_pos.set_zoom(20000, 40000)
        slider_pos.set_position_ms(50000)
        assert slider_pos.value() == 1000

    def test_no_zoom_normal_mapping(self, slider_pos):
        """ズームなし時、duration_ms の 50% → value == 500。"""
        slider_pos.set_position_ms(50000)
        assert slider_pos.value() == 500

    def test_no_zoom_zero_duration(self, slider_pos):
        """duration_ms == 0 の場合は value == 0（ゼロ除算安全）。"""
        slider_pos._duration_ms = 0
        slider_pos.set_position_ms(0)
        assert slider_pos.value() == 0

    # US2: ズーム範囲外での現在位置の認識

    def test_zoom_before_range_fixed_to_left_end(self, slider_pos):
        """ズーム範囲より前の現在位置 → マーカーが左端に固定（FR-004）。"""
        slider_pos.set_zoom(30000, 60000)
        slider_pos.set_position_ms(10000)  # ズーム開始より前
        assert slider_pos.value() == 0

    def test_zoom_after_range_fixed_to_right_end(self, slider_pos):
        """ズーム範囲より後の現在位置 → マーカーが右端に固定（FR-004）。"""
        slider_pos.set_zoom(30000, 60000)
        slider_pos.set_position_ms(80000)  # ズーム終了より後
        assert slider_pos.value() == slider_pos.maximum()

    def test_zoom_duration_zero_with_zoom_enabled(self, slider_pos):
        """duration_ms == 0 かつズーム有効時は ゼロ除算なし（ズームが優先）。"""
        slider_pos._duration_ms = 0
        slider_pos.set_zoom(1000, 2000)
        slider_pos.set_position_ms(1500)  # ズーム範囲中央
        assert slider_pos.value() == 500
