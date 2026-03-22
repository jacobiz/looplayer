"""Integration tests for video area right-click context menu (US1)."""
import pytest
from unittest.mock import patch

from PyQt6.QtWidgets import QMenu, QWidget
from PyQt6.QtCore import Qt, QPoint

from looplayer.i18n import t
from looplayer.player import VideoPlayer


class TestVideoContextOverlay:
    def test_overlay_exists_as_child_of_video_frame(self, player: VideoPlayer):
        """_video_ctx_overlay が video_frame の子ウィジェットとして存在すること。"""
        assert hasattr(player, "_video_ctx_overlay")
        overlay = player._video_ctx_overlay
        assert isinstance(overlay, QWidget)
        assert overlay.parent() is player.video_frame

    def test_overlay_has_correct_context_menu_policy(self, player: VideoPlayer):
        """overlay が CustomContextMenu ポリシーを持つこと。"""
        overlay = player._video_ctx_overlay
        assert overlay.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

    def test_show_video_context_menu_exists(self, player: VideoPlayer):
        """_show_video_context_menu メソッドが存在すること。"""
        assert hasattr(player, "_show_video_context_menu")
        assert callable(player._show_video_context_menu)


class TestVideoContextMenuActions:
    def _collect_menu_actions(self, player: VideoPlayer) -> dict:
        """_show_video_context_menu を呼び出してアクションを収集する。"""
        collected = {}

        def capture_exec(menu_self, *args, **kwargs):
            for action in menu_self.actions():
                if not action.isSeparator():
                    collected[action.text()] = action
            return None

        with patch.object(QMenu, "exec", capture_exec):
            player._show_video_context_menu(QPoint(10, 10))

        return collected

    def test_play_pause_action_exists(self, player: VideoPlayer):
        """メニューに「再生 / 一時停止」が存在すること。"""
        actions = self._collect_menu_actions(player)
        assert t("ctx.play_pause") in actions

    def test_play_pause_disabled_when_no_file(self, player: VideoPlayer):
        """ファイル未開時に再生系アクションが disabled であること。"""
        player._current_video_path = None
        actions = self._collect_menu_actions(player)
        if t("ctx.play_pause") in actions:
            assert not actions[t("ctx.play_pause")].isEnabled()

    def test_add_bookmark_disabled_when_ab_not_set(self, player: VideoPlayer):
        """A/B 未設定時は「ここにブックマークを追加」が disabled であること。"""
        player.ab_point_a = None
        player.ab_point_b = None
        player._current_video_path = None
        actions = self._collect_menu_actions(player)
        if t("ctx.add_bookmark") in actions:
            assert not actions[t("ctx.add_bookmark")].isEnabled()

    def test_add_bookmark_enabled_when_ab_both_set(self, player: VideoPlayer):
        """A/B 両方設定済み時に「ここにブックマークを追加」が enabled であること。"""
        player.ab_point_a = 1000
        player.ab_point_b = 2000
        player._current_video_path = "/some/video.mp4"
        actions = self._collect_menu_actions(player)
        assert t("ctx.add_bookmark") in actions
        assert actions[t("ctx.add_bookmark")].isEnabled()

    def test_fullscreen_action_always_present(self, player: VideoPlayer):
        """「フルスクリーン切り替え」は常に存在すること。"""
        actions = self._collect_menu_actions(player)
        assert t("ctx.fullscreen") in actions
