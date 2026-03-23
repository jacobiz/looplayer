# Tasks: 表示修正 — サイドパネルデフォルト ON・AB点アイコン改善

**Input**: Design documents from `/specs/025-ui-display-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: 憲法 I「テストファースト」により US1（デフォルト値変更）はテストを先に書く。US2（アイコン変更）は視覚確認のみで十分。

**Organization**: 2 つの独立した修正。US1 と US2 は完全に独立しており並列実装可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル、依存なし）
- **[Story]**: 対象ユーザーストーリー (US1, US2)

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 変更対象ファイルの確認と事前準備

- [x] T001 既存テストが全件パスすることを確認する: `pytest tests/unit/test_app_settings.py -v`

---

## Phase 2: Foundational（ブロッキング前提タスク）

該当なし — Phase 3 を直接開始できる。

---

## Phase 3: User Story 1 - アプリ起動時にブックマークサイドパネルが最初から表示される (Priority: P1) 🎯 MVP

**Goal**: `bookmark_panel_visible` のデフォルト値を `True` に変更し、初回起動時にサイドパネルが表示される

**Independent Test**: 設定ファイルなしの状態で `AppSettings().bookmark_panel_visible` が `True` を返すことを確認できる

### Tests for User Story 1 ⚠️ テストを書いてから実装する

> **NOTE: 以下のテストを先に追加し、FAIL することを確認してから T004 の実装に進むこと**

- [x] T002 [US1] `bookmark_panel_visible` のデフォルト値が `True` であることを確認するテストを `tests/unit/test_app_settings.py` に追加する（設定ファイルにキーが存在しない場合）
- [x] T003 [US1] テストが FAIL することを確認する: `pytest tests/unit/test_app_settings.py -k "bookmark_panel" -v`

### Implementation for User Story 1

- [x] T004 [US1] `looplayer/app_settings.py` L.140 の `_data.get("bookmark_panel_visible", False)` を `_data.get("bookmark_panel_visible", True)` に変更する
- [x] T005 [US1] テストが PASS することを確認する: `pytest tests/unit/test_app_settings.py -k "bookmark_panel" -v`

**Checkpoint**: `AppSettings().bookmark_panel_visible` が設定ファイルなしで `True` を返す。

---

## Phase 4: User Story 2 - A点・B点ボタンのアイコンで始点・終点が直感的に判別できる (Priority: P2)

**Goal**: A点セットを `SP_FileDialogStart`、B点セットを `SP_FileDialogEnd` に変更する

**Independent Test**: アプリを起動してボタンのアイコンが変わっていることを目視確認できる（ユニットテスト不要）

### Implementation for User Story 2

- [x] T006 [P] [US2] `looplayer/player.py` L.283 の `SP_MediaSeekBackward` を `SP_MediaSkipBackward` に変更する（SP_FileDialogStart は save_bookmark_btn と重複のため）
- [x] T007 [P] [US2] `looplayer/player.py` L.284 の `SP_MediaSeekForward` を `SP_FileDialogEnd` に変更する

**Checkpoint**: `python main.py` でアプリを起動し、A点・B点ボタンのアイコンが `|◀` / `▶|` 相当に変わっていることを確認。

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T008 全テストスイートがパスすることを確認する: `pytest tests/unit/test_app_settings.py -v`
- [ ] T009 [P] `quickstart.md` の手順に沿って手動動作確認を実施する（設定ファイルなしで起動 → サイドパネル表示確認、アイコン確認）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 即開始可
- **Phase 3 (US1)**: Phase 1 完了後
- **Phase 4 (US2)**: Phase 1 完了後（US1 と完全独立 — 並列実行可）
- **Phase 5 (Polish)**: Phase 3 & 4 完了後

### User Story Dependencies

- **US1 (P1)**: 独立（`app_settings.py` のみ）
- **US2 (P2)**: 独立（`player.py` のみ）— US1 完了を待たずに実装可

### ストーリー内の実行順序

```
T001（既存テスト確認）
    ↓
T002（US1テスト追加）  ←→  T006/T007（US2実装、並列可）
    ↓
T003（FAIL確認）
    ↓
T004（US1実装）
    ↓
T005（US1 PASS確認）
    ↓
T008（全テスト確認）
T009（手動確認）
```

### Parallel Opportunities

- T006, T007 — US2 の2行変更は同一ファイルのため実質同時に対応可
- US2（T006/T007）は US1 のテスト追加（T002〜T003）と並列実行可

---

## Parallel Example: US1 と US2 を並列実行

```
# US1（テストファースト）
T002 → T003（FAIL確認）→ T004 → T005（PASS確認）

# US2（実装のみ、同時に進めてよい）
T006 + T007（同時）
```

---

## Implementation Strategy

### MVP（US1 のみ）

1. T001: 既存テスト確認
2. T002〜T005: テストファースト → 実装 → PASS
3. **STOP and VALIDATE**: 設定ファイルなしで起動しサイドパネルが表示されることを確認

### Full Delivery

1. MVP (US1) 完了
2. T006/T007 (US2): アイコン変更（各1行）
3. T008/T009: 全テスト + 手動確認

---

## Notes

- US1 と US2 は完全独立。どちらから始めても良い
- US2 はコード2行の変更のみ。テストは不要（視覚確認で十分）
- US1 のデフォルト値変更は既存ユーザーに影響しない（設定ファイルにキーがあれば優先）
- テストは失敗してから実装する（憲法 I 遵守）
