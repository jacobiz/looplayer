"""シークバークリック × ABループのユニットテスト。

Constitution I 準拠: 実装前に作成し、失敗を確認してから実装に進む。
"""
from unittest.mock import patch, call
from looplayer.player import VideoPlayer


# ── Phase 3 (US1) ──────────────────────────────────────────────────────────


def test_click_past_b_does_not_jump_to_a(player: VideoPlayer):
    """B点以降をクリック後にタイマーを呼んでも set_time(ab_point_a) が呼ばれないこと。

    FR-001: B点以降クリック直後に即 A点ジャンプが起きないことを確認する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # B点以降の位置（70000ms）を _on_seek_ms() でセット
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player._on_seek_ms(70000)

    # _prev_timer_ms = 70000 の状態でタイマー呼び出し（current_ms=70200ms）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=70200 / 120000):
                player._on_timer()

    # A点へのジャンプは発生しないこと（70000 > 60000 → クロス不成立）
    mock_set_time.assert_not_called()


def test_natural_b_crossing_triggers_loop(player: VideoPlayer):
    """prev < B ≤ current の状態で _on_timer() を呼ぶと set_time(ab_point_a) が呼ばれること。

    FR-003: 自然なB点到達でループトリガーが発生することを確認する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # 直前の位置を B点前に設定（59800ms）
    player._prev_timer_ms = 59800

    # current_ms = 60000（B点ちょうど）でタイマー呼び出し
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=60000 / 120000):
                player._on_timer()

    # A点（30000ms）へのジャンプが発生すること
    mock_set_time.assert_called_once_with(30000)


def test_prev_timer_ms_reset_on_seek(player: VideoPlayer):
    """_on_seek_ms(ms) 呼び出し後に _prev_timer_ms == ms になること。

    シーク後は新しい位置を基点としてクロッシング検出を行うための確認。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # 初期値は None
    assert player._prev_timer_ms is None

    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player._on_seek_ms(45000)

    assert player._prev_timer_ms == 45000


# ── Phase 4 (US2) ──────────────────────────────────────────────────────────


def test_seek_before_b_then_loop_triggers(player: VideoPlayer):
    """_on_seek_ms(10000) 後に prev=59800 → curr=60000 でループトリガーが発生すること。

    US2: ループ範囲外クリック後、B点自然到達でループが継続されることを確認する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # A点前（10秒）にシーク
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player._on_seek_ms(10000)

    # _prev_timer_ms を直接 59800 に設定（シーク後から時間が経過した状態をシミュレート）
    player._prev_timer_ms = 59800

    # current_ms = 60000（B点到達）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=60000 / 120000):
                player._on_timer()

    # A点（30000ms）へのジャンプが発生すること
    mock_set_time.assert_called_once_with(30000)


# ── Phase 5 (Polish) ────────────────────────────────────────────────────────


def test_loop_toggle_off_preserves_position(player: VideoPlayer):
    """ループ有効中にシーク後、toggle_ab_loop(False) を呼んでも set_time() がループ関連で呼ばれないこと。

    FR-006: ループトグルOFF後は現在位置から継続再生（位置ジャンプなし）。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # B点以降にシーク
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player._on_seek_ms(70000)

    # ループをOFF
    player.toggle_ab_loop(False)

    # タイマー呼び出しでループが発生しないこと
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=70200 / 120000):
                player._on_timer()

    mock_set_time.assert_not_called()


def test_seek_relative_past_b_does_not_jump_to_a(player: VideoPlayer):
    """キーボードシーク（+N秒）でB点以降に移動した後、タイマーで A点ジャンプが発生しないこと。

    _seek_relative() 経由のシークも _prev_timer_ms を更新することを確認する（Issue 1 回帰防止）。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # キーボードで B点以降（55000 + 10000 = 65000ms）にシーク
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_time', return_value=55000):
                player._seek_relative(10000)

    # _prev_timer_ms = 65000 になっていること
    assert player._prev_timer_ms == 65000

    # タイマー: prev=65000 >= B=60000 → クロッシング不成立 → A点ジャンプなし
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=65200 / 120000):
                player._on_timer()

    mock_set_time.assert_not_called()


def test_a_only_no_loop_behavior(player: VideoPlayer):
    """A点のみ設定（B点=None）でシークしてもループ動作（A点ジャンプ）が発生しないこと。

    FR-005: B点未設定の場合はループ無効扱いで既存動作を維持する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = None  # B点未設定
    player.ab_loop_active = True

    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player._on_seek_ms(50000)

    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=50200 / 120000):
                player._on_timer()

    mock_set_time.assert_not_called()
