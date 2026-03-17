"""US6: ブックマーク エクスポート＆インポート 統合テスト。"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t as _t
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


@pytest.fixture
def player_with_video(player, tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()
    with patch.object(player.media_player, "play"):
        with patch.object(player.media_player, "set_media"):
            player._open_path(str(video))
    bm1 = LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="マーク1", repeat_count=2, order=0)
    bm2 = LoopBookmark(point_a_ms=6000, point_b_ms=10000, name="マーク2", repeat_count=1, order=1)
    player._store.add(str(video), bm1)
    player._store.add(str(video), bm2)
    player.bookmark_panel._refresh_list()
    return player, video, bm1, bm2


class TestExportMenuAction:
    """ファイルメニューにエクスポートアクションが存在する。"""

    def test_export_action_exists(self, player):
        file_menu = _get_file_menu(player)
        texts = [a.text() for a in file_menu.actions()]
        export_text = _t("menu.file.export")
        assert any(export_text in txt for txt in texts)

    def test_export_action_disabled_without_video(self, player):
        """動画未選択時はエクスポートメニューが無効。"""
        file_menu = _get_file_menu(player)
        export_action = next((a for a in file_menu.actions() if _t("menu.file.export") in a.text()), None)
        assert export_action is not None
        assert not export_action.isEnabled()

    def test_export_action_enabled_with_video(self, player_with_video):
        player, video, bm1, bm2 = player_with_video
        file_menu = _get_file_menu(player)
        export_action = next((a for a in file_menu.actions() if _t("menu.file.export") in a.text()), None)
        assert export_action is not None
        assert export_action.isEnabled()


class TestImportMenuAction:
    """ファイルメニューにインポートアクションが存在する。"""

    def test_import_action_exists(self, player):
        file_menu = _get_file_menu(player)
        texts = [a.text() for a in file_menu.actions()]
        import_text = _t("menu.file.import")
        assert any(import_text in txt for txt in texts)


class TestExportBookmarks:
    """エクスポート: ファイルダイアログ→ファイル保存。"""

    def test_export_saves_file(self, player_with_video, tmp_path):
        player, video, bm1, bm2 = player_with_video
        export_path = str(tmp_path / "out.json")
        with patch("looplayer.player.QFileDialog.getSaveFileName", return_value=(export_path, "")):
            player._export_bookmarks()
        assert Path(export_path).exists()

    def test_export_cancelled_does_nothing(self, player_with_video, tmp_path):
        player, video, bm1, bm2 = player_with_video
        with patch("looplayer.player.QFileDialog.getSaveFileName", return_value=("", "")):
            player._export_bookmarks()  # エラーにならないこと


class TestImportBookmarks:
    """インポート: ファイルダイアログ→重複スキップ。"""

    def test_import_adds_bookmarks(self, player_with_video, tmp_path):
        player, video, bm1, bm2 = player_with_video
        export_path = str(tmp_path / "export.json")
        with patch("looplayer.player.QFileDialog.getSaveFileName", return_value=(export_path, "")):
            player._export_bookmarks()
        # 既存ブックマーク削除
        player._store.delete(str(video), bm1.id)
        player._store.delete(str(video), bm2.id)
        assert len(player._store.get_bookmarks(str(video))) == 0
        # インポート
        with patch("looplayer.player.QFileDialog.getOpenFileName", return_value=(export_path, "")):
            player._import_bookmarks()
        assert len(player._store.get_bookmarks(str(video))) == 2

    def test_import_skips_duplicates(self, player_with_video, tmp_path):
        player, video, bm1, bm2 = player_with_video
        export_path = str(tmp_path / "export.json")
        with patch("looplayer.player.QFileDialog.getSaveFileName", return_value=(export_path, "")):
            player._export_bookmarks()
        # 同じデータを再インポート（重複スキップ）
        count_before = len(player._store.get_bookmarks(str(video)))
        with patch("looplayer.player.QFileDialog.getOpenFileName", return_value=(export_path, "")):
            player._import_bookmarks()
        count_after = len(player._store.get_bookmarks(str(video)))
        assert count_after == count_before

    def test_import_invalid_json_shows_error(self, player_with_video, tmp_path):
        player, video, bm1, bm2 = player_with_video
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid}")
        with patch("looplayer.player.QFileDialog.getOpenFileName", return_value=(str(bad_file), "")):
            with patch("looplayer.player.QMessageBox") as mock_msg:
                player._import_bookmarks()
                mock_msg.warning.assert_called()


def _get_file_menu(player):
    file_title = _t("menu.file").replace("&", "")
    for action in player.menuBar().actions():
        if file_title in action.text().replace("&", ""):
            return action.menu()
    return None
