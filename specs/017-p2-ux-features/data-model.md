# Data Model: P2 UX 機能群

**Branch**: `017-p2-ux-features` | **Date**: 2026-03-18

---

## 1. AppSettings 拡張

**既存クラス**: `looplayer/app_settings.py` — `AppSettings`

### 新規プロパティ

| プロパティ | 型 | デフォルト | 永続化キー | 説明 |
|----------|-----|----------|-----------|------|
| `onboarding_shown` | `bool` | `False` | `"onboarding_shown"` | オンボーディング完了/スキップ済みフラグ |

### 既存プロパティ（設定ダイアログで利用）

| プロパティ | 型 | タブ | 説明 |
|----------|-----|-----|------|
| `end_of_playback_action` | `str` ("stop"/"rewind"/"loop") | 再生 | 再生終了時動作 |
| `sequential_play_mode` | `str` ("infinite"/"one_round") | 再生 | 連続再生モード |
| `export_encode_mode` | `str` ("copy"/"transcode") | 再生 | エクスポートエンコードモード |
| `check_update_on_startup` | `bool` | アップデート | 起動時更新確認 |

**表示タブ**: `always_on_top` は `VideoPlayer` の `Qt.WindowType.WindowStaysOnTopHint` フラグで管理。`AppSettings` への永続化は本フィーチャーのスコープ外（既存の `_toggle_always_on_top()` で管理済み）。

### バリデーション規則

- `onboarding_shown`: getter は `bool(self._data.get("onboarding_shown", False))` で未設定時 `False`
- 設定ファイル破損時は既存 `_load()` の例外ハンドリングで `{}` にフォールバック（既存動作と同じ）

---

## 2. FullscreenOverlayState（VideoPlayer 内インメモリ状態）

**場所**: `looplayer/player.py` — `VideoPlayer` クラスのインスタンス変数

| 変数名 | 型 | 初期値 | 説明 |
|-------|-----|-------|------|
| `_overlay_hide_timer` | `QTimer` | `QTimer(singleShot=True, interval=3000)` | 3秒後コントロール非表示タイマー |

**状態遷移**:

```
フルスクリーン突入
  └→ removeWidget(controls_panel)
     → controls_panel.setGeometry(0, h-overlay_h, w, overlay_h)
     → controls_panel.raise_()
     → controls_panel.hide()

mouseMoveEvent (下端10%検出)
  └→ controls_panel.show()
     → unsetCursor()
     → _overlay_hide_timer.start(3000)
     → _cursor_hide_timer.start(3000)

_overlay_hide_timer.timeout
  └→ controls_panel.hide()

controls_panel 上の mouseMoveEvent (EventFilter)
  └→ _overlay_hide_timer.start(3000)  ← リセット

フルスクリーン解除
  └→ centralWidget().layout().insertWidget(1, controls_panel)
     → controls_panel.show()
     → _overlay_hide_timer.stop()
```

---

## 3. PreferencesDialog

**場所**: `looplayer/widgets/preferences_dialog.py` — 新規ファイル

| フィールド | 型 | 説明 |
|---------|-----|------|
| `_settings` | `AppSettings` | 読み書き対象の設定オブジェクト |
| `_end_action_combo` | `QComboBox` | 再生終了時動作（stop/rewind/loop） |
| `_seq_mode_combo` | `QComboBox` | 連続再生モード（infinite/one_round） |
| `_encode_mode_combo` | `QComboBox` | エクスポートエンコードモード（copy/transcode） |
| `_check_update_checkbox` | `QCheckBox` | 起動時更新確認 |

**タブ構成**:

```
QTabWidget
├── 再生タブ (index 0)
│   ├── 再生終了時動作: QComboBox [停止 / 先頭に戻る / ループ]
│   ├── 連続再生モード: QComboBox [無限ループ / 1周停止]
│   └── エクスポートエンコードモード: QComboBox [高速 / 正確]
├── 表示タブ (index 1)
│   └── 常に最前面: QCheckBox  ← 読み取り専用表示（変更は既存メニューで）
└── アップデートタブ (index 2)
    └── 起動時に更新を確認する: QCheckBox
```

**OK/Cancel フロー**:
- `__init__`: `AppSettings` から値を読み込みウィジェットに反映
- OK: ウィジェット値を `AppSettings` へ書き込み → `accept()`
- Cancel: 何もせず → `reject()`

---

## 4. OnboardingOverlay

**場所**: `looplayer/widgets/onboarding_overlay.py` — 新規ファイル

| フィールド | 型 | 説明 |
|---------|-----|------|
| `_step` | `int` | 現在ステップ番号 (0–3) |
| `_settings` | `AppSettings` | 完了フラグ書き込み用 |
| `_title_label` | `QLabel` | ステップタイトル |
| `_body_label` | `QLabel` | ステップ説明文 |
| `_next_btn` | `QPushButton` | 「次へ」ボタン（最終ステップでは「完了」） |
| `_skip_btn` | `QPushButton` | 「スキップ」ボタン（クリック時に `onboarding_shown=True` を保存して閉じる） |
| `_progress_label` | `QLabel` | ステップ番号表示（例: 「1 / 4」） |

**ステップデータ（静的リスト）**:

| step | タイトル i18n キー | 本文 i18n キー |
|------|-----------------|--------------|
| 0 | `onboarding.step0.title` | `onboarding.step0.body` |
| 1 | `onboarding.step1.title` | `onboarding.step1.body` |
| 2 | `onboarding.step2.title` | `onboarding.step2.body` |
| 3 | `onboarding.step3.title` | `onboarding.step3.body` |

**状態遷移**:

```
__init__
  └→ _step = 0, _show_step(0)

「次へ」クリック（_step < 3）
  └→ _step += 1, _show_step(_step)

「次へ」クリック（_step == 3、「完了」時）
  └→ _settings.onboarding_shown = True → close()

「スキップ」クリック
  └→ _settings.onboarding_shown = True → close()  ← フラグを保存して閉じる（FR-304/305）

VideoPlayer を閉じる（ウィンドウ破棄）
  └→ onboarding_shown は保存しない → 次回起動時にステップ0から再表示
```

**サイズ・配置**:
- `VideoPlayer.resizeEvent` で `setGeometry(center_x - w/2, center_y - h/2, w, h)` で中央追従
- デフォルトサイズ: 480 × 280 px

---

## 5. BookmarkSlider ズーム状態

**既存クラス**: `looplayer/widgets/bookmark_slider.py` — `BookmarkSlider`

### 新規インスタンス変数

| 変数名 | 型 | 初期値 | 説明 |
|-------|-----|-------|------|
| `_zoom_enabled` | `bool` | `False` | ズームモード有効フラグ |
| `_zoom_start_ms` | `int` | `0` | ズーム表示範囲の開始時刻 (ms) |
| `_zoom_end_ms` | `int` | `0` | ズーム表示範囲の終了時刻 (ms) |

### ズーム範囲計算

```
padding = (b_ms - a_ms) * 0.1
_zoom_start_ms = max(0, a_ms - padding)
_zoom_end_ms   = min(duration_ms, b_ms + padding)
```

最小幅保証: `_zoom_end_ms - _zoom_start_ms` が `duration_ms * 0.01` 未満の場合は最低幅を適用。

### 座標変換の変更

| メソッド | 通常モード | ズームモード |
|--------|---------|-----------|
| `_ms_to_x(ms, groove)` | `ms / duration_ms` で線形マップ | `(ms - zoom_start) / (zoom_end - zoom_start)` で線形マップ |
| `_x_to_ms(x, groove)` | `ratio * duration_ms` | `zoom_start + ratio * (zoom_end - zoom_start)` |

---

## 6. i18n キー（新規追加）

**対象ファイル**: `looplayer/i18n.py`

### PreferencesDialog

| キー | 日本語 | 英語 |
|-----|--------|------|
| `menu.file.preferences` | 設定... | Preferences... |
| `dialog.prefs.title` | 設定 | Preferences |
| `dialog.prefs.tab.playback` | 再生 | Playback |
| `dialog.prefs.tab.view` | 表示 | View |
| `dialog.prefs.tab.updates` | アップデート | Updates |
| `dialog.prefs.end_action.label` | 再生終了時の動作 | End of playback |
| `dialog.prefs.end_action.stop` | 停止 | Stop |
| `dialog.prefs.end_action.rewind` | 先頭に戻る | Rewind |
| `dialog.prefs.end_action.loop` | ループ | Loop |
| `dialog.prefs.seq_mode.label` | 連続再生モード | Sequential play |
| `dialog.prefs.encode_mode.label` | エクスポートエンコードモード | Export encode mode |
| `dialog.prefs.always_on_top.label` | 常に最前面に表示（メニューで変更） | Always on top (change via menu) |
| `dialog.prefs.check_update.label` | 起動時に更新を確認する | Check for updates on startup |

### OnboardingOverlay

| キー | 日本語 | 英語 |
|-----|--------|------|
| `menu.help.tutorial` | チュートリアルを表示 | Show Tutorial |
| `onboarding.step0.title` | ようこそ！looplay! へ | Welcome to looplay! |
| `onboarding.step0.body` | AB ループ練習ツールへようこそ。まず動画ファイルを開きましょう。「ファイル > ファイルを開く」またはウィンドウにドラッグ＆ドロップで動画を読み込めます。 | Welcome to looplay! Start by opening a video file. Use "File > Open File" or drag and drop a video onto the window. |
| `onboarding.step1.title` | A/B 点を設定する | Set A/B Points |
| `onboarding.step1.body` | 動画を再生しながら「A点」ボタンでループ開始点、「B点」ボタンでループ終了点を設定します。シークバーで任意の位置に移動してから設定するとより正確です。 | While the video plays, press "Set A" to mark the loop start, and "Set B" for the loop end. Seek to the exact position first for precise results. |
| `onboarding.step2.title` | AB ループを再生する | Play the AB Loop |
| `onboarding.step2.body` | 「AB ループ: OFF」ボタンを押すとループ再生が開始されます。A 点と B 点の間を繰り返し再生します。 | Press the "AB Loop: OFF" button to start loop playback. The video will repeat between your A and B points. |
| `onboarding.step3.title` | ブックマークに保存する | Save as Bookmark |
| `onboarding.step3.body` | 「ブックマーク保存」でこの区間を名前を付けて保存できます。保存した区間は左パネルのリストに表示され、いつでも呼び出せます。 | Click "Save Bookmark" to save this loop section with a name. Saved bookmarks appear in the left panel and can be recalled anytime. |
| `onboarding.btn.next` | 次へ | Next |
| `onboarding.btn.finish` | 完了 | Finish |
| `onboarding.btn.skip` | スキップ | Skip |
| `onboarding.progress` | {step} / {total} | {step} / {total} |

### BookmarkSlider ズーム

| キー | 日本語 | 英語 |
|-----|--------|------|
| `btn.zoom_mode` | ズーム | Zoom |
| `tooltip.btn.zoom_mode` | AB区間をシークバー全幅に拡大表示 (Z) | Zoom to AB section (Z) |
