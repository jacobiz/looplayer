"""ABループ判定ロジックのユニットテスト。"""
from unittest.mock import patch
from main import VideoPlayer


def test_loop_does_not_trigger_without_b(player: VideoPlayer):
    """A点のみセット・ab_loop_active=True の状態で _on_timer を呼んでもループしない。"""
    player.ab_point_a = 5000
    player.ab_point_b = None
    player.ab_loop_active = True
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=30000):
            with patch.object(player.media_player, 'get_position', return_value=0.5):
                player._on_timer()
    mock_set_time.assert_not_called()


def test_loop_does_not_trigger_without_a(player: VideoPlayer):
    """B点のみセット・ab_loop_active=True の状態で _on_timer を呼んでもループしない。"""
    player.ab_point_a = None
    player.ab_point_b = 10000
    player.ab_loop_active = True
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=30000):
            with patch.object(player.media_player, 'get_position', return_value=0.5):
                player._on_timer()
    mock_set_time.assert_not_called()


def test_loop_triggers_when_reaching_b(player: VideoPlayer):
    """A/B 両方セット・active=True・current >= B のとき set_time(A) が呼ばれる。"""
    player.ab_point_a = 5000
    player.ab_point_b = 10000
    player.ab_loop_active = True
    # position=10000/30000=0.3333... → current_ms=10000（B点ちょうど）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=30000):
            with patch.object(player.media_player, 'get_position', return_value=10000 / 30000):
                player._on_timer()
    mock_set_time.assert_called_once_with(5000)


def test_loop_does_not_trigger_before_b(player: VideoPlayer):
    """B点未到達では set_time が呼ばれない。"""
    player.ab_point_a = 5000
    player.ab_point_b = 10000
    player.ab_loop_active = True
    # current_ms = 9999
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=30000):
            with patch.object(player.media_player, 'get_position', return_value=9999 / 30000):
                player._on_timer()
    mock_set_time.assert_not_called()


def test_ab_loop_flag_unchanged_after_reset(player: VideoPlayer):
    """reset_ab() 後に ab_loop_active が False になること。"""
    player.ab_point_a = 5000
    player.ab_point_b = 10000
    player.ab_loop_active = True
    player.reset_ab()
    assert player.ab_loop_active is False
    assert player.ab_point_a is None
    assert player.ab_point_b is None


def test_ab_loop_flag_unchanged_on_video_end(player: VideoPlayer):
    """stop() を呼んでも ab_loop_active が変化しないこと（状態維持）。"""
    player.ab_loop_active = True
    player.media_player.stop()
    assert player.ab_loop_active is True
