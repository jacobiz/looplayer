# Tasks: プレイヤーメニュー基本機能

**Input**: Design documents from `/specs/003-player-menus/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Tests**: 憲法 I（テストファースト）に基づき、各実装タスクの前にテストタスクを含める。

**Organization**: タスクはユーザーストーリー単位でグループ化し、各ストーリーを独立して実装・テスト可能とする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1/US2/US3）
- 各タスクには具体的なファイルパスを含める

---

## Phase 1: Setup（テストファイル骨格作成）

**Purpose**: テスト環境が動作することを確認し、RED を確認する基盤を整える

- [x] T001 [P] ユニットテストファイルの骨格を作成 — `tests/unit/test_volume_controls.py`、`tests/unit/test_playback_speed.py`
- [x] T002 [P] 統合テストファイルの骨格を作成 — `tests/integration/test_menus.py`、`tests/integration/test_fullscreen.py`

**Checkpoint**: `pytest tests/ -v` が収集エラーなく完走すること

---

## Phase 2: Foundational（controls_panel リファクタリング）

**Purpose**: フルスクリーン時の一括 hide/show と音量スライダー配置に必要なコンテナを準備する。US2・US3 がブロックされる。

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの実装を開始しない

- [x] T003 `looplayer/player.py` の `_build_ui()` をリファクタリングして `controls_panel`（`QWidget`）コンテナを追加し、シークバー・再生ボタン群・ABループコントロール・ブックマーク保存ボタン・ブックマークパネルを `controls_panel` の `QVBoxLayout` 内にラップする（`video_frame` は直接 `central` に残す）

**Checkpoint**: `pytest tests/ -v` が引き続き 74 件 PASS すること（既存テスト回帰なし）

---

## Phase 3: User Story 1 - ファイルメニューとキーボードショートカット (Priority: P1) 🎯 MVP

**Goal**: メニューバーの追加と基本ショートカット（ファイル操作・再生・シーク）により、マウス不要で動画を操作できる

**Independent Test**: メニューバーに「ファイル」「再生」「表示」が存在し、`Space` で再生/一時停止、`←`/`→` で 5 秒シーク、`Ctrl+O` でファイルダイアログが開き、`Ctrl+Q` でアプリ終了することを確認

### US1 テスト

- [x] T004 [US1] US1 の統合テストを作成（メニュー項目の存在確認・`Space`/`←`/`→`/`Ctrl+O` ショートカットの動作）— `tests/integration/test_menus.py`（RED 確認後 T005 へ）

### US1 実装

- [x] T005 [US1] `looplayer/player.py` に `QMenuBar` を追加し「ファイル」メニュー（「開く…」`Ctrl+O`・セパレーター・「終了」`Ctrl+Q`）を実装、全アクションに `ApplicationShortcut` コンテキストを設定
- [x] T006 [US1] `looplayer/player.py` に「再生」メニューの骨格と `Space`（再生/一時停止）・`←`/`→`（5秒シーク）ショートカットを実装（`_seek_relative(ms)` メソッド追加）
- [x] T007 [US1] `looplayer/player.py` に「表示」メニューの骨格を追加（項目は後のフェーズで追加）

**Checkpoint**: `pytest tests/integration/test_menus.py -v` が US1 テスト GREEN、`python main.py` でメニューバーが表示されショートカットが動作すること

---

## Phase 4: User Story 2 - 再生コントロールメニューとシーク操作 (Priority: P2)

**Goal**: 音量スライダー常時表示・ミュート・再生速度変更がメニューとキーボードの両方から操作できる

**Independent Test**: 音量スライダーがコントロールバーに表示され、`↑`/`↓` キーで音量が変化し、`M` でミュート/復元、「再生速度 > 1.5倍」で速度が変わりファイルを開き直すと 1.0倍 にリセットされることを確認

### US2 テスト

- [x] T008 [US2] 音量状態の単体テストを作成（初期値 80%・`_set_volume` のクランプ・ミュート状態遷移・ミュート解除後の音量復元）— `tests/unit/test_volume_controls.py`（RED 確認後 T010 へ）
- [x] T009 [P] [US2] 再生速度状態の単体テストを作成（`_set_playback_rate` の有効値・`open_file` 時のリセット）— `tests/unit/test_playback_speed.py`（RED 確認後 T014 へ）

### US2 実装

- [x] T010 [US2] `looplayer/player.py` に `_volume: int = 80`、`_is_muted: bool = False`、`_pre_mute_volume: int = 80` フィールドと `_set_volume(v: int)` メソッド（0〜100 クランプ・スライダー同期・VLC 反映）を実装（T008 RED 確認後）
- [x] T011 [US2] `looplayer/player.py` に `_toggle_mute()` メソッドを実装（ミュート時: `_pre_mute_volume` 保存・音量 0 設定・`_is_muted=True`、復帰時: 保存音量を復元）
- [x] T012 [US2] `looplayer/player.py` の `controls_panel` 内（シークバーの上）に音量スライダー（`QSlider`、範囲 0〜100、初期値 80）と音量ラベル（「80%」形式）を追加し `_set_volume()` に接続
- [x] T013 [US2] `looplayer/player.py` の「再生」メニューに「音量を上げる」(`↑`)・「音量を下げる」(`↓`)・「ミュート」(`M`) アクションを追加し `_set_volume`・`_toggle_mute` に接続、`M` ショートカットも接続
- [x] T014 [US2] `looplayer/player.py` に `_playback_rate: float = 1.0` フィールドと `_set_playback_rate(rate: float)` メソッドを実装し、`open_file()` に `set_rate(1.0)` リセット処理を追加（T009 RED 確認後）
- [x] T015 [US2] `looplayer/player.py` の「再生」メニューに「再生速度」サブメニュー（`QActionGroup` 排他選択: 0.5 / 0.75 / **1.0** / 1.25 / 1.5 / 2.0 倍、デフォルト 1.0 にチェック）を追加し `_set_playback_rate` に接続

**Checkpoint**: `pytest tests/unit/test_volume_controls.py tests/unit/test_playback_speed.py -v` が GREEN、`python main.py` で音量スライダーが表示され操作できること

---

## Phase 5: User Story 3 - 表示メニューとフルスクリーン (Priority: P3)

**Goal**: `F` キー 1 押しでフルスクリーンに切り替わり（コントロール類全非表示）、`Esc` で復帰。常に最前面トグルも動作する

**Independent Test**: `toggle_fullscreen()` 呼び出しで `isFullScreen()` が変化し、`controls_panel` と `menuBar()` が hide/show されることを確認。`Esc` で通常ウィンドウに戻り、ABループ状態が維持されることを確認

### US3 テスト

- [x] T016 [US3] フルスクリーン統合テストを作成（`toggle_fullscreen()` の前後状態・`controls_panel` の visibility・`Esc` で復帰・フルスクリーン中の ABループ状態維持）— `tests/integration/test_fullscreen.py`（RED 確認後 T017 へ）

### US3 実装

- [x] T017 [US3] `looplayer/player.py` に `toggle_fullscreen()` メソッドを実装（`showFullScreen`/`showNormal`・`controls_panel.hide()/show()`・`menuBar().hide()/show()`）し「表示」メニューに「フルスクリーン」`F` アクションと `Esc` アクションを追加
- [x] T018 [US3] `looplayer/player.py` に FR-016 対応のマウス追跡を実装（フルスクリーン中に `video_frame.setMouseTracking(True)` を設定・`mouseMoveEvent` でカーソルが画面上端 15px 以内なら `menuBar().show()` + `_menu_hide_timer`（2秒後 `menuBar().hide()`）を起動）
- [x] T019 [US3] `looplayer/player.py` に「常に最前面に表示」トグルを実装（`WindowStaysOnTopHint` フラグのセット/解除・`setWindowFlags` 後に `show()` 呼び出し・`QAction.setChecked` でメニューのチェックマーク更新）し「表示」メニューにセパレーター付きで追加

**Checkpoint**: `pytest tests/integration/test_fullscreen.py -v` が GREEN、`python main.py` で `F` キーでフルスクリーンに切り替わり `Esc` で復帰すること

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全ユーザーストーリー完了後の確認・細部調整

- [x] T020 [P] `↑`/`↓` キーが QSpinBox にフォーカスがある場合でも音量操作が優先されることを確認し、必要に応じて `ApplicationShortcut` コンテキストの設定漏れを修正 — `looplayer/player.py`
- [x] T021 全テスト実行・全件パス確認 — `pytest tests/ -v`（既存 74 件 + 新規テスト: 114 件 PASS）
- [ ] T022 `python main.py` で quickstart.md の実装フロー3ステップ（US1→US2→US3）を手動動作確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能
- **Foundational (Phase 2)**: Phase 1 完了後 — **全ユーザーストーリーをブロック**
- **User Stories (Phase 3+)**: Phase 2 完了後にそれぞれ開始可能（優先度順: P1→P2→P3）
- **Polish (Phase 6)**: 全ユーザーストーリー完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始可能。他のストーリーへの依存なし
- **US2 (P2)**: Phase 2 完了後かつ US1 完了後（「再生」メニュー骨格が US1 で作成されるため）
- **US3 (P3)**: Phase 2 完了後かつ US1 完了後（「表示」メニュー骨格が US1 で作成されるため）

### Within Each User Story

1. テストを書いて **RED（失敗）を確認** してから実装開始
2. 状態管理 → ロジック → UI 接続 → メニュー統合 の順
3. ストーリー完了後に `pytest` でチェックポイントを確認してからコミット

### Parallel Opportunities

- Phase 1: T001・T002 は並列実行可能（異なるファイル）
- Phase 4: T008・T009 は並列実行可能（異なるファイル）
- Phase 6: T020 は他タスクと並列実行可能

---

## Parallel Example: User Story 2

```bash
# Phase 4 内の並列可能タスク（Phase 3 完了後）:
Task T008: "音量状態の単体テストを作成 — tests/unit/test_volume_controls.py"
Task T009: "再生速度状態の単体テストを作成 — tests/unit/test_playback_speed.py"

# T008, T009 の RED 確認後に順番に:
Task T010 → T011 → T012 → T013 → T014 → T015
```

---

## Implementation Strategy

### MVP First（User Story 1 のみ）

1. Phase 1 完了: テストファイル骨格作成
2. Phase 2 完了: `controls_panel` リファクタリング（**必須: US2/US3 をブロック**）
3. Phase 3 完了: US1 メニューバー + ショートカット
4. **STOP & VALIDATE**: `pytest tests/integration/test_menus.py -v` GREEN → `python main.py` で動作確認
5. 必要なら MVP としてデモ

### Incremental Delivery

1. Setup + Foundational → `controls_panel` 準備完了
2. US1 追加 → メニューバー + 基本ショートカット（MVP）
3. US2 追加 → 音量・ミュート・再生速度
4. US3 追加 → フルスクリーン・常に最前面

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベルでタスクをユーザーストーリーにトレース
- **憲法 I**: テストを先に書き、RED を確認してから実装する
- **憲法 II/III**: 新モジュールを作らない。全変更は `looplayer/player.py` 内に完結
- 各チェックポイントで `pytest` をパスしてからコミットする
- `ApplicationShortcut` コンテキストをすべてのアクションに設定してショートカット競合を防ぐ（research.md #6 参照）
