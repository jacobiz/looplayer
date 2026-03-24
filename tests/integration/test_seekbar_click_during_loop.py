"""シークバークリック × ABループの統合テスト。

Constitution I 準拠: 実装前に作成し、失敗を確認してから実装に進む。
"""
from unittest.mock import patch, MagicMock, call
from looplayer.player import VideoPlayer


# ── Phase 3 (US1) ──────────────────────────────────────────────────────────


def test_click_within_loop_starts_from_click_position(player: VideoPlayer, qtbot):
    """ABループ有効中にループ内の位置をクリックすると、その位置から再生が継続される。

    FR-001: seek_slider.seek_requested シグナル → _on_seek_ms → media_player.set_time(ms)
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # seek_slider が seek_requested(45000) を emit → _on_seek_ms(45000) が呼ばれる
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player.seek_slider.seek_requested.emit(45000)

    # media_player.set_time(45000) が呼ばれること
    mock_set_time.assert_called_once_with(45000)


def test_pause_state_preserved_on_click(player: VideoPlayer, qtbot):
    """一時停止中にシークバーをクリックしたとき、play() が呼ばれず一時停止状態が維持される。

    FR-004: 一時停止中クリック → 再生ヘッド移動のみ（自動再生開始しない）。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # 一時停止状態をシミュレート（is_playing = False）
    with patch.object(player.media_player, 'is_playing', return_value=False):
        with patch.object(player.media_player, 'play') as mock_play:
            with patch.object(player.media_player, 'set_time'):
                with patch.object(player.media_player, 'get_length', return_value=120000):
                    player.seek_slider.seek_requested.emit(45000)

    # play() は呼ばれないこと
    mock_play.assert_not_called()


def test_zoom_mode_click_seeks_correctly(player: VideoPlayer, qtbot):
    """ズームモード有効中にシークバーをクリックすると、ズーム範囲内の正しい ms でシークされる。

    FR-001: ズームモードでも通常モードと同様にクリック位置から再生開始する。
    seek_requested はズーム計算済みの ms を emit するため、
    _on_seek_ms(ms) → media_player.set_time(ms) が正しく呼ばれることを確認する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # ズームモードを有効にする（20秒〜80秒の範囲を全幅表示）
    player.seek_slider.set_zoom(20000, 80000)
    player.seek_slider._duration_ms = 120000

    # ズーム範囲内の 45000ms を seek_requested で emit（BookmarkSlider が計算済みの値を送出）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player.seek_slider.seek_requested.emit(45000)

    # media_player.set_time(45000) が呼ばれること
    mock_set_time.assert_called_once_with(45000)

    # クリーンアップ
    player.seek_slider.clear_zoom()


# ── Phase 4 (US2) ──────────────────────────────────────────────────────────


def test_click_outside_loop_then_loop_resumes(player: VideoPlayer, qtbot):
    """ループ範囲外（A点前・10秒）をクリック後、B点自然到達でA点ループトリガーが発生すること。

    US2: ループ範囲外クリック → クリック位置確認 → B点到達でA点へ戻る一連の動作を検証。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # ① A点前（10秒）をクリック
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player.seek_slider.seek_requested.emit(10000)

    # クリック位置（10000ms）に set_time が呼ばれること
    mock_set_time.assert_called_once_with(10000)

    # ② _prev_timer_ms を 59800ms に手動設定（10秒から59.8秒まで再生経過をシミュレート）
    player._prev_timer_ms = 59800

    # ③ B点（60000ms）到達時のタイマー呼び出し
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=60000 / 120000):
                player._on_timer()

    # A点（30000ms）へのジャンプが発生すること
    mock_set_time.assert_called_once_with(30000)


# ── Phase 5 (Polish) ────────────────────────────────────────────────────────


def test_video_end_after_seek_past_b_follows_app_settings(player: VideoPlayer, qtbot):
    """B点以降にシーク後、動画末尾到達時はABループではなくapp_settingsの終了動作が適用される。

    Edge Case: B点以降クリック後に動画末尾到達 → ABループより末尾処理が上位。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # B点以降（70000ms）にシーク
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=80000):
            player._on_seek_ms(70000)

    # _prev_timer_ms = 70000 の状態でタイマー呼び出し（current_ms=75000 < B点超えだが動画末尾近く）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=80000):
            with patch.object(player.media_player, 'get_position',
                              return_value=75000 / 80000):
                player._on_timer()

    # ABループによるA点ジャンプは発生しないこと（prev=70000 >= 60000 → クロス不成立）
    mock_set_time.assert_not_called()


def test_drag_seek_not_affected_by_loop_change(player: VideoPlayer, qtbot):
    """連続ドラッグでB点を超えた後、タイマー実行でA点ジャンプが発生しないこと（回帰確認）。

    連続ドラッグシーク中は _on_seek_ms が複数回呼ばれ _prev_timer_ms が都度更新される。
    最終停止位置（B点以降）では prev >= B となりクロッシング不成立 → A点ジャンプなし。
    crossing detection の実装後もドラッグシーク動作が変化しないことを確認する。
    """
    player.ab_point_a = 30000
    player.ab_point_b = 60000
    player.ab_loop_active = True

    # ドラッグ中フラグ
    player.seek_slider._dragging = True

    # 連続ドラッグシーク: 50000ms → 65000ms → 70000ms（B点を通過）
    with patch.object(player.media_player, 'set_time'):
        with patch.object(player.media_player, 'get_length', return_value=120000):
            player.seek_slider.seek_requested.emit(50000)  # _prev_timer_ms = 50000
            player.seek_slider.seek_requested.emit(65000)  # _prev_timer_ms = 65000
            player.seek_slider.seek_requested.emit(70000)  # _prev_timer_ms = 70000

    # ドラッグ解除
    player.seek_slider._dragging = False

    # タイマー実行: current_ms=70000（prev=70000 >= B=60000 → クロッシング不成立）
    with patch.object(player.media_player, 'set_time') as mock_set_time:
        with patch.object(player.media_player, 'get_length', return_value=120000):
            with patch.object(player.media_player, 'get_position',
                              return_value=70000 / 120000):
                player._on_timer()

    # B点以降で _prev_timer_ms >= B のためA点ジャンプは発生しないこと
    mock_set_time.assert_not_called()
