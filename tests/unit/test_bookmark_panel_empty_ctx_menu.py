"""Tests for BookmarkPanel empty area context menu (US3)."""
import pytest
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QMenu, QListWidgetItem
from PyQt6.QtCore import QPoint, Qt

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t


VIDEO = "/test/video.mp4"


def make_store(tmp_path):
    return BookmarkStore(storage_path=tmp_path / "bm.json")


def make_panel(store, qapp):
    from looplayer.widgets.bookmark_panel import BookmarkPanel
    return BookmarkPanel(store=store)


def make_bm(a_ms=1000, b_ms=2000, name="bm"):
    return LoopBookmark(point_a_ms=a_ms, point_b_ms=b_ms, name=name)


def collect_panel_menu_actions(panel, pos):
    """_show_panel_context_menu を呼び出してアクションを収集する。"""
    actions = {}

    def capture_exec(menu_self, *args, **kwargs):
        for action in menu_self.actions():
            if not action.isSeparator():
                actions[action.text()] = action
        return None

    with patch.object(QMenu, "exec", capture_exec):
        panel._show_panel_context_menu(pos)

    return actions


class TestPanelContextMenuVisibility:
    def test_menu_shown_when_clicking_empty_area(self, qapp, tmp_path):
        """空白クリック時はメニューが生成されること。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)

        # pos that doesn't correspond to any item
        pos = QPoint(10, 10)  # empty area (no items loaded)

        actions = collect_panel_menu_actions(panel, pos)
        # Should have import and export actions
        assert t("ctx.import_bookmarks") in actions

    def test_menu_not_shown_when_clicking_on_item(self, qapp, tmp_path):
        """行クリック時はメニューが無視されること（itemAt が None でないとき）。"""
        store = make_store(tmp_path)
        bm = make_bm()
        store.add(VIDEO, bm)
        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        # Mock itemAt to return a non-None item
        mock_item = MagicMock()
        with patch.object(panel.list_widget, "itemAt", return_value=mock_item):
            actions = collect_panel_menu_actions(panel, QPoint(10, 10))

        # Menu should not be shown (no actions collected)
        assert len(actions) == 0


class TestPanelContextMenuSignals:
    def test_import_requested_signal_emitted(self, qapp, tmp_path):
        """import_requested シグナルがメニューから発火されること。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)

        received = []
        panel.import_requested.connect(lambda: received.append(True))

        actions = collect_panel_menu_actions(panel, QPoint(10, 10))
        assert t("ctx.import_bookmarks") in actions
        actions[t("ctx.import_bookmarks")].trigger()

        assert received == [True]

    def test_export_signal_emitted_when_bookmarks_exist(self, qapp, tmp_path):
        """ブックマーク1件以上のとき export_from_panel_requested が発火されること。"""
        store = make_store(tmp_path)
        bm = make_bm()
        store.add(VIDEO, bm)
        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)

        received = []
        panel.export_from_panel_requested.connect(lambda: received.append(True))

        # Mock itemAt to return None (simulate click in empty area)
        with patch.object(panel.list_widget, "itemAt", return_value=None):
            actions = collect_panel_menu_actions(panel, QPoint(10, 10))

        assert t("ctx.export_bookmarks") in actions
        actions[t("ctx.export_bookmarks")].trigger()

        assert received == [True]

    def test_export_disabled_when_no_bookmarks(self, qapp, tmp_path):
        """ブックマーク0件時に「エクスポート」が disabled であること。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)
        panel.load_video(VIDEO)  # no bookmarks added

        actions = collect_panel_menu_actions(panel, QPoint(10, 10))
        assert t("ctx.export_bookmarks") in actions
        assert not actions[t("ctx.export_bookmarks")].isEnabled()

    def test_export_disabled_when_no_video_loaded(self, qapp, tmp_path):
        """動画未ロード時に「エクスポート」が disabled であること。"""
        store = make_store(tmp_path)
        panel = make_panel(store, qapp)
        # No load_video called

        actions = collect_panel_menu_actions(panel, QPoint(10, 10))
        assert t("ctx.export_bookmarks") in actions
        assert not actions[t("ctx.export_bookmarks")].isEnabled()
