"""再生制御の統合テスト（ボタン操作・UI状態確認）。"""
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot
from looplayer.player import VideoPlayer


def test_initial_state(player: VideoPlayer):
    """初期状態: 再生ボタンラベルが「再生」、スライダーが先頭、時刻が00:00。"""
    assert player.play_btn.text() == "再生"
    assert player.seek_slider.value() == 0
    assert player.time_label.text() == "00:00 / 00:00"


def test_initial_ab_info(player: VideoPlayer):
    """初期状態: ABラベルが「A: --  B: --」。"""
    assert player.ab_info_label.text() == "A: --  B: --"


def test_initial_ab_loop_button(player: VideoPlayer):
    """初期状態: ABループボタンが「ABループ: OFF」でオフ。"""
    assert player.ab_toggle_btn.text() == "ABループ: OFF"
    assert not player.ab_toggle_btn.isChecked()


def test_stop_resets_slider(player: VideoPlayer, qtbot: QtBot):
    """停止ボタンを押すとスライダーが0に戻り時刻表示がリセットされる。"""
    qtbot.mouseClick(player.stop_btn, Qt.MouseButton.LeftButton)
    assert player.seek_slider.value() == 0
    assert player.time_label.text() == "00:00 / 00:00"
    assert player.play_btn.text() == "再生"
