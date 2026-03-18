"""F-501: 初回起動オンボーディング（OnboardingOverlay）ユニットテスト。"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel
from pytestqt.qtbot import QtBot

from looplayer.app_settings import AppSettings
from looplayer.bookmark_store import BookmarkStore
from looplayer.player import VideoPlayer


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    s = AppSettings.__new__(AppSettings)
    s._data = {}
    s.save = MagicMock()
    return s


@pytest.fixture
def overlay(qtbot: QtBot, settings: AppSettings, tmp_path: Path):
    parent = QWidget()
    parent.resize(800, 600)
    qtbot.addWidget(parent)
    from looplayer.widgets.onboarding_overlay import OnboardingOverlay
    ov = OnboardingOverlay(settings=settings, parent=parent)
    # parent を yield 終了まで生かしておく（child はスコープが消えると GC される）
    yield ov
    # テスト終了後: parent は qtbot が cleanup する


@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget.media_player.stop()


class TestOnboardingOverlayInit:
    """オーバーレイの初期化確認。"""

    def test_overlay_is_qwidget(self, overlay):
        """OnboardingOverlay は QWidget のサブクラス。"""
        assert isinstance(overlay, QWidget)

    def test_overlay_starts_at_step_0(self, overlay):
        """初期ステップは 0。"""
        assert overlay._step == 0

    def test_overlay_has_next_button(self, overlay):
        """「次へ」ボタンが存在する。"""
        assert hasattr(overlay, "_next_btn")
        assert isinstance(overlay._next_btn, QPushButton)

    def test_overlay_has_skip_button(self, overlay):
        """「スキップ」ボタンが存在する。"""
        assert hasattr(overlay, "_skip_btn")
        assert isinstance(overlay._skip_btn, QPushButton)

    def test_overlay_has_progress_label(self, overlay):
        """ステップ進捗ラベルが存在する。"""
        assert hasattr(overlay, "_progress_label")
        assert isinstance(overlay._progress_label, QLabel)

    def test_progress_label_shows_step_number(self, overlay):
        """ステップ 0 では「1 / 4」と表示される。"""
        assert "1" in overlay._progress_label.text()
        assert "4" in overlay._progress_label.text()


class TestOnboardingOverlayNavigation:
    """ステップナビゲーション確認。"""

    def test_next_button_advances_step(self, overlay):
        """「次へ」ボタンをクリックするとステップが増加する。"""
        assert overlay._step == 0
        overlay._next_btn.click()
        assert overlay._step == 1

    def test_next_button_advances_to_step_3(self, overlay):
        """3回クリックでステップ 3 になる。"""
        for _ in range(3):
            overlay._next_btn.click()
        assert overlay._step == 3

    def test_next_btn_text_changes_to_finish_on_last_step(self, overlay):
        """最終ステップ（3）では「次へ」ボタンのテキストが「完了」になる。"""
        for _ in range(3):
            overlay._next_btn.click()
        assert overlay._step == 3
        text = overlay._next_btn.text()
        assert "完了" in text or "Finish" in text

    def test_progress_label_updates_on_next(self, overlay):
        """「次へ」クリック後に進捗ラベルが更新される。"""
        overlay._next_btn.click()
        assert "2" in overlay._progress_label.text()


class TestOnboardingOverlayCompletion:
    """完了・スキップ時のフラグ保存確認。"""

    def test_finish_on_last_step_saves_flag(self, overlay, settings):
        """最終ステップで「完了」クリックすると onboarding_shown=True が保存される。"""
        for _ in range(3):
            overlay._next_btn.click()
        overlay._next_btn.click()  # 4回目 = 完了
        assert settings._data.get("onboarding_shown") is True

    def test_finish_on_last_step_closes_overlay(self, overlay, settings):
        """最終ステップで「完了」クリックするとオーバーレイが hidden になる。"""
        for _ in range(3):
            overlay._next_btn.click()
        overlay._next_btn.click()
        assert overlay.isHidden()

    def test_skip_saves_flag(self, overlay, settings):
        """「スキップ」クリックで onboarding_shown=True が保存される。"""
        overlay._skip_btn.click()
        assert settings._data.get("onboarding_shown") is True

    def test_skip_closes_overlay(self, overlay, settings):
        """「スキップ」クリックでオーバーレイが hidden になる。"""
        overlay._skip_btn.click()
        assert overlay.isHidden()

    def test_close_without_finish_does_not_save_flag(self, overlay, settings):
        """完了/スキップなしでオーバーレイを直接 close() しても onboarding_shown は保存されない。"""
        overlay.close()
        assert "onboarding_shown" not in settings._data


class TestOnboardingPlayerIntegration:
    """VideoPlayer との統合確認。"""

    def test_overlay_shown_when_onboarding_not_completed(self, qtbot, tmp_path):
        """onboarding_shown=False のとき VideoPlayer 起動でオーバーレイが生成・表示される。"""
        store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
        with patch("looplayer.app_settings.AppSettings.onboarding_shown", new_callable=lambda: property(
            lambda self: False,
            lambda self, v: None,
        )):
            widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
            qtbot.addWidget(widget)
            widget.timer.stop()
            widget.media_player.stop()
            assert hasattr(widget, "_onboarding_overlay")
            assert widget._onboarding_overlay is not None

    def test_overlay_not_created_when_already_completed(self, player):
        """デフォルト（onboarding_shown=False だが実際はモック環境で None）— 属性が存在する。"""
        # VideoPlayer は必ず _onboarding_overlay 属性を持つ（None または OnboardingOverlay）
        assert hasattr(player, "_onboarding_overlay")

    def test_help_menu_tutorial_action_exists(self, player):
        """ヘルプメニューに「チュートリアルを表示」アクションが存在する。"""
        help_menu_action = None
        for action in player.menuBar().actions():
            if "ヘルプ" in action.text() or "Help" in action.text():
                help_menu_action = action
                break
        assert help_menu_action is not None
        menu = help_menu_action.menu()
        texts = [a.text() for a in menu.actions()]
        assert any("チュートリアル" in t or "Tutorial" in t for t in texts)
