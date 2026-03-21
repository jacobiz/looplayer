"""US4: キーボードショートカット一覧ダイアログの統合テスト。"""
import pytest
from PyQt6.QtCore import Qt
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

    w._size_poll_timer.stop()
    w.media_player.stop()


class TestShortcutDialogExists:
    """ショートカット一覧ダイアログの存在テスト。"""

    def test_show_shortcut_dialog_method_exists(self, player):
        """_show_shortcut_dialog() メソッドが存在すること。"""
        assert hasattr(player, "_show_shortcut_dialog")
        assert callable(player._show_shortcut_dialog)

    def test_help_menu_exists(self, player):
        """ヘルプメニューがメニューバーに存在すること。"""
        menu_bar = player.menuBar()
        menu_titles = [action.text() for action in menu_bar.actions()]
        has_help = any("ヘルプ" in t or "Help" in t or "H" in t for t in menu_titles)
        assert has_help, f"ヘルプメニューが見つかりません: {menu_titles}"


class TestShortcutDialogContent:
    """ショートカット一覧ダイアログのコンテンツテスト。"""

    def test_dialog_has_categories(self, player, qtbot):
        """ダイアログに5カテゴリ以上のショートカットが含まれること。"""
        dialogs_shown = []
        original_exec = QDialog.exec

        def mock_exec(self):
            dialogs_shown.append(self)
            return 0

        QDialog.exec = mock_exec
        try:
            player._show_shortcut_dialog()
        finally:
            QDialog.exec = original_exec

        assert len(dialogs_shown) == 1
        # ダイアログにラベルが含まれていること
        from PyQt6.QtWidgets import QLabel
        labels = dialogs_shown[0].findChildren(QLabel)
        # 十分なエントリが表示されていること（5カテゴリ以上）
        assert len(labels) >= 5

    def test_dialog_contains_space_key(self, player, qtbot):
        """スペースキー（再生/一時停止）がダイアログに含まれること。"""
        dialogs_shown = []
        original_exec = QDialog.exec

        def mock_exec(self):
            dialogs_shown.append(self)
            return 0

        QDialog.exec = mock_exec
        try:
            player._show_shortcut_dialog()
        finally:
            QDialog.exec = original_exec

        from PyQt6.QtWidgets import QLabel
        labels = dialogs_shown[0].findChildren(QLabel)
        all_text = " ".join(lb.text() for lb in labels)
        assert "Space" in all_text or "スペース" in all_text or "再生" in all_text

    def test_question_mark_shortcut_registered(self, player):
        """? キーがショートカットとして登録されていること。"""
        # QAction またはQShortcut として ? が登録されていること
        from PyQt6.QtGui import QShortcut
        shortcuts = player.findChildren(QShortcut)
        actions = player.actions()
        keys = [s.key().toString() for s in shortcuts]
        action_keys = [a.shortcut().toString() for a in actions]
        all_keys = keys + action_keys
        assert any("?" in k or "Shift+/" in k for k in all_keys), (
            f"? キーショートカットが見つかりません: {all_keys}"
        )
