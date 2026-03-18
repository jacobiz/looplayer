# Implementation Plan: プレイヤー UI バグ修正・操作性改善

**Branch**: `013-player-ui-fixes` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-player-ui-fixes/spec.md`

## Summary

4件のバグ修正・UX改善を実施する。①フルスクリーン中の ESC キー無効バグ（メニューバー非表示時に QAction ショートカットが失効する問題）、②設定中 AB 点のシークバーリアルタイム表示、③シークバー上 AB 点マーカーのドラッグ操作、④ブックマーク行の「ポーズ」「繰返」スピンボックス幅の拡張。主な変更対象は `BookmarkSlider`・`player.py`・`bookmark_row.py` の 3 ファイル。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203
**Storage**: `~/.looplayer/bookmarks.json`（既存、変更なし）
**Testing**: pytest + pytest-qt（pytestqt）
**Target Platform**: デスクトップ（Linux/Windows/macOS）
**Project Type**: デスクトップアプリ（PyQt6 GUI）
**Performance Goals**: AB 点セット後のシークバー更新が体感遅延なし（< 16ms / 1フレーム相当）
**Constraints**: ウィンドウ最小幅（既存）に収まる範囲でスピンボックス幅を拡張する
**Scale/Scope**: 単一ウィンドウ、変更対象ファイル 3 本

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 判定 | 根拠 |
|------|------|------|
| I. テストファースト | ✅ PASS | 各ユーザーストーリーで先にテストを書いてから実装する |
| II. シンプルさ重視 | ✅ PASS | 既存ファイルへの最小変更。新規ファイルは必要最小限 |
| III. 過度な抽象化の禁止 | ✅ PASS | ヘルパークラスなし。QShortcut 追加・メソッド拡張のみ |
| IV. 日本語コミュニケーション | ✅ PASS | コード内コメント・コミットメッセージは日本語 |

**Complexity Tracking**: 違反なし。記録不要。

## Project Structure

### Documentation (this feature)

```text
specs/013-player-ui-fixes/
├── plan.md              # このファイル
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
└── tasks.md             # /speckit.tasks コマンド出力
```

### Source Code (repository root)

```text
looplayer/
├── player.py                          # ESC ショートカット修正、AB 点更新呼び出し追加
├── widgets/
│   ├── bookmark_slider.py             # AB 点プレビュー表示 + ドラッグ操作追加
│   └── bookmark_row.py                # スピンボックス幅拡張

tests/
├── unit/
│   ├── test_bookmark_slider.py        # AB プレビュー表示テスト追加
│   └── test_bookmark_row_layout.py    # スピンボックス幅テスト（新規）
└── integration/
    ├── test_fullscreen.py             # ESC QShortcut 経由テスト追加
    └── test_ab_seekbar.py             # AB 点シークバー統合テスト（新規）
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規ファイルはテストのみ 2 本追加。

---

## Phase 0: Research

*research.md に詳細を記載。以下は重要決定事項のサマリー。*

### R-001: ESC キーバグの根本原因と修正方針

**原因**: `esc_action` は `view_menu`（メニューバー配下の QMenu）に追加された QAction。フルスクリーン時に `self.menuBar().hide()` でメニューバーが非表示になると、PyQt6 では `ApplicationShortcut` コンテキストであっても**非表示の親ウィジェットを持つ QAction のショートカットは機能しなくなる**。

**修正方針**: メニューの QAction とは独立に、`QShortcut(QKeySequence("Escape"), self)` を MainWindow に直接追加する。`ApplicationShortcut` コンテキストを設定し、フォーカス状態・メニューバー表示状態に依存しない確実な ESC ハンドリングを実現する。既存の `esc_action` は互換性のため残す（メニュー項目として表示される）。

**代替案**: `keyPressEvent` オーバーライド → ショートカットとして管理できず複雑になるため却下。

### R-002: AB 点プレビュー表示（BookmarkSlider 拡張）

**方針**: `BookmarkSlider` に `set_ab_preview(a_ms: int | None, b_ms: int | None)` メソッドを追加。`paintEvent` 内で既存のブックマークバー描画後に AB 点プレビューを重ね描きする。

**描画スタイル**:
- A 点のみ: 白色の縦線（幅 2px、GrooveRect の高さに合わせる）+ 上端に小三角マーカー（▼）でドラッグ可能を示唆
- A・B 両方: 白色半透明バー（アルファ 150）+ 両端に縦線
- 保存済みブックマークバーと区別するため白系（`QColor(255, 255, 255, 150)`）を使用

**代替案**: 別 Widget を重ねる → 座標合わせが複雑なため却下。

### R-003: AB 点マーカードラッグ（BookmarkSlider 拡張）

**方針**: `mousePressEvent` でのヒット判定に「AB 点マーカー付近（±6px）」を追加し、AB ドラッグモードを開始する。優先順位: AB マーカー > ブックマークバー > トラックシーク。

**新規シグナル**: `ab_point_drag_finished = pyqtSignal(str, int)` — "a" または "b" と確定 ms 値を emit。マウスリリース時のみ emit（ドラッグ中は内部状態のみ更新）。これにより Player 側で `ab_point_a`/`ab_point_b` を更新し、UI に反映する。

**制約の実装**: ドラッグ中に A > B または B < A になる場合、B-1ms（または A+1ms）にクランプ。

**代替案**: ドラッグ中もリアルタイム emit → spec で「ドラッグ終了時のみ更新」と決定済みのため却下。

### R-004: スピンボックス幅の修正

**現状**: `repeat_spin.setFixedWidth(55)`、`pause_spin.setFixedWidth(64)`
**問題**: "99" (repeat) や "10.0" (pause) が表示しきれない幅になっている。
**修正**:
- `repeat_spin`: `setFixedWidth(55)` → `setMinimumWidth(68)` に変更（fixedWidth 廃止でフレキシブルに）
- `pause_spin`: `setFixedWidth(64)` → `setMinimumWidth(75)` に変更
- `setFixedWidth` を廃止して `setMinimumWidth` に変更することで、ウィンドウ幅が広いときに自然に伸縮する

---

## Phase 1: Design & Contracts

### Data Model Changes

*data-model.md に詳細を記載。主要な変更:*

#### BookmarkSlider の状態拡張

```
BookmarkSlider（既存属性に追加）
├── _ab_preview_a: int | None    # 設定中 A 点 (ms)、None = 未設定
├── _ab_preview_b: int | None    # 設定中 B 点 (ms)、None = 未設定
└── _ab_drag_target: str | None  # ドラッグ中のターゲット "a" / "b" / None
```

#### BookmarkSlider の新規 API

```
メソッド:
  set_ab_preview(a_ms: int | None, b_ms: int | None) -> None
    AB 点プレビューを更新して再描画する

シグナル:
  ab_point_drag_finished = pyqtSignal(str, int)
    ドラッグ完了時に emit。str: "a"/"b"、int: 確定 ms 値
```

#### Player.py の変更点

```
既存メソッド変更:
  set_point_a()   → 末尾で seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b) 呼び出し
  set_point_b()   → 末尾で seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b) 呼び出し
  clear_ab_loop() → 末尾で seek_slider.set_ab_preview(None, None) 呼び出し

新規接続:
  seek_slider.ab_point_drag_finished.connect(self._on_ab_drag_finished)

新規メソッド:
  _on_ab_drag_finished(target: str, ms: int) -> None
    target="a" → ab_point_a = ms; target="b" → ab_point_b = ms
    seek_slider.set_ab_preview(ab_point_a, ab_point_b) 呼び出し

新規ショートカット（__init__ または _setup_shortcuts 内）:
  QShortcut(QKeySequence("Escape"), self) → _exit_fullscreen に接続
```

### Contracts

このプロジェクトはデスクトップアプリ（内部コンポーネント間通信のみ）のため、外部 API コントラクトは不要。PyQt6 シグナルを内部インターフェースとして使用する。

---

## Implementation Order (by User Story)

テストファーストに従い、各ストーリーで「テスト → 実装 → パス確認 → コミット」のサイクルを回す。

### US1: ESC キー修正（P1）

1. `test_fullscreen.py` に `QShortcut` 経由での ESC テストを追加（`QTest.keyClick` でなく `QShortcut.activated` をシミュレート）
2. `player.py` に `QShortcut(QKeySequence("Escape"), self)` を追加し `_exit_fullscreen` に接続
3. テストパス確認

### US2: AB 点プレビュー表示（P2）

1. `test_bookmark_slider.py` に `set_ab_preview` の単体テストを追加
2. `BookmarkSlider.set_ab_preview()` と `paintEvent` 拡張を実装
3. `test_ab_seekbar.py` に Player 統合テストを追加
4. `player.py` の `set_point_a/b`・`clear_ab_loop` に呼び出し追加
5. テストパス確認

### US3: AB 点ドラッグ（P2）

1. `test_bookmark_slider.py` に AB ドラッグテスト追加（マウスイベントシミュレーション）
2. `BookmarkSlider` の `mousePressEvent`・`mouseMoveEvent`・`mouseReleaseEvent` 拡張
3. `player.py` に `_on_ab_drag_finished` 接続を追加
4. テストパス確認

### US4: スピンボックス幅修正（P3）

1. `test_bookmark_row_layout.py` でスピンボックス幅テストを追加（`minimumWidth()` の検証）
2. `bookmark_row.py` の `setFixedWidth` を `setMinimumWidth` に変更
3. テストパス確認

---

## Constitution Check（Post-Design）

| 原則 | 判定 | 根拠 |
|------|------|------|
| I. テストファースト | ✅ PASS | US ごとにテストを先に書く設計を維持 |
| II. シンプルさ重視 | ✅ PASS | 既存クラス拡張のみ。新クラスなし |
| III. 過度な抽象化の禁止 | ✅ PASS | `set_ab_preview` は 1 箇所（BookmarkSlider）でのみ定義・使用 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットメッセージを日本語で記述 |
