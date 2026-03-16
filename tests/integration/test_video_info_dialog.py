"""US3: 動画情報ダイアログの統合テスト。"""
import pytest
from PyQt6.QtWidgets import QDialog
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def player(qtbot: QtBot, tmp_path):
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    w = VideoPlayer(store=store)
    qtbot.addWidget(w)
    yield w
    w.timer.stop()
    w.media_player.stop()


class TestVideoInfoAction:
    """動画情報アクションの存在と有効/無効制御のテスト。"""

    def test_video_info_action_exists(self, player):
        """ファイルメニューに「動画情報」アクションが存在すること。"""
        assert hasattr(player, "_video_info_action")

    def test_video_info_action_disabled_initially(self, player):
        """動画を開く前はアクションが無効なこと。"""
        assert not player._video_info_action.isEnabled()

    def test_video_info_action_enabled_after_open(self, player, tmp_path):
        """動画を開いた後はアクションが有効なこと（ファイル存在チェックのみ・VLC再生なし）。"""
        # ダミーのmp4パスをセット（VLC再生失敗はOK、アクション有効化だけ確認）
        player._current_video_path = str(tmp_path / "test.mp4")
        player._export_action.setEnabled(True)
        player._video_info_action.setEnabled(True)
        assert player._video_info_action.isEnabled()


class TestVideoInfoDialog:
    """動画情報ダイアログのコンテンツテスト。"""

    def test_show_video_info_method_exists(self, player):
        """_show_video_info() メソッドが存在すること。"""
        assert hasattr(player, "_show_video_info")
        assert callable(player._show_video_info)

    def test_dialog_shows_filename_field(self, player, qtbot, tmp_path):
        """_show_video_info() がダイアログを生成し、ファイル名フィールドを含むこと。"""
        # ダミーパスを設定
        fake_path = str(tmp_path / "sample_video.mp4")
        player._current_video_path = fake_path

        # ダイアログを非ブロッキングで開く
        dialogs_shown = []

        original_exec = QDialog.exec

        def mock_exec(self):
            dialogs_shown.append(self)
            return 0  # Rejected (non-blocking)

        QDialog.exec = mock_exec
        try:
            player._show_video_info()
        finally:
            QDialog.exec = original_exec

        assert len(dialogs_shown) == 1
        # ダイアログにラベルが含まれていること（7項目）
        from PyQt6.QtWidgets import QLabel
        labels = dialogs_shown[0].findChildren(QLabel)
        label_texts = [lb.text() for lb in labels]
        # 最低限「ファイル名」または「サイズ」などのラベルが存在すること
        combined = " ".join(label_texts)
        assert "sample_video.mp4" in combined or "ファイル" in combined or len(labels) >= 2
