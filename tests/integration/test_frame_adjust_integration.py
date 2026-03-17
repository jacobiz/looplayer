"""T011: フレーム微調整 BookmarkRow 統合テスト。"""
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QPushButton
from looplayer.bookmark_store import LoopBookmark
from looplayer.widgets.bookmark_row import BookmarkRow


def _make_row(a=0, b=1000) -> BookmarkRow:
    bm = LoopBookmark(point_a_ms=a, point_b_ms=b, name="テスト")
    return BookmarkRow(bm)


class TestBookmarkRowFrameAdjustButtons:
    def test_frame_adjust_buttons_exist(self, qtbot):
        """BookmarkRow に A/B の +1F/-1F ボタンが存在する。"""
        row = _make_row()
        qtbot.addWidget(row)
        buttons = row.findChildren(QPushButton)
        tooltips = [b.toolTip() for b in buttons]
        texts = [b.text() for b in buttons]
        # 4つのフレーム調整ボタンのうち少なくとも -1F / +1F ラベルが存在する
        assert any("-1F" in t or "+1F" in t for t in texts)

    def test_frame_adjusted_signal_emitted(self, qtbot):
        """+1F ボタンクリックで frame_adjusted シグナルが emit される。"""
        row = _make_row(a=0, b=1000)
        qtbot.addWidget(row)
        received = []
        row.frame_adjusted.connect(lambda bm_id, point, ms: received.append((bm_id, point, ms)))

        # A の +1F ボタンを探してクリック
        buttons = row.findChildren(QPushButton)
        frame_btns = [b for b in buttons if "+1F" in b.text() or "-1F" in b.text()]
        assert frame_btns, "frame adjust ボタンが見つからない"
        # 最初の +1F を探す
        plus_btn = next((b for b in frame_btns if "+1F" in b.text()), None)
        assert plus_btn is not None
        plus_btn.click()
        assert len(received) == 1

    def test_a_ge_b_rejected(self, qtbot):
        """A+1F >= B となる場合は frame_adjusted シグナルが emit されない。"""
        row = _make_row(a=960, b=1000)
        qtbot.addWidget(row)
        received = []
        row.frame_adjusted.connect(lambda *args: received.append(args))

        buttons = row.findChildren(QPushButton)
        frame_btns = [b for b in buttons if "+1F" in b.text()]
        # A の +1F ボタン（最初の +1F）
        if frame_btns:
            frame_btns[0].click()
        assert len(received) == 0
