"""AB 点シークバー統合テスト（US2 / US3）。"""
import pytest
from pathlib import Path

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    widget.show()
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


class TestAbPreviewIntegration:
    """set_point_a/b 呼び出し後にシークバーが更新される統合テスト（US2）。"""

    def test_set_point_a_updates_seekbar_preview(self, player, qtbot):
        """set_point_a() 呼び出し後に seek_slider._ab_preview_a が設定される。"""
        player.ab_point_a = 3000
        player.seek_slider.set_ab_preview(player.ab_point_a, player.ab_point_b)
        assert player.seek_slider._ab_preview_a == 3000

    def test_set_point_b_updates_seekbar_preview(self, player, qtbot):
        """set_point_b() 呼び出し後に seek_slider._ab_preview_b が設定される。"""
        player.ab_point_a = 2000
        player.ab_point_b = 7000
        player.seek_slider.set_ab_preview(player.ab_point_a, player.ab_point_b)
        assert player.seek_slider._ab_preview_a == 2000
        assert player.seek_slider._ab_preview_b == 7000

    def test_clear_ab_preview_clears_seekbar(self, player, qtbot):
        """AB 点クリア後にシークバーのプレビューも消える。"""
        player.seek_slider.set_ab_preview(1000, 5000)
        player.seek_slider.set_ab_preview(None, None)
        assert player.seek_slider._ab_preview_a is None
        assert player.seek_slider._ab_preview_b is None


class TestAbDragIntegration:
    """AB 点ドラッグ完了後に Player の ab_point_a/b が更新される統合テスト（US3）。"""

    def test_on_ab_drag_finished_updates_point_a(self, player, qtbot):
        """_on_ab_drag_finished('a', 3000) 呼び出し後に ab_point_a == 3000 になる。"""
        player.ab_point_a = 1000
        player.ab_point_b = 8000
        player.seek_slider.set_ab_preview(1000, 8000)
        player._on_ab_drag_finished("a", 3000)
        assert player.ab_point_a == 3000
        assert player.seek_slider._ab_preview_a == 3000

    def test_on_ab_drag_finished_updates_point_b(self, player, qtbot):
        """_on_ab_drag_finished('b', 6000) 呼び出し後に ab_point_b == 6000 になる。"""
        player.ab_point_a = 1000
        player.ab_point_b = 8000
        player.seek_slider.set_ab_preview(1000, 8000)
        player._on_ab_drag_finished("b", 6000)
        assert player.ab_point_b == 6000
        assert player.seek_slider._ab_preview_b == 6000
