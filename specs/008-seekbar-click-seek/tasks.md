# Tasks: シークバークリックシーク

**Input**: Design documents from `/specs/008-seekbar-click-seek/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, contracts/ui-signals.md ✅, quickstart.md ✅

**Tests**: 憲法 I（テストファースト）に従い、すべての実装タスクの前にテストを記述する。

**Organization**: US1（クリック・ドラッグシーク）→ US2（ブックマークバーリグレッション確認）の順。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 既存プロジェクト構造の確認。新規依存関係なし。

- [X] T001 既存テストファイル `tests/unit/test_bookmark_slider.py` の構造を確認し、新テストクラスを追加する準備（ファイル末尾のクラス配置を把握）

---

## Phase 2: Foundational（ブロッキング前提条件）

**Purpose**: US1・US2 どちらも同一ファイルを操作するため、特別な前提インフラはない。Phase 1 完了で直ちに開始可能。

**⚠️ CRITICAL**: T001 完了後に開始。

*(このフェーズに独立タスクなし。US1 の最初のテスト作成が事実上の基盤となる)*

---

## Phase 3: User Story 1 — シークバートラッククリックでシーク (Priority: P1) 🎯 MVP

**Goal**: シークバーのトラックをクリック・ドラッグすると `seek_requested(ms)` シグナルが emit され、VideoPlayer が再生位置を更新する。

**Independent Test**: `tests/unit/test_bookmark_slider.py::TestClickSeek` および `TestDragSeek` がすべてパスし、`BookmarkSlider.seek_requested` シグナルが正しい ms 値で発火することを確認する。

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T002 [US1] `tests/unit/test_bookmark_slider.py` に `TestClickSeek` クラスを追加する。テスト内容:
  - `test_click_on_track_emits_seek_requested`: groove 幅が有効なとき、トラック中央クリックで `seek_requested` が duration の 50% 付近の ms 値で emit される
  - `test_click_at_left_emits_zero_ms`: groove 左端クリックで emit される ms が 0 またはそれに近い値
  - `test_click_at_right_emits_max_ms`: groove 右端クリックで emit される ms が duration に近い値
  - `test_click_when_duration_zero_does_not_emit`: `_duration_ms=0` の状態でクリックしても `seek_requested` が emit されない

- [X] T003 [US1] `tests/unit/test_bookmark_slider.py` に `TestDragSeek` クラスを追加する。テスト内容:
  - `test_drag_sets_dragging_flag`: トラッククリック後に `_dragging` が `True` になる
  - `test_release_clears_dragging_flag`: `mouseReleaseEvent` 後に `_dragging` が `False` になる
  - `test_drag_emits_seek_requested_on_move`: `_dragging=True` の状態で `mouseMoveEvent` を送ると `seek_requested` が emit される

### Implementation for User Story 1

- [X] T004 [US1] `looplayer/widgets/bookmark_slider.py` の `BookmarkSlider` クラスに以下を追加する:
  - クラス変数: `seek_requested = pyqtSignal(int)` (先頭のシグナル定義に追加)
  - `__init__` にインスタンス変数: `self._dragging: bool = False`

- [X] T005 [US1] `looplayer/widgets/bookmark_slider.py` に `_x_to_ms(self, x: int, groove: QRect) -> int` メソッドを追加する:
  - `groove.width() <= 0` の場合は `0` を返す
  - `ratio = max(0.0, min(1.0, (x - groove.left()) / groove.width()))`
  - `return int(ratio * self._duration_ms)`

- [X] T006 [US1] `looplayer/widgets/bookmark_slider.py` の `mousePressEvent` を拡張する:
  - 左クリック・ブックマークバー未命中・`_duration_ms > 0` の場合:
    - `groove = self._groove_rect()`
    - `ms = self._x_to_ms(event.position().toPoint().x(), groove)` で ms を計算
    - `self.seek_requested.emit(ms)` を emit
    - `self._dragging = True`
    - `event.accept()` で処理を終了（`super()` を呼ばない）
  - 既存のブックマークバー命中ケース（`bm_id is not None`）の動作は変更しない

- [X] T007 [US1] `looplayer/widgets/bookmark_slider.py` に `mouseMoveEvent(self, event)` を追加する:
  - `self._dragging` が `True` かつ左ボタン押下中の場合:
    - `groove = self._groove_rect()`
    - `ms = self._x_to_ms(event.position().toPoint().x(), groove)`
    - `self.seek_requested.emit(ms)`
  - それ以外は `super().mouseMoveEvent(event)` を呼ぶ

- [X] T008 [US1] `looplayer/widgets/bookmark_slider.py` に `mouseReleaseEvent(self, event)` を追加する:
  - 左ボタンリリース時: `self._dragging = False`
  - `super().mouseReleaseEvent(event)` を呼ぶ

- [X] T009 [US1] `looplayer/player.py` に `_on_seek_ms(self, ms: int) -> None` メソッドを追加し、`seek_requested` シグナルと接続する:
  - `VideoPlayer.__init__` 内で `self.seek_slider.seek_requested.connect(self._on_seek_ms)` を追加（`bookmark_bar_clicked.connect` の直後）
  - `_on_seek_ms` の実装: `if self.media_player.get_length() > 0: self.media_player.set_time(ms)`

- [X] T010 [US1] `looplayer/player.py` の `_on_timer` メソッドの条件を更新してドラッグ中のスライダー上書きを防止する:
  - 変更前: `if length_ms > 0 and not self.seek_slider.isSliderDown():`
  - 変更後: `if length_ms > 0 and not self.seek_slider.isSliderDown() and not self.seek_slider._dragging:`

**Checkpoint**: `pytest tests/unit/test_bookmark_slider.py::TestClickSeek tests/unit/test_bookmark_slider.py::TestDragSeek -v` がすべてパスすること。

---

## Phase 4: User Story 2 — ブックマークバー上のクリックは既存挙動を維持 (Priority: P2)

**Goal**: US1 実装後も `bookmark_bar_clicked` シグナルが従来どおり発火し、`seek_requested` が emit されないことを確認する。

**Independent Test**: `tests/unit/test_bookmark_slider.py::TestBookmarkBarClickRegression` がすべてパスする。

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [US2] `tests/unit/test_bookmark_slider.py` に `TestBookmarkBarClickRegression` クラスを追加する。テスト内容:
  - `test_bookmark_bar_click_emits_bookmark_signal_not_seek`: ブックマークバーをクリックしたとき `bookmark_bar_clicked` が emit され、`seek_requested` は emit されない
  - `test_track_click_outside_bar_does_not_emit_bookmark_signal`: ブックマークバー外のトラッククリックで `bookmark_bar_clicked` が emit されない

### Implementation for User Story 2

*(T006 の `mousePressEvent` 実装がブックマークバー優先を保証しているため、追加実装は不要。テストがリグレッションを検証する。)*

**Checkpoint**: `pytest tests/unit/test_bookmark_slider.py -v` がすべてパスすること（既存テスト含む）。

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 全体テスト実行・クリーンアップ

- [X] T012 [P] `pytest tests/ -v` を実行し、全テストがパスすることを確認する（リグレッションゼロ）
- [ ] T013 quickstart.md の手動テストシナリオに従い、シークバークリック・ドラッグ・ブックマークバー非干渉を手動検証する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし・即開始可能
- **Foundational (Phase 2)**: Phase 1 完了後（実質 T001）
- **US1 (Phase 3)**: T001 完了後。テスト(T002, T003) → 実装(T004-T010) の順を厳守
- **US2 (Phase 4)**: T001〜T010 完了後
- **Polish (Phase 5)**: US1・US2 完了後

### User Story Dependencies

- **US1 (P1)**: Phase 1 完了後に開始。他の US に依存しない。
- **US2 (P2)**: US1 の実装完了後に開始（同一ファイルを検証するため）

### Within Each User Story

- テストを書いて **失敗** させてから実装する（憲法 I）
- `seek_requested` シグナル追加(T004) → `_x_to_ms` 追加(T005) → `mousePressEvent` 拡張(T006) → `mouseMoveEvent`(T007) → `mouseReleaseEvent`(T008) → VideoPlayer 接続(T009, T010)

### Parallel Opportunities

- T002 と T003（テストクラス 2 つ）は同一ファイルだが独立した記述 → 実際には逐次実行推奨（競合回避）
- T004〜T008（BookmarkSlider 変更）は T009〜T010（VideoPlayer 変更）と並行実行可能 [P]
- T012 と T013 は並行実行可能 [P]

---

## Parallel Example: User Story 1

```bash
# ウィジェット側とプレイヤー側を並行実装（同一ファイルへの変更がない場合）:
Task A: "T004-T008: BookmarkSlider にシグナル・メソッドを追加 (looplayer/widgets/bookmark_slider.py)"
Task B: "T009-T010: VideoPlayer に _on_seek_ms 接続・_on_timer 更新 (looplayer/player.py)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 完了: T001
2. US1 テスト作成: T002, T003（失敗確認）
3. US1 実装: T004→T005→T006→T007→T008→T009→T010
4. **STOP and VALIDATE**: `pytest tests/unit/test_bookmark_slider.py -v`
5. 手動確認: quickstart.md シナリオ 1〜3

### Incremental Delivery

1. T001〜T010: US1（クリック・ドラッグシーク）完成 → デモ可能
2. T011: US2（リグレッションテスト追加）完成 → 品質確認
3. T012〜T013: 全体検証 → マージ準備

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **憲法 I 必須**: T002・T003 は T004 より前に書き、必ず失敗させてから実装に進む
- `_x_to_ms` は `_ms_to_x` の逆関数。既存テスト (`TestMsToX`) を参考に境界値を確認する
- `_dragging` は公開プロパティではなく保護インスタンス変数（`_` プレフィックス）
- VideoPlayer から `seek_slider._dragging` を直接参照するのは単純化のため（抽象化不要 — 憲法 III）
