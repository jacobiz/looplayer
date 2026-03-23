# Tasks: シークバーズーム時の現在位置インジケーター表示

**Input**: Design documents from `/specs/024-seekbar-zoom-position/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: 憲法 I「テストファースト」により必須。先にテストを書き、失敗を確認してから実装する。

**Organization**: 2 つのユーザーストーリーに対応したタスク。US1 と US2 は同一の実装（`set_position_ms`）で達成されるため、実装タスクは US1 にまとめ、US2 はテストのみ。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル、依存なし）
- **[Story]**: 対象ユーザーストーリー (US1, US2)

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 変更対象ファイルの確認と事前準備

- [x] T001 現在のテスト全件がパスすることを確認する: `pytest tests/unit/test_bookmark_slider_zoom.py -v`

---

## Phase 2: Foundational（ブロッキング前提タスク）

**Purpose**: 変更点はすべて既存ファイルへの追加のみ。新規ファイル・スキーマ変更なし。

該当なし — Phase 3 を直接開始できる。

---

## Phase 3: User Story 1 - ズーム中の現在位置を正確に把握する (Priority: P1) 🎯 MVP

**Goal**: ズームモード有効時、QSlider のハンドルがズーム範囲内の正しい相対位置に表示される

**Independent Test**: 動画を再生しながらズームを有効にし、ハンドルがズーム範囲内の正確な位置に表示されることを確認できる

### Tests for User Story 1 ⚠️ テストを書いてから実装する

> **NOTE: 以下のテストを先に追加し、実行して FAIL することを確認してから T007 の実装に進むこと**

- [x] T002 [US1] `TestSetPositionMs` クラスを `tests/unit/test_bookmark_slider_zoom.py` に追加: ズーム有効・範囲内の位置 → `value == 500`（中央）のテスト
- [x] T003 [P] [US1] ズーム有効・zoom_start_ms → `value == 0`（左端）のテストを `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T004 [P] [US1] ズーム有効・zoom_end_ms → `value == 1000`（右端）のテストを `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T005 [P] [US1] ズーム無効時の通常マッピング（duration の 50% → `value == 500`）のテストを `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T006 テストが FAIL することを確認する: `pytest tests/unit/test_bookmark_slider_zoom.py::TestSetPositionMs -v`（`AttributeError` で失敗するはず）

### Implementation for User Story 1

- [x] T007 [US1] `BookmarkSlider.set_position_ms(current_ms: int) -> None` を `looplayer/widgets/bookmark_slider.py` の `set_bookmarks()` メソッドの後に追加する（ズーム有効時: `zoom_start〜zoom_end` の相対値に変換、無効時: `duration_ms` 全体の比率で変換して `setValue` を呼ぶ）
- [x] T008 [US1] `player.py` の `_on_timer()` L.1124 を `seek_slider.set_position_ms(int(pos * length_ms))` に変更する
- [x] T009 [US1] テストが PASS することを確認する: `pytest tests/unit/test_bookmark_slider_zoom.py::TestSetPositionMs -v`

**Checkpoint**: ズームモード有効時にハンドルが正しい位置に表示される。`python main.py` で動作確認可能。

---

## Phase 4: User Story 2 - ズーム範囲外での現在位置の認識 (Priority: P2)

**Goal**: 再生位置がズーム範囲外の場合、マーカーがシークバーの端（左端または右端）に固定表示される

**Independent Test**: 現在位置がズーム範囲外の状態でズームを有効にし、マーカーが端に固定されることを確認できる（T007 の実装で Qt の value クリップにより自動達成）

### Tests for User Story 2 ⚠️ テストを書いてから確認する

> **NOTE: T007 完了後にこれらのテストを追加し、PASS することを確認する（実装追加は不要）**

- [x] T010 [US2] ズーム有効・範囲より前の位置（`current_ms < zoom_start_ms`）→ `value == 0` のテストを `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T011 [P] [US2] ズーム有効・範囲より後の位置（`current_ms > zoom_end_ms`）→ `value == 1000` のテストを `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T012 [P] [US2] `duration_ms == 0` 時のゼロ除算安全性テスト（`value == 0`）を `tests/unit/test_bookmark_slider_zoom.py` に追加
- [x] T013 [US2] テストが PASS することを確認する: `pytest tests/unit/test_bookmark_slider_zoom.py::TestSetPositionMs -v`

**Checkpoint**: ズーム範囲外でもマーカーが端に固定される動作が確認できる。

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 全体品質確認

- [x] T014 全テストスイートがパスすることを確認する: `pytest tests/ -v`
- [ ] T015 [P] `quickstart.md` の手順に沿って手動動作確認を実施する（ズーム有効化・解除・範囲内外での位置確認）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし — 即開始可
- **Phase 3 (US1)**: Phase 1 完了後 — ブロッキングなし
- **Phase 4 (US2)**: T007（`set_position_ms` 実装）完了後 — US2 は US1 の実装で自動達成
- **Phase 5 (Polish)**: Phase 3 & 4 完了後

### User Story Dependencies

- **US1 (P1)**: 即開始可（既存ファイルへの追加のみ）
- **US2 (P2)**: US1 の T007 完了後（同一実装で達成されるためテストのみ追加）

### ストーリー内の実行順序

```
T002〜T005（テスト追加、並列可）
    ↓
T006（FAIL 確認）
    ↓
T007（set_position_ms 実装）
    ↓
T008（player.py 修正）
    ↓
T009（PASS 確認）
    ↓
T010〜T012（US2 テスト追加、並列可）
T013（PASS 確認）
    ↓
T014〜T015（最終確認）
```

### Parallel Opportunities

- T003, T004, T005 — 並列実行可（同一ファイルの異なるテストメソッド）
- T008 — T007 完了後に実行（player.py 修正）
- T009 — T008 完了後に実行（テスト PASS 確認）、T008 とは順序依存あり
- T010, T011, T012 — 並列実行可

---

## Parallel Example: User Story 1

```bash
# テスト追加（並列）:
Task T003: "ズーム有効・zoom_start_ms → value == 0 のテスト追加"
Task T004: "ズーム有効・zoom_end_ms → value == 1000 のテスト追加"
Task T005: "ズーム無効時の通常マッピングテスト追加"

# 実装後（シーケンシャル）:
Task T008: "player.py _on_timer 修正" → 完了後に
Task T009: "US1 テスト PASS 確認"
```

---

## Implementation Strategy

### MVP（US1 のみ）

1. Phase 1: T001（既存テスト確認）
2. Phase 3: T002〜T009（テストファースト → 実装 → PASS）
3. **STOP and VALIDATE**: `python main.py` でズーム中のハンドル位置を確認

### Incremental Delivery

1. MVP (US1) 完了 → ズーム中の正確な位置表示が動作
2. US2 テスト追加 (T010〜T013) → 範囲外の端固定も確認済み
3. 全テスト通過 → リリース可能

---

## Notes

- [P] タスク = 別ファイルまたは独立したコード、依存なし
- US2 の実装は US1 と同一（Qt の `setValue` クリップで自動達成）— テストのみ追加
- テストは失敗してから実装する（憲法 I 遵守）
- 各チェックポイントでコミットする
