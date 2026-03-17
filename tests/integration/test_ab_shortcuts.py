"""T007: I/O ショートカットによる A/B 点セットの統合テスト。"""
from unittest.mock import patch
from PyQt6.QtGui import QKeySequence, QShortcut
from looplayer.player import VideoPlayer
from looplayer.i18n import t as tr


def _find_shortcut(player: VideoPlayer, key: str) -> QShortcut | None:
    """指定キーの QShortcut を探す。"""
    for s in player.findChildren(QShortcut):
        if s.key().toString() == key:
            return s
    return None


def test_i_shortcut_registered(player: VideoPlayer):
    """I キーショートカットが player に登録されている。"""
    assert _find_shortcut(player, "I") is not None


def test_o_shortcut_registered(player: VideoPlayer):
    """O キーショートカットが player に登録されている。"""
    assert _find_shortcut(player, "O") is not None


def test_i_shortcut_sets_point_a(player: VideoPlayer):
    """I キーショートカットの activated シグナルが set_point_a() を呼ぶ。"""
    shortcut = _find_shortcut(player, "I")
    assert shortcut is not None
    with patch.object(player.media_player, 'get_time', return_value=7000):
        shortcut.activated.emit()
    assert player.ab_point_a == 7000


def test_o_shortcut_sets_point_b(player: VideoPlayer):
    """O キーショートカットの activated シグナルが set_point_b() を呼ぶ。"""
    shortcut = _find_shortcut(player, "O")
    assert shortcut is not None
    with patch.object(player.media_player, 'get_time', return_value=12000):
        shortcut.activated.emit()
    assert player.ab_point_b == 12000


def test_shortcut_dialog_contains_i_o_labels():
    """i18n に shortcut.set_a / shortcut.set_b キーが登録されている。"""
    assert tr("shortcut.set_a") != "shortcut.set_a"
    assert tr("shortcut.set_b") != "shortcut.set_b"
    assert "I" in tr("shortcut.set_a")
    assert "O" in tr("shortcut.set_b")
