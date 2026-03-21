"""T009/T012: プレイヤー機能強化の統合テスト（US2・US3）。"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.i18n import t as _t
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store)
    qtbot.addWidget(widget)
    widget.show()
    yield widget
    widget.timer.stop()

    widget._size_poll_timer.stop()
    widget.media_player.stop()


def _get_play_menu(player: VideoPlayer):
    play_title = _t("menu.playback").replace("&", "")
    for action in player.menuBar().actions():
        if play_title in action.text().replace("&", ""):
            return action.menu()
    return None


def _get_file_menu(player: VideoPlayer):
    file_title = _t("menu.file").replace("&", "")
    for action in player.menuBar().actions():
        if file_title in action.text().replace("&", ""):
            return action.menu()
    return None


# ── T009: US2 音声・字幕トラックメニュー ─────────────────────────


class TestAudioTrackMenu:
    """US2: 音声トラックメニューの存在確認（T009）。"""

    def test_audio_track_menu_exists_in_play_menu(self, player):
        play_menu = _get_play_menu(player)
        assert play_menu is not None
        audio_text = _t("menu.playback.audio_track").replace("&", "")
        titles = [a.text().replace("&", "") for a in play_menu.actions()]
        assert any(audio_text in txt for txt in titles), f"音声トラックメニューが再生メニューにありません: {titles}"

    def test_audio_track_menu_is_submenu(self, player):
        play_menu = _get_play_menu(player)
        audio_text = _t("menu.playback.audio_track").replace("&", "")
        for action in play_menu.actions():
            if audio_text in action.text().replace("&", ""):
                assert action.menu() is not None, "音声トラックメニューがサブメニューではありません"
                return
        pytest.fail("音声トラックメニューが見つかりません")


class TestSubtitleMenu:
    """US2: 字幕メニューの存在確認（T009）。"""

    def test_subtitle_menu_exists_in_play_menu(self, player):
        play_menu = _get_play_menu(player)
        assert play_menu is not None
        sub_text = _t("menu.playback.subtitle").replace("&", "")
        titles = [a.text().replace("&", "") for a in play_menu.actions()]
        assert any(sub_text in txt for txt in titles), f"字幕メニューが再生メニューにありません: {titles}"

    def test_subtitle_menu_is_submenu(self, player):
        play_menu = _get_play_menu(player)
        sub_text = _t("menu.playback.subtitle").replace("&", "")
        for action in play_menu.actions():
            if sub_text in action.text().replace("&", ""):
                assert action.menu() is not None, "字幕メニューがサブメニューではありません"
                return
        pytest.fail("字幕メニューが見つかりません")


# ── T012: US3 スクリーンショットメニュー ─────────────────────────


class TestScreenshotMenu:
    """US3: スクリーンショットメニューの存在・動画未ロード時グレーアウト確認（T012）。"""

    def test_screenshot_action_exists_in_file_menu(self, player):
        file_menu = _get_file_menu(player)
        assert file_menu is not None
        ss_text = _t("menu.file.screenshot").replace("&", "")
        titles = [a.text().replace("&", "") for a in file_menu.actions()]
        assert any(ss_text in txt for txt in titles), (
            f"スクリーンショットアクションがファイルメニューにありません: {titles}"
        )

    def test_screenshot_action_disabled_when_no_video(self, player):
        """動画未ロード時はスクリーンショットアクションがグレーアウトされていること。"""
        file_menu = _get_file_menu(player)
        ss_text = _t("menu.file.screenshot").replace("&", "")
        for action in file_menu.actions():
            if ss_text in action.text().replace("&", ""):
                assert not action.isEnabled(), "動画未ロード時はグレーアウトされるべきです"
                return
        pytest.fail("スクリーンショットアクションが見つかりません")
