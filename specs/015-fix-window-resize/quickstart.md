# Quickstart: 015-fix-window-resize

## 検証シナリオ

### シナリオ 1: アスペクト比が正しいことを確認（US1 / FR-001）

```python
# 単体テストでの検証例
# video_frame の高さが正しい UI オフセットで計算されているか

player = VideoPlayer(...)
player.show()
# video_frame とウィンドウの高さ差分が UI オフセット
ui_offset = player.height() - player.video_frame.height()

# 1280×720 の動画に対してリサイズ
player._resize_to_video(1280, 720)

# 動画フレームの高さが 720 になっていること
assert player.video_frame.height() == 720
# ウィンドウの高さは 720 + ui_offset であること
assert player.height() == 720 + ui_offset
```

### シナリオ 2: ポーリングが 5 秒でタイムアウトすること（US2 / FR-002）

```python
# VLC が動画サイズを返さない状態を模擬
with patch.object(player.media_player, 'video_get_size', return_value=(0, 0)):
    player._start_size_poll()
    # 100 回ポーリング（5秒相当）後にタイマーが停止していること
    for _ in range(101):
        player._poll_video_size()
    assert not player._size_poll_timer.isActive()
```

### シナリオ 3: デッドコードが存在しないこと（US3 / FR-004, FR-005）

```python
# _user_resized 属性が存在しないこと
assert not hasattr(player, '_user_resized')

# _on_vlc_video_changed メソッドが存在しないこと
assert not hasattr(player, '_on_vlc_video_changed')
```

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `looplayer/player.py` | `_resize_to_video` の高さ計算修正、ポーリングタイムアウト追加、デッドコード削除 |
| `tests/unit/test_window_resize.py` | 新規テストファイル |
