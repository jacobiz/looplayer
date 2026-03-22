"""023-button-icons: US2 ABループボタンのアイコン化テスト。

対象ボタン: set_a_btn, set_b_btn, ab_toggle_btn, ab_reset_btn
検証内容:
- 各ボタンにアイコンが設定されている（FR-005〜FR-007）
- ab_toggle_btn が isCheckable() == True（FR-005）
- 初期状態で ab_toggle_btn.isChecked() == False
- toggle_ab_loop(True) 後に ab_toggle_btn.isChecked() == True（FR-005）
- reset_ab() 後に ab_toggle_btn.isChecked() == False
- 全4ボタンにツールチップが設定されている（FR-010）
"""
import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture(scope="module")
def player(tmp_path_factory, qapp):
    tmp_path = tmp_path_factory.mktemp("p2")
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    yield widget
    widget.timer.stop()
    widget._size_poll_timer.stop()
    widget.media_player.stop()


class TestSetABtnIcon:
    def test_set_a_btn_has_icon(self, player):
        """A点セットボタンにアイコンが設定されている（FR-006）。"""
        assert not player.set_a_btn.icon().isNull()

    def test_set_a_btn_has_tooltip(self, player):
        """A点セットボタンにツールチップが設定されている（FR-010）。"""
        assert player.set_a_btn.toolTip() != ""


class TestSetBBtnIcon:
    def test_set_b_btn_has_icon(self, player):
        """B点セットボタンにアイコンが設定されている（FR-007）。"""
        assert not player.set_b_btn.icon().isNull()

    def test_set_b_btn_has_tooltip(self, player):
        """B点セットボタンにツールチップが設定されている（FR-010）。"""
        assert player.set_b_btn.toolTip() != ""


class TestAbToggleBtnIcon:
    def test_ab_toggle_btn_has_icon(self, player):
        """ABループ切り替えボタンにアイコンが設定されている（FR-005）。"""
        assert not player.ab_toggle_btn.icon().isNull()

    def test_ab_toggle_btn_is_checkable(self, player):
        """ab_toggle_btn が checkable である（FR-005）。"""
        assert player.ab_toggle_btn.isCheckable()

    def test_ab_toggle_btn_initially_unchecked(self, player):
        """初期状態で ab_toggle_btn は unchecked（OFF）。"""
        player.reset_ab()
        assert not player.ab_toggle_btn.isChecked()

    def test_ab_toggle_btn_checked_after_toggle_true(self, player):
        """toggle_ab_loop(True) 後に ab_toggle_btn.isChecked() == True（FR-005）。"""
        player.toggle_ab_loop(True)
        assert player.ab_toggle_btn.isChecked()

    def test_ab_toggle_btn_unchecked_after_reset(self, player):
        """reset_ab() 後に ab_toggle_btn.isChecked() == False。"""
        player.toggle_ab_loop(True)
        player.reset_ab()
        assert not player.ab_toggle_btn.isChecked()

    def test_ab_toggle_btn_has_tooltip(self, player):
        """ab_toggle_btn にツールチップが設定されている（FR-010）。"""
        assert player.ab_toggle_btn.toolTip() != ""


class TestAbResetBtnIcon:
    def test_ab_reset_btn_has_icon(self, player):
        """ABリセットボタンにアイコンが設定されている（FR-005）。"""
        assert not player.ab_reset_btn.icon().isNull()

    def test_ab_reset_btn_has_tooltip(self, player):
        """ABリセットボタンにツールチップが設定されている（FR-010）。"""
        assert player.ab_reset_btn.toolTip() != ""
