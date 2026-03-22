"""023-button-icons: US1 主要再生ボタンのアイコン化テスト。

対象ボタン: open_btn, play_btn, stop_btn
検証内容:
- 各ボタンにアイコンが設定されている（FR-001〜FR-003）
- メディア未ロード時に play_btn が disabled（FR-001）
- _update_play_btn_appearance() が play/pause アイコンを正しく切り替える（FR-001）
- 全3ボタンにツールチップが設定されている（FR-010）
"""
import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture(scope="module")
def player(tmp_path_factory, qapp):
    tmp_path = tmp_path_factory.mktemp("p1")
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    yield widget
    widget.timer.stop()
    widget._size_poll_timer.stop()
    widget.media_player.stop()


class TestOpenBtnIcon:
    def test_open_btn_has_icon(self, player):
        """開くボタンにアイコンが設定されている（FR-003）。"""
        assert not player.open_btn.icon().isNull()

    def test_open_btn_has_tooltip(self, player):
        """開くボタンにツールチップが設定されている（FR-010）。"""
        assert player.open_btn.toolTip() != ""


class TestPlayBtnIcon:
    def test_play_btn_has_icon_initially(self, player):
        """初期状態（メディア未ロード）で play_btn にアイコンが設定されている（FR-001）。"""
        assert not player.play_btn.icon().isNull()

    def test_play_btn_shows_play_text_when_stopped(self, player):
        """停止状態ではアイコンあり + テキストが「再生」（FR-001）。"""
        player._update_play_btn_appearance(playing=False)
        assert not player.play_btn.icon().isNull()
        assert "再生" in player.play_btn.text() or "Play" in player.play_btn.text()

    def test_play_btn_shows_pause_text_when_playing(self, player):
        """再生中はアイコンあり + テキストが「一時停止」（FR-001）。"""
        player._update_play_btn_appearance(playing=True)
        assert not player.play_btn.icon().isNull()
        assert "一時停止" in player.play_btn.text() or "Pause" in player.play_btn.text()

    def test_play_btn_disabled_when_no_media(self, player, tmp_path):
        """メディア未ロード時は play_btn が disabled（FR-001）。"""
        # 新規インスタンスは play_btn が disabled で初期化される
        tmp_store = BookmarkStore(storage_path=tmp_path / "test_disabled_bm.json")
        fresh = VideoPlayer(store=tmp_store)
        try:
            assert not fresh.play_btn.isEnabled()
        finally:
            fresh.timer.stop()
            fresh._size_poll_timer.stop()
            fresh.media_player.stop()

    def test_play_btn_has_tooltip(self, player):
        """play_btn にツールチップが設定されている（FR-010）。"""
        assert player.play_btn.toolTip() != ""


class TestStopBtnIcon:
    def test_stop_btn_has_icon(self, player):
        """停止ボタンにアイコンが設定されている（FR-002）。"""
        assert not player.stop_btn.icon().isNull()

    def test_stop_btn_has_tooltip(self, player):
        """停止ボタンにツールチップが設定されている（FR-010）。"""
        assert player.stop_btn.toolTip() != ""
