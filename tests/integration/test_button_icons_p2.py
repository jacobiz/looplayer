"""023-button-icons + 027-minor-fixes: US2 ABループボタンのアイコン化テスト。

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
from PyQt6.QtWidgets import QStyle

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


# ── 027: B点アイコン対称性テスト ──────────────────────────────────────────────


class TestSetBBtnIconSymmetry:
    """_apply_btn_icon に渡された StandardPixmap 引数を記録してアイコンを検証する。

    QIcon.cacheKey() は呼び出しごとに新規オブジェクトが生成されるため cacheKey
    による直接比較が不安定。代わりに初期化時の引数をスパイで記録する方式を採用。
    """

    @pytest.fixture
    def player_with_icon_spy(self, tmp_path, qapp):
        """_apply_btn_icon の呼び出し引数を記録する専用 player fixture。"""
        from unittest.mock import patch
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        icon_calls: dict = {}
        original = VideoPlayer._apply_btn_icon

        def spy(self_player, btn, sp):
            icon_calls[id(btn)] = sp
            original(self_player, btn, sp)

        with patch.object(VideoPlayer, "_apply_btn_icon", spy):
            widget = VideoPlayer(store=store)

        yield widget, icon_calls
        widget.timer.stop()
        widget._size_poll_timer.stop()
        widget.media_player.stop()

    def test_set_b_btn_icon_matches_sp_media_skip_forward(self, player_with_icon_spy):
        """B点セットボタンのアイコンが SP_MediaSkipForward であること（FR-002）。"""
        widget, icon_calls = player_with_icon_spy
        assert icon_calls.get(id(widget.set_b_btn)) == QStyle.StandardPixmap.SP_MediaSkipForward

    def test_set_a_and_b_icons_are_symmetric_pair(self, player_with_icon_spy):
        """A点は SP_MediaSkipBackward、B点は SP_MediaSkipForward で左右対称のペアになること（FR-002）。"""
        widget, icon_calls = player_with_icon_spy
        assert icon_calls.get(id(widget.set_a_btn)) == QStyle.StandardPixmap.SP_MediaSkipBackward
        assert icon_calls.get(id(widget.set_b_btn)) == QStyle.StandardPixmap.SP_MediaSkipForward
