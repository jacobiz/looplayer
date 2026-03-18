# Tasks: プレイヤー UI バグ修正・操作性改善

**Input**: Design documents from `/specs/013-player-ui-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Constitution I（テストファースト）により、各ユーザーストーリーでテストを先に書いてから実装する。

**Organization**: タスクはユーザーストーリーごとにグループ化。各ストーリーは独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並行実行可能（異なるファイル、依存なし）
- **[Story]**: 対応するユーザーストーリー (US1〜US4)
- 各タスクに正確なファイルパスを含む

---

## Phase 1: Setup（既存確認）

**Purpose**: テスト環境の動作確認と既存テストのベースライン確立

- [x] T001 既存テストスイートを全実行してベースラインを確認する（`pytest tests/ -v`）

---

## Phase 2: Foundational（共有基盤）

**Purpose**: 複数のユーザーストーリーが依存する基盤。US2/US3 の両方が `BookmarkSlider` の拡張に依存するため、共有の型定義を先に確認する。

**⚠️ CRITICAL**: このフェーズ完了後に US1〜US4 の実装を開始する

- [x] T002 `looplayer/widgets/bookmark_slider.py` の現状を確認し、拡張ポイント（`__init__`・`paintEvent`・マウスイベント）を把握する
- [x] T003 `looplayer/player.py` の `set_point_a`・`set_point_b`・`clear_ab_loop` の呼び出し箇所を確認する

**Checkpoint**: 既存コードの把握完了 → 各 US の実装開始可能

---

## Phase 3: User Story 1 — ESC キーでフルスクリーン解除 (Priority: P1) 🎯 MVP

**Goal**: フルスクリーン中に ESC キーを押すと、フォーカス状態に関わらず通常ウィンドウに戻る

**Independent Test**: フルスクリーン → スピンボックスにフォーカス → ESC → 通常ウィンドウ

### テスト（先に書いて失敗を確認）

> **NOTE: 実装前にテストを書き、FAIL することを確認すること**

- [x] T004 [US1] `tests/integration/test_fullscreen.py` に `TestEscapeShortcut` クラスを追加：`QShortcut` が存在し `_exit_fullscreen` に接続されていることを検証するテスト（`test_esc_shortcut_is_registered`）を記述する
- [x] T005 [US1] `tests/integration/test_fullscreen.py` に追加：フルスクリーン中に `esc_shortcut.activated` をシグナルで emit して通常ウィンドウに戻ることを検証するテスト（`test_esc_shortcut_exits_fullscreen`）を記述する
- [x] T006 [US1] `tests/integration/test_fullscreen.py` に追加：通常ウィンドウ中に ESC ショートカットを発火しても何も変化しないことを検証するテスト（`test_esc_shortcut_no_effect_in_normal_window`）を記述する

### 実装

- [x] T007 [US1] `looplayer/player.py` の `__init__` または `_setup_shortcuts` に `QShortcut(QKeySequence("Escape"), self)` を追加し `ApplicationShortcut` コンテキストで `_exit_fullscreen` に接続する
- [x] T008 [US1] T004〜T006 のテストが PASS することを確認する（`pytest tests/integration/test_fullscreen.py -v`）

**Checkpoint**: US1 完了 — ESC キーがフルスクリーンを確実に解除する

---

## Phase 4: User Story 2 — AB 点のシークバー上リアルタイム表示 (Priority: P2)

**Goal**: A/B 点設定後、即座にシークバー上にマーカー/バーが表示される

**Independent Test**: A 点セット → シークバーの `_ab_preview_a` が設定値と一致する

### テスト（先に書いて失敗を確認）

> **NOTE: 実装前にテストを書き、FAIL することを確認すること**

- [x] T009 [P] [US2] `tests/unit/test_bookmark_slider.py` に `TestAbPreview` クラスを追加：`set_ab_preview(a_ms, None)` 呼び出し後に `_ab_preview_a` が設定値、`_ab_preview_b` が None になることを検証する（`test_set_ab_preview_a_only`）
- [x] T010 [P] [US2] `tests/unit/test_bookmark_slider.py` に追加：`set_ab_preview(a_ms, b_ms)` 呼び出し後に両属性が正しく設定されることを検証する（`test_set_ab_preview_both`）
- [x] T011 [P] [US2] `tests/unit/test_bookmark_slider.py` に追加：`set_ab_preview(None, None)` 呼び出し後に両属性が None になることを検証する（`test_set_ab_preview_clear`）
- [x] T012 [US2] `tests/integration/test_ab_seekbar.py`（新規）を作成し、Player に動画なしの状態で `set_point_a()` 呼び出し後に `seek_slider._ab_preview_a` が設定されることを検証する統合テスト（`TestAbPreviewIntegration`）を記述する

### 実装

- [x] T013 [US2] `looplayer/widgets/bookmark_slider.py` の `__init__` に `_ab_preview_a: int | None = None`・`_ab_preview_b: int | None = None` を追加する
- [x] T014 [US2] `looplayer/widgets/bookmark_slider.py` に `set_ab_preview(a_ms: int | None, b_ms: int | None) -> None` メソッドを追加し、属性を更新して `self.update()` を呼び出す
- [x] T015 [US2] `looplayer/widgets/bookmark_slider.py` の `paintEvent` にブックマークバー描画後の AB 点プレビュー描画を追加する：A 点のみ = `QColor(255, 255, 255, 200)` 縦線（幅 3px）、A・B 両方 = `QColor(255, 255, 255, 120)` 半透明バー + 両端縦線
- [x] T016 [US2] `looplayer/player.py` の `set_point_a()` 末尾に `self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)` を追加する
- [x] T017 [US2] `looplayer/player.py` の `set_point_b()` 末尾に `self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)` を追加する
- [x] T018 [US2] `looplayer/player.py` の `clear_ab_loop()` （または AB 点リセット処理の末尾）に `self.seek_slider.set_ab_preview(None, None)` を追加する
- [x] T019 [US2] T009〜T012 のテストが PASS することを確認する（`pytest tests/unit/test_bookmark_slider.py tests/integration/test_ab_seekbar.py -v`）

**Checkpoint**: US2 完了 — A/B 点がリアルタイムでシークバーに表示される

---

## Phase 5: User Story 3 — シークバー上で AB 点をドラッグ操作 (Priority: P2)

**Goal**: シークバー上の A/B 点マーカーをドラッグして位置を変更できる

**Independent Test**: AB 点マーカー付近でマウスドラッグ → `ab_point_drag_finished` シグナルが emit される

**⚠️ Note**: US2（T013〜T018）完了後に開始すること（BookmarkSlider の AB プレビュー属性が必要）

### テスト（先に書いて失敗を確認）

> **NOTE: 実装前にテストを書き、FAIL することを確認すること**

- [x] T020 [P] [US3] `tests/unit/test_bookmark_slider.py` に `TestAbDrag` クラスを追加：A 点マーカー付近（±6px）でマウスプレスすると `_ab_drag_target` が `"a"` になることを検証する（`test_mousepress_near_a_sets_drag_target_a`）
- [x] T021 [P] [US3] `tests/unit/test_bookmark_slider.py` に追加：B 点マーカー付近でマウスプレスすると `_ab_drag_target` が `"b"` になることを検証する（`test_mousepress_near_b_sets_drag_target_b`）
- [x] T022 [P] [US3] `tests/unit/test_bookmark_slider.py` に追加：ドラッグ後にマウスリリースすると `ab_point_drag_finished` シグナルが emit され `_ab_drag_target` が None にリセットされることを検証する（`test_mouserelease_emits_ab_drag_finished`）
- [x] T023 [P] [US3] `tests/unit/test_bookmark_slider.py` に追加：A 点を B 点より右にドラッグしようとした場合、emit される ms 値が B 点 ms より小さくクランプされることを検証する（`test_a_drag_clamped_at_b_point`）
- [x] T023b [P] [US3] `tests/unit/test_bookmark_slider.py` に追加：B 点を A 点より左にドラッグしようとした場合、emit される ms 値が A 点 ms より大きくクランプされることを検証する（`test_b_drag_clamped_at_a_point`）— FR-008 後半・US3 Acceptance Scenario 4 対応
- [x] T024 [US3] `tests/integration/test_ab_seekbar.py` に `TestAbDragIntegration` クラスを追加：Player の `_on_ab_drag_finished("a", 3000)` 呼び出し後に `ab_point_a == 3000` かつ `seek_slider._ab_preview_a == 3000` になることを検証する

### 実装

- [x] T025 [US3] `looplayer/widgets/bookmark_slider.py` の `__init__` に `_ab_drag_target: str | None = None` を追加する
- [x] T026 [US3] `looplayer/widgets/bookmark_slider.py` に `_find_ab_drag_target(x: int) -> str | None` メソッドを追加する：`_ab_preview_a`・`_ab_preview_b` の X 座標から ±6px 以内かを判定し `"a"` / `"b"` / `None` を返す
- [x] T027 [US3] `looplayer/widgets/bookmark_slider.py` の `mousePressEvent` を拡張する：既存のブックマークバークリック判定より前に `_find_ab_drag_target` を呼び出し、マッチした場合は `_ab_drag_target` をセットして `event.accept()` で return する
- [x] T028 [US3] `looplayer/widgets/bookmark_slider.py` の `mouseMoveEvent` を拡張する：`_ab_drag_target` が非 None の場合、ドラッグ位置 ms を計算し A/B のクランプ制約を適用して `_ab_preview_a`/`_ab_preview_b` を更新・`self.update()` を呼び出す
- [x] T029 [US3] `looplayer/widgets/bookmark_slider.py` に `ab_point_drag_finished = pyqtSignal(str, int)` シグナルを追加し、`mouseReleaseEvent` 内で `_ab_drag_target` が非 None の場合にシグナルを emit して `_ab_drag_target = None` にリセットする
- [x] T030 [US3] `looplayer/widgets/bookmark_slider.py` の `mousePressEvent` で AB ドラッグ中はブックマークバークリック判定・トラックシークを**スキップ**する（AB ドラッグ優先度が高い）
- [x] T031 [US3] `looplayer/player.py` に `_on_ab_drag_finished(target: str, ms: int) -> None` メソッドを追加する：`target=="a"` → `self.ab_point_a = ms`、`target=="b"` → `self.ab_point_b = ms`、その後 `_update_ab_ui()` と `seek_slider.set_ab_preview(...)` を呼び出す
- [x] T032 [US3] `looplayer/player.py` の初期化部分で `self.seek_slider.ab_point_drag_finished.connect(self._on_ab_drag_finished)` を接続する
- [x] T033 [US3] T020〜T023b・T024 のテストが PASS することを確認する（`pytest tests/unit/test_bookmark_slider.py -k "TestAbDrag" tests/integration/test_ab_seekbar.py -v`）

**Checkpoint**: US3 完了 — AB 点マーカーをドラッグで位置変更できる

---

## Phase 6: User Story 4 — "ポーズ"・"繰返" 入力欄の表示改善 (Priority: P3)

**Goal**: スピンボックスの数値（1〜99、0.0〜10.0）が切り取られず読み取れる

**Independent Test**: `repeat_spin.minimumWidth() >= 68` かつ `pause_spin.minimumWidth() >= 75`

### テスト（先に書いて失敗を確認）

> **NOTE: 実装前にテストを書き、FAIL することを確認すること**

- [x] T034 [P] [US4] `tests/unit/test_bookmark_row_layout.py`（新規）を作成し、BookmarkRow の `repeat_spin.minimumWidth() >= 68` を検証するテスト（`test_repeat_spin_minimum_width`）を記述する
- [x] T035 [P] [US4] `tests/unit/test_bookmark_row_layout.py` に追加：`pause_spin.minimumWidth() >= 75` を検証するテスト（`test_pause_spin_minimum_width`）を記述する
- [x] T036 [P] [US4] `tests/unit/test_bookmark_row_layout.py` に追加：`repeat_spin.maximumWidth()` が `QWIDGETSIZE_MAX`（Qt の最大値）であること（fixedWidth でないこと）を検証するテスト（`test_repeat_spin_not_fixed_width`）を記述する

### 実装

- [x] T037 [US4] `looplayer/widgets/bookmark_row.py` の `repeat_spin.setFixedWidth(55)` を `repeat_spin.setMinimumWidth(68)` に変更する
- [x] T038 [US4] `looplayer/widgets/bookmark_row.py` の `pause_spin.setFixedWidth(64)` を `pause_spin.setMinimumWidth(75)` に変更する
- [x] T039 [US4] T034〜T036 のテストが PASS することを確認する（`pytest tests/unit/test_bookmark_row_layout.py -v`）

**Checkpoint**: US4 完了 — スピンボックスの数値が正常に表示される

---

## Phase 7: Polish & 全体検証

**Purpose**: 全ストーリーの統合確認とリグレッション検証

- [x] T040 [P] 全テストスイートを実行してリグレッションがないことを確認する（`pytest tests/ -v`）
- [x] T041 [P] `quickstart.md` の手動確認チェックリスト（5項目）をアプリ起動して検証する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1（Setup）**: 依存なし — 即座に開始可能
- **Phase 2（Foundational）**: Phase 1 完了後
- **Phase 3（US1）**: Phase 2 完了後 — 他のストーリーと独立して実行可能
- **Phase 4（US2）**: Phase 2 完了後 — US1 と並行実行可能
- **Phase 5（US3）**: **Phase 4（US2）完了後** — BookmarkSlider の AB プレビュー属性が必要
- **Phase 6（US4）**: Phase 2 完了後 — US1/US2/US3 と独立して並行実行可能
- **Phase 7（Polish）**: 全ストーリー完了後

### User Story Dependencies

- **US1 (P1)**: 依存なし — Phase 2 完了後すぐ開始可能
- **US2 (P2)**: 依存なし — Phase 2 完了後すぐ開始可能
- **US3 (P2)**: **US2 に依存** — US2 完了後に開始
- **US4 (P3)**: 依存なし — Phase 2 完了後すぐ開始可能

### 各ストーリー内の実行順

1. テストを書く → FAIL を確認
2. 実装する
3. テストが PASS することを確認
4. コミット

### Parallel Opportunities

```bash
# Phase 2 完了後、以下を並行実行可能:
US1: test_fullscreen.py テスト追加 → player.py QShortcut 追加
US2: test_bookmark_slider.py テスト追加 → bookmark_slider.py / player.py 実装
US4: test_bookmark_row_layout.py テスト追加 → bookmark_row.py 実装

# US2 完了後:
US3: test_bookmark_slider.py ドラッグテスト追加 → bookmark_slider.py / player.py 実装
```

---

## Parallel Example: User Story 2

```bash
# US2 テスト（並行で書ける）:
Task T009: "test_set_ab_preview_a_only を tests/unit/test_bookmark_slider.py に追加"
Task T010: "test_set_ab_preview_both を tests/unit/test_bookmark_slider.py に追加"
Task T011: "test_set_ab_preview_clear を tests/unit/test_bookmark_slider.py に追加"
Task T012: "TestAbPreviewIntegration を tests/integration/test_ab_seekbar.py に追加"

# US2 実装（T013→T014→T015 の順、T016〜T018 は並行可能）:
Task T013: "__init__ に _ab_preview_a/_ab_preview_b を追加"
Task T014: "set_ab_preview() メソッドを追加"（T013 後）
Task T015: "paintEvent に描画ロジックを追加"（T014 後）
Task T016 [P]: "player.py の set_point_a() に呼び出しを追加"
Task T017 [P]: "player.py の set_point_b() に呼び出しを追加"
Task T018 [P]: "player.py の clear_ab_loop() に呼び出しを追加"
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1: Setup（T001）
2. Phase 2: Foundational（T002, T003）
3. Phase 3: US1（T004〜T008）
4. **STOP & VALIDATE**: ESC キーバグが修正されたことをテストと手動で確認
5. コミット・デモ可能な状態

### Incremental Delivery

1. Setup + Foundational → 基盤確認
2. US1 → ESC バグ修正（即座にユーザー価値）
3. US2 → AB 点プレビュー表示
4. US3 → AB 点ドラッグ（US2 完了後）
5. US4 → スピンボックス幅修正（任意のタイミング）
6. 各ストーリーが前のストーリーを壊さないことを確認

---

## Notes

- `[P]` タスク = 異なるファイル、依存関係なし → 並行実行可能
- `[US?]` ラベルは対応するユーザーストーリーへのトレーサビリティ
- テストは必ず先に書いて FAIL を確認してから実装する（Constitution I）
- 各タスクまたは論理グループ完了後にコミットする
- リグレッションを防ぐため T040 は全タスク完了後に実行する
