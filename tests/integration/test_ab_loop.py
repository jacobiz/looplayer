"""ABループ操作フローの統合テスト。"""
from unittest.mock import patch
from main import VideoPlayer


def test_set_point_a_calls_method_and_updates_ui(player: VideoPlayer):
    """set_point_a() で ab_point_a が記録され UI ラベルが更新される。"""
    with patch.object(player.media_player, 'get_time', return_value=15000):
        player.set_point_a()
    assert player.ab_point_a == 15000
    assert player.ab_info_label.text() == "A: 00:15  B: --"


def test_set_point_b_calls_method_and_updates_ui(player: VideoPlayer):
    """set_point_b() で ab_point_b が記録され UI ラベルが更新される。"""
    with patch.object(player.media_player, 'get_time', return_value=30000):
        player.set_point_b()
    assert player.ab_point_b == 30000
    assert player.ab_info_label.text() == "A: --  B: 00:30"


def test_both_points_ui_display(player: VideoPlayer):
    """A/B 両点セット時に UI ラベルが両方表示される。"""
    with patch.object(player.media_player, 'get_time', return_value=15000):
        player.set_point_a()
    with patch.object(player.media_player, 'get_time', return_value=30000):
        player.set_point_b()
    assert player.ab_info_label.text() == "A: 00:15  B: 00:30"


def test_toggle_ab_loop_on(player: VideoPlayer):
    """toggle_ab_loop(True) でボタンラベルが「ABループ: ON」になりフラグがセットされる。"""
    player.toggle_ab_loop(True)
    assert player.ab_toggle_btn.text() == "ABループ: ON"
    assert player.ab_loop_active is True
    assert player.ab_toggle_btn.isChecked()


def test_toggle_ab_loop_off(player: VideoPlayer):
    """toggle_ab_loop(False) でボタンラベルが「ABループ: OFF」になりフラグが解除される。"""
    player.toggle_ab_loop(True)
    player.toggle_ab_loop(False)
    assert player.ab_toggle_btn.text() == "ABループ: OFF"
    assert player.ab_loop_active is False
    assert not player.ab_toggle_btn.isChecked()


def test_reset_ab_clears_all_state(player: VideoPlayer):
    """reset_ab() で A/B 点・ループ状態が全てクリアされ UI が初期値に戻る。"""
    with patch.object(player.media_player, 'get_time', return_value=5000):
        player.set_point_a()
    with patch.object(player.media_player, 'get_time', return_value=10000):
        player.set_point_b()
    player.toggle_ab_loop(True)

    player.reset_ab()

    assert player.ab_point_a is None
    assert player.ab_point_b is None
    assert player.ab_loop_active is False
    assert player.ab_toggle_btn.text() == "ABループ: OFF"
    assert not player.ab_toggle_btn.isChecked()
    assert player.ab_info_label.text() == "A: --  B: --"


def test_new_file_resets_ab_state(player: VideoPlayer):
    """FR-014: 新しいファイルを開いたとき AB点とループ状態が自動リセットされる。"""
    with patch.object(player.media_player, 'get_time', return_value=5000):
        player.set_point_a()
    with patch.object(player.media_player, 'get_time', return_value=10000):
        player.set_point_b()
    player.toggle_ab_loop(True)

    # ファイルダイアログ・VLC操作をモックして open_file() を実行
    with patch("main.QFileDialog.getOpenFileName", return_value=("/fake/video.mp4", "")):
        with patch.object(player.instance, 'media_new', return_value=object()):
            with patch.object(player.media_player, 'set_media'):
                with patch.object(player.media_player, 'set_xwindow'):
                    with patch.object(player.media_player, 'play'):
                        player.open_file()

    assert player.ab_point_a is None
    assert player.ab_point_b is None
    assert player.ab_loop_active is False
