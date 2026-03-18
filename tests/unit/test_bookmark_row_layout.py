"""BookmarkRow レイアウトテスト — スピンボックス幅（US4）。"""
import pytest
from PyQt6.QtWidgets import QApplication

from looplayer.bookmark_store import LoopBookmark
from looplayer.widgets.bookmark_row import BookmarkRow


@pytest.fixture
def row(qtbot):
    bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="テスト")
    widget = BookmarkRow(bm)
    qtbot.addWidget(widget)
    return widget


class TestSpinboxWidth:
    """繰返し・ポーズスピンボックスの幅テスト（US4）。"""

    def test_repeat_spin_minimum_width(self, row):
        """repeat_spin の minimumWidth が 68px 以上であること。"""
        assert row.repeat_spin.minimumWidth() >= 68, (
            f"repeat_spin.minimumWidth() = {row.repeat_spin.minimumWidth()} < 68"
        )

    def test_pause_spin_minimum_width(self, row):
        """pause_spin の minimumWidth が 75px 以上であること。"""
        assert row.pause_spin.minimumWidth() >= 75, (
            f"pause_spin.minimumWidth() = {row.pause_spin.minimumWidth()} < 75"
        )

    def test_repeat_spin_not_fixed_width(self, row):
        """repeat_spin が fixedWidth でないこと（最大幅が QWIDGETSIZE_MAX）。"""
        from PyQt6.QtWidgets import QSizePolicy
        # fixedWidth 設定時は minimumWidth == maximumWidth になる
        # setMinimumWidth に変更後は maximumWidth が QWIDGETSIZE_MAX (16777215) になる
        assert row.repeat_spin.maximumWidth() > 68, (
            "repeat_spin が fixedWidth のままになっている"
        )
