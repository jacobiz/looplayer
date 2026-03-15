# Data Model: プレイヤーメニュー基本機能

**Date**: 2026-03-15

本フィーチャーはディスクへの永続化を持たない。状態はすべて `VideoPlayer` インスタンスのメモリ内で管理される。

## 状態フィールド（VideoPlayer クラスへの追加）

### 音量状態

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `_volume` | `int` | `80` | 現在の音量（0〜100%）。VLC に直接反映。 |
| `_is_muted` | `bool` | `False` | ミュート中かどうか |
| `_pre_mute_volume` | `int` | `80` | ミュート前の音量。ミュート解除時に復元。 |

**バリデーション**:
- `_volume` は 0〜100 の範囲でクランプする
- `set_volume(v)` を介してのみ変更し、スライダーと VLC を同期させる

**状態遷移（ミュート）**:
```
通常 → ミュート: _pre_mute_volume = _volume; _volume = 0; _is_muted = True
ミュート → 通常: _volume = _pre_mute_volume; _is_muted = False
```

---

### 再生速度状態

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `_playback_rate` | `float` | `1.0` | 現在の再生速度 |

**有効値**: `0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 2.0`

**リセット条件**: `open_file()` 呼び出し時に `1.0` にリセット（FR-012）

---

### フルスクリーン状態

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `isFullScreen()` | `bool` (Qt 組み込み) | フルスクリーン中かどうか（フィールド追加不要） |
| `_menu_hide_timer` | `QTimer` | フルスクリーン中のメニューバー自動非表示タイマー（2秒） |

---

### 常に最前面状態

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `_always_on_top` | `bool` | `False` | 常に最前面フラグ。`QAction.isChecked()` と同期。 |

---

## UI ウィジェット（新規追加）

| ウィジェット | 型 | 説明 |
|------------|-----|------|
| `controls_panel` | `QWidget` | コントロール群コンテナ。フルスクリーン時に hide/show。 |
| `volume_slider` | `QSlider` | 音量スライダー（0〜100、水平） |
| `volume_label` | `QLabel` | 音量表示ラベル（例: "80%"） |
| `speed_action_group` | `QActionGroup` | 再生速度の排他選択グループ |
| `fullscreen_action` | `QAction` | フルスクリーントグルアクション |
| `always_on_top_action` | `QAction` | 常に最前面トグルアクション（checkable） |
| `_menu_hide_timer` | `QTimer` | フルスクリーン中メニューバー自動非表示タイマー |

---

## 状態間の依存関係

```
open_file()
  ├── _playback_rate → 1.0（リセット）
  └── 音量は維持（_volume 変化なし）

toggle_fullscreen()
  ├── isFullScreen() → True  : controls_panel.hide(), menuBar().hide()
  └── isFullScreen() → False : controls_panel.show(), menuBar().show()

toggle_mute()
  ├── _is_muted=False → True  : _pre_mute_volume=_volume; _volume=0
  └── _is_muted=True  → False : _volume=_pre_mute_volume; _is_muted=False
```
