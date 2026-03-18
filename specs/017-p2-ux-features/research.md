# Research: P2 UX 機能群

**Branch**: `017-p2-ux-features` | **Date**: 2026-03-18

---

## F-503: フルスクリーン中コントロールオーバーレイ

### Decision: controls_panel をフローティングオーバーレイとして再利用する

**Rationale**: 既存の `controls_panel` QWidget（QVBoxLayout 内の最後のアイテム）を、フルスクリーン突入時にレイアウトから取り外し、`setGeometry()` で絶対配置する。フルスクリーン解除時に `insertWidget(1, controls_panel)` で元に戻す。新規ウィジェットを作らないため重複コードがゼロ。

**Approach**:
1. フルスクリーン突入時: `centralWidget().layout().removeWidget(controls_panel)` → `setGeometry(0, h - overlay_h, w, overlay_h)` → `raise_()` → `hide()`
2. `mouseMoveEvent` でウィンドウ下端 10% に入ったら `controls_panel.show()` + タイマーリセット
3. 3 秒タイマーで `controls_panel.hide()`
4. `controls_panel` 上でのマウス移動でタイマーリセット（`controls_panel.setMouseTracking(True)` + `installEventFilter`）
5. フルスクリーン解除時: `centralWidget().layout().insertWidget(1, controls_panel)` → `controls_panel.show()`

**Alternatives considered**:
- 新規 `FullscreenOverlay` ウィジェット作成 → 全コントロールの複製が必要でシークバー同期が複雑。YAGNI 違反
- `controls_panel.hide/show` だけで対応（マウストリガーなし）→ キーボード不要要件を満たさない

**Qt API**: `QLayout.removeWidget()`, `QLayout.insertWidget()`, `QWidget.setGeometry()`, `QWidget.raise_()`

**Cursor hide coordination**: 既存 `_cursor_hide_timer` (3s) と新設 `_overlay_hide_timer` (3s) は独立したタイマー。マウス移動時に両方リセット。`controls_panel` 表示中はカーソルを `unsetCursor()` で常時表示（`_hide_cursor()` は `controls_panel` 非表示時のみ動作させる）

---

## F-401: 設定画面（Preferences）

### Decision: PreferencesDialog を新規 QDialog ウィジェットとして実装

**Rationale**: 既存の `AppSettings` クラスをそのまま利用できる。`QTabWidget` で「再生 / 表示 / アップデート」の 3 タブ構成。OK 押下まで変更をバッファし、Cancel で破棄。

**Approach**:
1. `looplayer/widgets/preferences_dialog.py` に `PreferencesDialog(QDialog)` を作成
2. `__init__` で `AppSettings` から現在値を読み込み、各ウィジェットに反映
3. OK ボタンで各値を `AppSettings` に書き込み → `accept()`
4. Cancel ボタンで何もせず → `reject()`
5. `player.py` の `_build_menus()` で「ファイル > 設定」QAction を追加

**Tab 構成**:
- **再生タブ**: 再生終了時動作（QComboBox or QRadioButton 3択）、連続再生モード（QComboBox）、エクスポートエンコードモード（QComboBox）
- **表示タブ**: 常に最前面（QCheckBox）
- **アップデートタブ**: 起動時更新確認（QCheckBox）

**Alternatives considered**:
- `QFormLayout` 全項目 1 画面 → タブなしが最もシンプルだが、将来の設定項目追加でスクロールが必要になる。タブは現時点でも 6 項目あるため妥当
- 変更即時保存（Apply 不要）→ Cancel 動作が不要になるが、誤操作リスクあり。OK/Cancel 2 ボタン構成に決定済み（clarify A）

---

## F-501: 初回起動オンボーディング

### Decision: OnboardingOverlay を非モーダル QWidget オーバーレイとして実装

**Rationale**: `QDialog`（モーダル）ではなく `QWidget` を直接使い、`VideoPlayer` 中央に半透明オーバーレイとして重ねる。`VideoPlayer.resizeEvent` で位置・サイズを追従させる。

**Approach**:
1. `looplayer/widgets/onboarding_overlay.py` に `OnboardingOverlay(QWidget)` を作成
2. `VideoPlayer.__init__` 末尾で `AppSettings.onboarding_shown` を確認。`False` なら生成・表示
3. 4 ステップを内部リストで保持。「次へ」で `_step` カウンタをインクリメント
4. 最終ステップの「完了」と「スキップ」ボタンで `AppSettings.onboarding_shown = True` → `close()`
5. 途中で VideoPlayer を閉じた場合は `onboarding_shown` を保存しない → 次回起動時にステップ 1 から再表示（clarify A）
6. 「ヘルプ > チュートリアルを表示」QAction で `onboarding_shown = False` → 再表示

**AppSettings 拡張**: `onboarding_shown: bool` プロパティを追加

**Alternatives considered**:
- `QWizard` → ステップナビゲーション機能があるが UIが固定的でオーバーレイ表示に不向き
- `QDialog`（モーダル）→ FR-306（非モーダル）に違反

---

## F-105: ABループ区間のズーム表示

### Decision: BookmarkSlider にズーム座標変換を追加

**Rationale**: `BookmarkSlider` は既に `_ms_to_x()` と `_x_to_ms()` の座標変換メソッドを持つ。ズームモード時にこれらの変換式を `view_start_ms`/`view_end_ms` を使った線形補間に差し替えるだけで実装できる。

**Approach**:
1. `BookmarkSlider` に `_zoom_enabled: bool`, `_zoom_start_ms: int`, `_zoom_end_ms: int` フィールドを追加
2. `set_zoom(start_ms: int, end_ms: int)` と `clear_zoom()` メソッドを追加
3. `_ms_to_x()` と `_x_to_ms()` に `if self._zoom_enabled:` 分岐を追加（ズームモードでは `_zoom_start_ms`〜`_zoom_end_ms` を全幅にマップ）
4. `player.py` に `_zoom_btn` トグルボタンと `_toggle_zoom_mode()` メソッドを追加
5. AB 点変更時に `_zoom_btn` が ON なら zoom range を自動更新
6. 動画切り替え時にズームモードをリセット

**Zoom range calculation**: A点/B点の ±10% パディングを加えた範囲を `view_start_ms`/`view_end_ms` とする
- `padding = (b_ms - a_ms) * 0.1`
- `view_start = max(0, a_ms - padding)`
- `view_end = min(duration_ms, b_ms + padding)`

**Alternatives considered**:
- 新規 `ZoomableSlider` サブクラス → `BookmarkSlider` の描画ロジック（bookmark bars, AB handles）をすべて継承する必要があり、過度な抽象化
- Player 側でズーム座標変換 → Slider の描画と操作が分離し、整合性維持が困難
