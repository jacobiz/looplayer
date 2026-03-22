"""023-button-icons: US3 その他ボタンのアイコン化テスト。

対象ボタン: save_bookmark_btn, _zoom_btn
検証内容:
- 各ボタンにアイコンが設定されている（FR-004, FR-008）
- _zoom_btn が isCheckable() == True（FR-008）
- _apply_btn_icon() で null アイコン返却時はアイコン未設定（FR-009フォールバック）
- save_bookmark_btn にツールチップが設定されている（FR-010）
- 全9ボタンにツールチップが設定されている（FR-010網羅確認）
"""
from unittest.mock import patch

import pytest
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QStyle
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture(scope="module")
def player(tmp_path_factory, qapp):
    tmp_path = tmp_path_factory.mktemp("p3")
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    yield widget
    widget.timer.stop()
    widget._size_poll_timer.stop()
    widget.media_player.stop()


class TestSaveBookmarkBtnIcon:
    def test_save_bookmark_btn_has_icon(self, player):
        """ブックマーク保存ボタンにアイコンが設定されている（FR-004）。"""
        assert not player.save_bookmark_btn.icon().isNull()

    def test_save_bookmark_btn_has_tooltip(self, player):
        """ブックマーク保存ボタンにツールチップが設定されている（FR-010）。"""
        assert player.save_bookmark_btn.toolTip() != ""


class TestZoomBtnIcon:
    def test_zoom_btn_has_icon(self, player):
        """ズームボタンにアイコンが設定されている（FR-008）。"""
        assert not player._zoom_btn.icon().isNull()

    def test_zoom_btn_is_checkable(self, player):
        """_zoom_btn が checkable である（FR-008）。"""
        assert player._zoom_btn.isCheckable()

    def test_zoom_btn_has_tooltip(self, player):
        """_zoom_btn にツールチップが設定されている（FR-010）。"""
        assert player._zoom_btn.toolTip() != ""


class TestFR009Fallback:
    def test_apply_btn_icon_no_seticon_when_null(self, player):
        """style() が null アイコンを返す場合、ボタンにアイコンを設定しない（FR-009）。"""
        # open_btn のアイコンをクリアしてテスト対象とする
        player.open_btn.setIcon(QIcon())
        assert player.open_btn.icon().isNull()

        with patch.object(player, "style") as mock_style:
            mock_style.return_value.standardIcon.return_value = QIcon()
            player._apply_btn_icon(player.open_btn, QStyle.StandardPixmap.SP_DirOpenIcon)

        # null アイコンを渡した場合、ボタンのアイコンは設定されない（isNull() のまま）
        assert player.open_btn.icon().isNull()

    def test_apply_btn_icon_sets_icon_when_valid(self, player):
        """style() が有効なアイコンを返す場合、ボタンにアイコンが設定される（FR-009）。"""
        player._apply_btn_icon(player.open_btn, QStyle.StandardPixmap.SP_DirOpenIcon)
        assert not player.open_btn.icon().isNull()


class TestFR010AllButtonsTooltips:
    """FR-010: 全9ボタンにツールチップが設定されている。"""

    def test_open_btn_has_tooltip(self, player):
        assert player.open_btn.toolTip() != ""

    def test_play_btn_has_tooltip(self, player):
        assert player.play_btn.toolTip() != ""

    def test_stop_btn_has_tooltip(self, player):
        assert player.stop_btn.toolTip() != ""

    def test_set_a_btn_has_tooltip(self, player):
        assert player.set_a_btn.toolTip() != ""

    def test_set_b_btn_has_tooltip(self, player):
        assert player.set_b_btn.toolTip() != ""

    def test_ab_toggle_btn_has_tooltip(self, player):
        assert player.ab_toggle_btn.toolTip() != ""

    def test_ab_reset_btn_has_tooltip(self, player):
        assert player.ab_reset_btn.toolTip() != ""

    def test_save_bookmark_btn_has_tooltip(self, player):
        assert player.save_bookmark_btn.toolTip() != ""

    def test_zoom_btn_has_tooltip(self, player):
        assert player._zoom_btn.toolTip() != ""
