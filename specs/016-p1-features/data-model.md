# Data Model: P1優先度機能の実装

**Branch**: `016-p1-features` | **Date**: 2026-03-18

---

## F-201 外部字幕ファイル

### エンティティ: ExternalSubtitle（VideoPlayer の内部状態）

新規クラスは作らない。`VideoPlayer` に以下のインスタンス変数を追加する。

| 変数名 | 型 | 初期値 | 説明 |
|--------|-----|--------|------|
| `_external_subtitle_path` | `Path \| None` | `None` | 現在読み込まれている外部字幕ファイルのパス |

### ライフサイクル

```
None
  ↓ [メニューから SRT/ASS ファイルを選択]
Path オブジェクト（ファイルパス）
  ↓ [別の動画ファイルを開く]
None（リセット）
  ↓ [アプリ終了]
None（保存しない。セッション限りの一時設定）
```

### バリデーション規則

- 拡張子が `.srt` または `.ass` であること（大文字小文字不問）
- ファイルが存在すること
- 動画が開かれていること（`_current_video_path is not None`）

### 永続化

外部字幕パスは**永続化しない**。アプリ起動ごとに手動で再読み込みする設計。

---

## F-403 ウィンドウジオメトリ

### エンティティ: WindowGeometry（AppSettings の新規プロパティ）

`settings.json` に追加される新しいフィールド。

```json
{
  "window_geometry": {
    "x": 100,
    "y": 200,
    "width": 1280,
    "height": 720
  }
}
```

| フィールド | 型 | 制約 | 説明 |
|-----------|-----|------|------|
| `x` | `int` | 任意の整数 | ウィンドウ左上の X 座標（スクリーン座標系） |
| `y` | `int` | 任意の整数 | ウィンドウ左上の Y 座標（スクリーン座標系） |
| `width` | `int` | >= 800 | ウィンドウ幅（ピクセル） |
| `height` | `int` | >= 600 | ウィンドウ高さ（ピクセル） |

**デフォルト値**: `None`（キーが存在しない場合）→ OSデフォルト位置で起動

### VideoPlayer の内部状態

| 変数名 | 型 | 初期値 | 説明 |
|--------|-----|--------|------|
| `_pre_fullscreen_geometry` | `QRect \| None` | `None` | フルスクリーン突入直前のジオメトリ |

### ライフサイクル

```
起動時:
  settings.window_geometry が None → OS デフォルト位置
  settings.window_geometry が存在 → QApplication.screenAt() で有効性確認
                                    → 有効: 指定位置に復元
                                    → 無効: プライマリスクリーン中央に補正

フルスクリーン突入時:
  _pre_fullscreen_geometry = self.geometry()

フルスクリーン解除時:
  _pre_fullscreen_geometry = None（showNormal() が自動復元するため）

終了時:
  isFullScreen() == True → _pre_fullscreen_geometry を保存
  isFullScreen() == False → self.geometry() を保存

「ウィンドウ位置をリセット」選択時:
  settings.window_geometry = None（キー削除）
  次回起動時に OS デフォルト位置で起動
```

### バリデーション規則（復元時）

- `QApplication.screenAt(QPoint(x, y))` が `None` を返す → スクリーン外 → プライマリスクリーン中央に補正
- `width < 800` または `height < 600` → 最小値 `800 x 600` に補正

---

## F-502 ツールチップ文字列

### エンティティ: TooltipString（i18n.py への追加キー）

新規エンティティなし。既存の `_STRINGS` 辞書に追記する。

| i18n キー | 日本語 | 英語 |
|-----------|--------|------|
| `tooltip.btn.play` | `"再生/一時停止 (Space)"` | `"Play/Pause (Space)"` |
| `tooltip.seekbar` | `"クリックまたはドラッグで再生位置を変更"` | `"Click or drag to seek"` |
| `tooltip.volume` | `"音量を調整 (↑/↓)"` | `"Adjust volume (↑/↓)"` |
| `tooltip.btn.frame_minus` | `"1フレーム戻す (,)"` | `"Go back 1 frame (,)"` |
| `tooltip.btn.frame_plus` | `"1フレーム進める (.)"` | `"Go forward 1 frame (.)"` |
| `tooltip.btn.set_a` | `"A点を設定 (I)"` | `"Set point A (I)"` |
| `tooltip.btn.set_b` | `"B点を設定 (O)"` | `"Set point B (O)"` |
| `tooltip.btn.ab_loop` | `"ABループを切り替える"` | `"Toggle AB loop"` |
| `tooltip.btn.edit_tags` | `"タグを編集"` | `"Edit tags"` |
| `tooltip.btn.reset_play_count` | `"再生回数をリセット"` | `"Reset play count"` |
| `tooltip.pause_interval` | `"ループ間の一時停止時間（秒）"` | `"Pause duration between loops (seconds)"` |
| `tooltip.btn.frame_a_minus` | `"A点を1フレーム前にずらす (Shift+,)"` | `"Move A point back 1 frame (Shift+,)"` |
| `tooltip.btn.frame_a_plus` | `"A点を1フレーム後にずらす (Shift+.)"` | `"Move A point forward 1 frame (Shift+.)"` |
| `tooltip.btn.frame_b_minus` | `"B点を1フレーム前にずらす (Ctrl+,)"` | `"Move B point back 1 frame (Ctrl+,)"` |
| `tooltip.btn.frame_b_plus` | `"B点を1フレーム後にずらす (Ctrl+.)"` | `"Move B point forward 1 frame (Ctrl+.)"` |

### 新規 i18n キー（F-201 メッセージ）

| i18n キー | 日本語 | 英語 |
|-----------|--------|------|
| `menu.playback.subtitle.open_file` | `"字幕ファイルを開く..."` | `"Open Subtitle File..."` |
| `msg.subtitle_no_video.title` | `"動画が開かれていません"` | `"No Video Open"` |
| `msg.subtitle_no_video.body` | `"字幕ファイルを読み込むには動画を開いてください。"` | `"Please open a video to load a subtitle file."` |
| `msg.subtitle_bad_format.title` | `"非対応のファイル形式"` | `"Unsupported File Format"` |
| `msg.subtitle_bad_format.body` | `"SRT または ASS 形式の字幕ファイルを選択してください。"` | `"Please select a subtitle file in SRT or ASS format."` |
| `msg.subtitle_load_error.title` | `"字幕読み込みエラー"` | `"Subtitle Load Error"` |
| `msg.subtitle_load_error.body` | `"字幕ファイルの読み込みに失敗しました。UTF-8 形式のファイルを使用してください。"` | `"Failed to load subtitle file. Please use a UTF-8 encoded file."` |

### 新規 i18n キー（F-403 メニュー）

| i18n キー | 日本語 | 英語 |
|-----------|--------|------|
| `menu.view.reset_window` | `"ウィンドウ位置をリセット"` | `"Reset Window Position"` |
