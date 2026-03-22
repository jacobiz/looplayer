# Data Model: ボタンアイコン追加

**Branch**: `023-button-icons` | **Date**: 2026-03-22

このフィーチャーはデータベースやファイルストレージを変更しない。
変更対象は `VideoPlayer` ウィジェットの UI 状態のみ。

---

## ボタン状態モデル

### ButtonIconState（概念モデル）

各ボタンが持つアイコン関連の状態を定義する。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `icon` | `QIcon` | 表示アイコン（isNull() == False なら有効） |
| `tooltip` | `str` | hover 時のテキスト（空文字列なら未設定） |
| `is_checkable` | `bool` | ON/OFF 状態を持つトグルボタンか |
| `is_checked` | `bool` | トグルボタンの現在状態（is_checkable == True 時のみ有効） |
| `is_enabled` | `bool` | ボタンが操作可能か |

---

## 9ボタンの状態一覧

### P1: 主要再生ボタン

| ボタン | 属性名 | icon（初期） | is_checkable | is_enabled（初期） |
|--------|--------|-------------|-------------|-------------------|
| 開く | `open_btn` | SP_DirOpenIcon | False | True |
| 再生/一時停止 | `play_btn` | SP_MediaPlay | False | **False**（メディア未ロード時） |
| 停止 | `stop_btn` | SP_MediaStop | False | True |

### P2: ABループボタン

| ボタン | 属性名 | icon（初期） | is_checkable | is_enabled（初期） |
|--------|--------|-------------|-------------|-------------------|
| A点設定 | `set_a_btn` | SP_MediaSeekBackward | False | True |
| B点設定 | `set_b_btn` | SP_MediaSeekForward | False | True |
| ABループ切り替え | `ab_toggle_btn` | SP_BrowserReload | **True** | True |
| ABリセット | `ab_reset_btn` | SP_DialogResetButton | False | True |

### P3: その他ボタン

| ボタン | 属性名 | icon（初期） | is_checkable | is_enabled（初期） |
|--------|--------|-------------|-------------|-------------------|
| ブックマーク保存 | `save_bookmark_btn` | SP_FileDialogStart | False | False（AB未設定時） |
| ズームモード | `_zoom_btn` | SP_FileDialogContentsView | **True** | False（AB未設定時） |

---

## play_btn 状態遷移

```
[メディア未ロード]
  icon: SP_MediaPlay
  enabled: False
  text: "再生"
        |
        | _open_path() 呼び出し
        ↓
[再生中]
  icon: SP_MediaPause
  enabled: True
  text: "一時停止"
        |
        | toggle_play() または stop() 呼び出し
        ↓
[停止/一時停止中]
  icon: SP_MediaPlay
  enabled: True
  text: "再生"
```

## ab_toggle_btn / _zoom_btn 状態遷移

```
[OFF 状態]
  icon: SP_BrowserReload（または SP_FileDialogContentsView）
  is_checked: False  ← unchecked（通常表示）
        |
        | ボタンをクリック
        ↓
[ON 状態]
  icon: 同一アイコン
  is_checked: True   ← checked（強調/押し込み表示）
```

---

## 変更しないデータ

- `~/.looplayer/bookmarks.json` — 変更なし
- `~/.looplayer/settings.json` — 変更なし
- `~/.looplayer/positions.json` — 変更なし
- `~/.looplayer/recent_files.json` — 変更なし
- `looplayer/i18n.py` — 変更なし（新規キー追加なし）
