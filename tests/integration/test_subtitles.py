"""016-p1-features: F-201 外部字幕ファイルの読み込み 統合テスト。

実 VLC インスタンスを使用（モック不可）。
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()

    widget._size_poll_timer.stop()
    widget.media_player.stop()


@pytest.fixture
def srt_file(tmp_path: Path) -> Path:
    """最小構成の SRT 字幕ファイル。"""
    srt = tmp_path / "test.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:05,000\nテスト字幕\n\n",
        encoding="utf-8",
    )
    return srt


@pytest.fixture
def ass_file(tmp_path: Path) -> Path:
    """最小構成の ASS 字幕ファイル。"""
    ass = tmp_path / "test.ass"
    ass.write_text(
        "[Script Info]\nTitle: Test\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginV, Effect, Text\n",
        encoding="utf-8",
    )
    return ass


class TestSubtitleNoVideo:
    """FR-103: 動画未選択時の字幕読み込み拒否。"""

    def test_open_subtitle_without_video_shows_error(self, player, srt_file):
        """動画未選択時に _open_subtitle_file() を呼ぶとエラーメッセージが表示される。"""
        assert player._current_video_path is None  # 動画未選択状態

        with patch("looplayer.player.QFileDialog.getOpenFileName",
                   return_value=(str(srt_file), "")):
            with patch("looplayer.player.QMessageBox.warning") as mock_warning:
                player._open_subtitle_file()
                mock_warning.assert_called_once()


class TestSubtitleLoad:
    """FR-102: 動画再生中の字幕読み込み。"""

    def test_load_srt_sets_external_subtitle_path(self, player, srt_file, tmp_path):
        """有効な SRT ファイルを選択すると _external_subtitle_path が設定される。"""
        # 動画が読み込まれているシミュレーション（_current_path を設定）
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"")
        player._current_video_path = str(fake_video)

        with patch("looplayer.player.QFileDialog.getOpenFileName",
                   return_value=(str(srt_file), "")):
            with patch.object(player.media_player, "add_slave", return_value=True):
                player._open_subtitle_file()

        assert player._external_subtitle_path == srt_file

    def test_load_ass_sets_external_subtitle_path(self, player, ass_file, tmp_path):
        """有効な ASS ファイルを選択すると _external_subtitle_path が設定される。"""
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"")
        player._current_video_path = str(fake_video)

        with patch("looplayer.player.QFileDialog.getOpenFileName",
                   return_value=(str(ass_file), "")):
            with patch.object(player.media_player, "add_slave", return_value=True):
                player._open_subtitle_file()

        assert player._external_subtitle_path == ass_file


class TestSubtitleBadFormat:
    """FR-104: 非対応拡張子の拒否。"""

    def test_unsupported_extension_shows_error(self, player, tmp_path):
        """非対応拡張子（.txt）を選択するとフォーマットエラーが表示される。"""
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"")
        player._current_video_path = str(fake_video)

        txt_file = tmp_path / "subtitle.txt"
        txt_file.write_text("not a subtitle", encoding="utf-8")

        with patch("looplayer.player.QFileDialog.getOpenFileName",
                   return_value=(str(txt_file), "")):
            with patch("looplayer.player.QMessageBox.warning") as mock_warning:
                player._open_subtitle_file()
                mock_warning.assert_called_once()

        assert player._external_subtitle_path is None


class TestSubtitleReset:
    """FR-106: 動画切り替え時の字幕リセット。"""

    def test_open_new_video_resets_subtitle_path(self, player, srt_file, tmp_path):
        """別の動画を開くと _external_subtitle_path が None にリセットされる。"""
        # 字幕パスを手動設定
        player._external_subtitle_path = srt_file

        fake_video = tmp_path / "new_video.mp4"
        fake_video.write_bytes(b"")

        mock_media = object()
        with patch.object(player.instance, "media_new", return_value=mock_media):
            with patch.object(player.media_player, "set_media"):
                with patch.object(player.media_player, "play"):
                    with patch.object(player, "_load_bookmarks_for_current_video",
                                      create=True, side_effect=None):
                        player._open_path(str(fake_video))

        assert player._external_subtitle_path is None


class TestSubtitleSwitchTrack:
    """FR-105: 外部字幕読み込み後の内蔵字幕トラック切り替え。"""

    def test_subtitle_menu_exists_after_video_load(self, player):
        """字幕メニュー内に「字幕ファイルを開く」アクションが存在する。"""
        from looplayer.i18n import t as _t
        # メニューを展開して _rebuild_subtitle_menu を呼ぶ
        player._subtitle_menu.setEnabled(True)
        player._rebuild_subtitle_menu()
        open_subtitle_text = _t("menu.playback.subtitle.open_file")
        action_texts = [a.text() for a in player._subtitle_menu.actions()]
        assert any(open_subtitle_text in txt for txt in action_texts), \
            f"字幕ファイルを開くアクションが見つかりません: {action_texts}"
