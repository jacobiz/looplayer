"""test_mirror_display: AppSettings.mirror_display と ミラー表示機能のテスト（F-203）。"""
import json
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
        widget = VideoPlayer(store=store)
        qtbot.addWidget(widget)
        yield widget
        widget.timer.stop()
        widget.media_player.stop()


class TestAppSettingsMirrorDisplayProperty:
    """T002: AppSettings.mirror_display プロパティの基本テスト。"""

    def test_mirror_display_default_is_false(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            assert s.mirror_display is False

    def test_mirror_display_setter_saves(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            s.mirror_display = True
            data = json.loads(settings_path.read_text())
            assert data["mirror_display"] is True

    def test_mirror_display_setter_type_error_on_non_bool(self, tmp_path):
        with patch("looplayer.app_settings._SETTINGS_PATH", tmp_path / "settings.json"):
            from looplayer.app_settings import AppSettings
            s = AppSettings()
            with pytest.raises(TypeError):
                s.mirror_display = "true"


class TestMirrorDisplayPersistence:
    """T012: ミラー表示の永続化・トグルのテスト。"""

    def test_mirror_display_persists_across_instances(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            from looplayer.app_settings import AppSettings
            s1 = AppSettings()
            s1.mirror_display = True
            s2 = AppSettings()
            assert s2.mirror_display is True

    def test_toggle_mirror_updates_setting(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            from looplayer.app_settings import AppSettings
            settings = AppSettings()
            settings.mirror_display = True
            assert settings.mirror_display is True
            settings.mirror_display = False
            assert settings.mirror_display is False

    def test_toggle_mirror_without_video_changes_setting_only(self, player):
        """動画未開封状態でトグルしても設定のみ変更し _open_path は呼ばれない。"""
        assert player._current_video_path is None
        player._app_settings.mirror_display = False

        open_path_calls = []
        original = player._open_path
        player._open_path = lambda p: open_path_calls.append(p)

        player._toggle_mirror_display()

        assert player._app_settings.mirror_display is True
        assert open_path_calls == []
        player._open_path = original


class TestMirrorOpenPathOption:
    """_open_path() でのミラーオプション適用テスト。"""

    def test_open_path_adds_hflip_option_when_mirror_on(self, player):
        """mirror_display=True 時、media.add_option が hflip オプションで呼ばれる。"""
        player._app_settings.mirror_display = True

        mock_media = MagicMock()
        player.instance.media_new = MagicMock(return_value=mock_media)
        player.media_player.set_media = MagicMock()
        player.media_player.play = MagicMock()
        player.media_player.get_length = MagicMock(return_value=0)

        # _open_path の後続処理（ブックマーク・最近のファイル等）でエラーにならないよう最小パッチ
        with (
            patch.object(player, "_rebuild_recent_menu"),
            patch.object(player, "_video_changed"),
            patch.object(player.bookmark_panel, "load_video"),
            patch.object(player, "_set_playback_rate"),
        ):
            player._open_path("/fake/video.mp4")

        add_option_calls = [str(c) for c in mock_media.add_option.call_args_list]
        assert any("video-filter=transform" in c for c in add_option_calls)
        assert any("transform-type=hflip" in c for c in add_option_calls)

    def test_open_path_no_hflip_option_when_mirror_off(self, player):
        """mirror_display=False 時、hflip オプションが付加されない。"""
        player._app_settings.mirror_display = False

        mock_media = MagicMock()
        player.instance.media_new = MagicMock(return_value=mock_media)
        player.media_player.set_media = MagicMock()
        player.media_player.play = MagicMock()
        player.media_player.get_length = MagicMock(return_value=0)

        with (
            patch.object(player, "_rebuild_recent_menu"),
            patch.object(player, "_video_changed"),
            patch.object(player.bookmark_panel, "load_video"),
            patch.object(player, "_set_playback_rate"),
        ):
            player._open_path("/fake/video.mp4")

        add_option_calls = [str(c) for c in mock_media.add_option.call_args_list]
        assert not any("hflip" in c for c in add_option_calls)
