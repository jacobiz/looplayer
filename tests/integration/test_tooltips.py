"""016-p1-features: F-502 ツールチップの充実 統合テスト。

対象スコープは FR-304 の最小スコープ。
既存ツールチップ（bookmark.row.memo_tip / delete_tip / enabled_tip）は対象外。
"""
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.player import VideoPlayer
from looplayer.widgets.bookmark_row import BookmarkRow


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


@pytest.fixture
def bookmark_row(qtbot: QtBot, tmp_path: Path) -> BookmarkRow:
    bm = LoopBookmark(point_a_ms=0, point_b_ms=5000, name="テスト")
    row = BookmarkRow(bm)
    qtbot.addWidget(row)
    yield row


class TestMainWindowTooltips:
    """player.py 内の主要コントロールにツールチップが設定されている。"""

    def test_play_btn_has_tooltip(self, player):
        assert player.play_btn.toolTip() != ""

    def test_seek_slider_has_tooltip(self, player):
        assert player.seek_slider.toolTip() != ""

    def test_volume_slider_has_tooltip(self, player):
        assert player.volume_slider.toolTip() != ""

    def test_set_a_btn_has_tooltip(self, player):
        assert player.set_a_btn.toolTip() != ""

    def test_set_b_btn_has_tooltip(self, player):
        assert player.set_b_btn.toolTip() != ""

    def test_ab_toggle_btn_has_tooltip(self, player):
        assert player.ab_toggle_btn.toolTip() != ""


class TestBookmarkRowTooltips:
    """bookmark_row.py 内のコントロールにツールチップが設定されている。"""

    def test_frame_a_minus_btn_has_tooltip(self, bookmark_row):
        assert bookmark_row.frame_a_minus_btn.toolTip() != ""

    def test_frame_a_plus_btn_has_tooltip(self, bookmark_row):
        assert bookmark_row.frame_a_plus_btn.toolTip() != ""

    def test_frame_b_minus_btn_has_tooltip(self, bookmark_row):
        assert bookmark_row.frame_b_minus_btn.toolTip() != ""

    def test_frame_b_plus_btn_has_tooltip(self, bookmark_row):
        assert bookmark_row.frame_b_plus_btn.toolTip() != ""

    def test_pause_spin_has_tooltip(self, bookmark_row):
        assert bookmark_row.pause_spin.toolTip() != ""

    def test_tags_btn_has_tooltip(self, bookmark_row):
        assert bookmark_row.tags_btn.toolTip() != ""


class TestTooltipI18n:
    """ツールチップが i18n に対応している（空でない・未翻訳でない）。"""

    def test_main_window_tooltips_are_non_empty(self, player):
        controls = [
            ("play_btn", player.play_btn),
            ("seek_slider", player.seek_slider),
            ("volume_slider", player.volume_slider),
            ("set_a_btn", player.set_a_btn),
            ("set_b_btn", player.set_b_btn),
            ("ab_toggle_btn", player.ab_toggle_btn),
        ]
        for name, widget in controls:
            tip = widget.toolTip()
            assert tip != "", f"{name} のツールチップが空"
            assert "tooltip." not in tip, f"{name}: ツールチップが未翻訳キー: {tip}"

    def test_bookmark_row_tooltips_are_non_empty(self, bookmark_row):
        controls = [
            ("frame_a_minus_btn", bookmark_row.frame_a_minus_btn),
            ("frame_a_plus_btn", bookmark_row.frame_a_plus_btn),
            ("frame_b_minus_btn", bookmark_row.frame_b_minus_btn),
            ("frame_b_plus_btn", bookmark_row.frame_b_plus_btn),
            ("pause_spin", bookmark_row.pause_spin),
            ("tags_btn", bookmark_row.tags_btn),
        ]
        for name, widget in controls:
            tip = widget.toolTip()
            assert tip != "", f"{name} のツールチップが空"
            assert "tooltip." not in tip, f"{name}: ツールチップが未翻訳キー: {tip}"
