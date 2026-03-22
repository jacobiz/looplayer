# Tasks: ボタンアイコン追加

**Input**: Design documents from `/specs/023-button-icons/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: ユーザーストーリー単位でグループ化。Constitution I に従いテストを実装より先に作成する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル、依存なし）
- **[Story]**: 対応ユーザーストーリー番号

---

## Phase 1: Setup（共有インフラ）

**Purpose**: `looplayer/player.py` に `QStyle` を追加し、後続の全フェーズで使用できるようにする

- [x] T001 `QStyle` を `looplayer/player.py` の QtWidgets インポート行に追加する（`from PyQt6.QtWidgets import (..., QStyle,)`）

---

## Phase 2: Foundational（全ユーザーストーリーの前提）

**Purpose**: `_apply_btn_icon()` と `_update_play_btn_appearance()` を VideoPlayer に追加する。これらは US1〜US3 すべてが依存するため、先に完成させる必要がある。

**⚠️ CRITICAL**: この Phase が完了するまでユーザーストーリーの実装は開始しない

- [x] T002 VideoPlayer に `_apply_btn_icon(self, btn, sp)` メソッドを追加する（`looplayer/player.py`）— `style().standardIcon(sp)` を取得し `isNull()` でなければ `btn.setIcon()` を呼ぶ（FR-009）
- [x] T003 VideoPlayer に `_update_play_btn_appearance(self, playing: bool)` メソッドを追加する（`looplayer/player.py`）— playing=True なら SP_MediaPause + "一時停止"、False なら SP_MediaPlay + "再生" を設定する（FR-001）

**Checkpoint**: 2メソッドが player.py に存在し、インポートエラーがないことを確認

---

## Phase 3: User Story 1 — 主要再生ボタンのアイコン化（Priority: P1）🎯 MVP

**Goal**: 開く・再生/一時停止・停止ボタンにアイコンを設定し、play_btn の状態連動とメディア未ロード時 disabled を実現する

**Independent Test**: `pytest tests/integration/test_button_icons_p1.py -v` が全テストパスすること

### テスト（先に作成して FAIL を確認）

- [x] T004 [US1] `tests/integration/test_button_icons_p1.py` を新規作成する — 以下のテストを含む: open/play/stop の各ボタンに `icon().isNull() == False`、初期状態で `play_btn.isEnabled() == False`、`_update_play_btn_appearance(False)` 後に SP_MediaPlay アイコン、`_update_play_btn_appearance(True)` 後に SP_MediaPause アイコン、全3ボタンの `toolTip() != ""` — player fixture は `test_tooltips.py` と同じパターンを使用

### 実装

- [ ] T005 [US1] `looplayer/player.py` の `_build_ui()` 末尾に `open_btn`・`stop_btn` の `_apply_btn_icon()` 呼び出しを追加し、`open_btn.setToolTip(t("btn.open"))` と `stop_btn.setToolTip(t("btn.stop"))` を追加する
- [ ] T006 [US1] `looplayer/player.py` の `_build_ui()` 内 `play_btn` 作成直後に `self.play_btn.setEnabled(False)` を追加し、`_open_path()` のメディアロード直後（`media_player.play()` の次行）に `self.play_btn.setEnabled(True)` を追加する
- [ ] T007 [US1] `looplayer/player.py` の `play_btn.setText()` 全7箇所（717, 1067, 1070, 1074, 1903, 1919, 1962行付近）を `self._update_play_btn_appearance(True/False)` に置換する（research.md Decision 2 参照）

**Checkpoint**: `pytest tests/integration/test_button_icons_p1.py -v` が全テストパス

---

## Phase 4: User Story 2 — ABループボタンのアイコン化（Priority: P2）

**Goal**: A点設定・B点設定・ABループ切り替え・ABリセットの各ボタンにアイコンを設定し、ab_toggle_btn の checked/unchecked 状態変化を検証する

**Independent Test**: `pytest tests/integration/test_button_icons_p2.py -v` が全テストパスすること

### テスト（先に作成して FAIL を確認）

- [x] T008 [US2] `tests/integration/test_button_icons_p2.py` を新規作成する — 以下のテストを含む: set_a/set_b/ab_toggle/ab_reset の各ボタンに `icon().isNull() == False`、`ab_toggle_btn.isCheckable() == True`、初期状態で `ab_toggle_btn.isChecked() == False`、`toggle_ab_loop(True)` 後に `ab_toggle_btn.isChecked() == True`、`reset_ab()` 後に `ab_toggle_btn.isChecked() == False`、全4ボタンの `toolTip() != ""`

### 実装

- [x] T009 [US2] `looplayer/player.py` の `_build_ui()` 末尾に `set_a_btn`（SP_MediaSeekBackward）・`set_b_btn`（SP_MediaSeekForward）・`ab_toggle_btn`（SP_BrowserReload）・`ab_reset_btn`（SP_DialogResetButton）の `_apply_btn_icon()` 呼び出しを追加し、`ab_reset_btn.setToolTip(t("btn.ab_reset"))` を追加する

**Checkpoint**: `pytest tests/integration/test_button_icons_p2.py -v` が全テストパス

---

## Phase 5: User Story 3 — その他操作ボタンのアイコン化（Priority: P3）

**Goal**: ブックマーク保存・ズームモードボタンにアイコンを設定し、FR-009 フォールバックと FR-010 ツールチップを検証する

**Independent Test**: `pytest tests/integration/test_button_icons_p3.py -v` が全テストパスすること

### テスト（先に作成して FAIL を確認）

- [x] T010 [US3] `tests/integration/test_button_icons_p3.py` を新規作成する — 以下のテストを含む: save_bookmark/zoom の各ボタンに `icon().isNull() == False`、`_zoom_btn.isCheckable() == True`、`_apply_btn_icon()` を style モックで null アイコンを返すとき `btn.icon().isNull() == True`（FR-009フォールバック）、save_bookmark_btn の `toolTip() != ""`、全9ボタンの `toolTip() != ""`（FR-010網羅確認）

### 実装

- [x] T011 [US3] `looplayer/player.py` の `_build_ui()` 末尾に `save_bookmark_btn`（SP_FileDialogStart）・`_zoom_btn`（SP_FileDialogContentsView）の `_apply_btn_icon()` 呼び出しを追加し、`save_bookmark_btn.setToolTip(t("btn.save_bookmark"))` を追加する
- [x] T012 [US3] `looplayer/player.py` の `_build_ui()` 末尾に `_update_play_btn_appearance(playing=False)` を呼び出して play_btn の初期アイコンを設定する（play_btn のアイコン初期化は _update_play_btn_appearance に委譲する）

**Checkpoint**: `pytest tests/integration/test_button_icons_p3.py -v` が全テストパス

---

## Phase 6: Polish & 横断的確認

**Purpose**: 全ストーリー完了後の回帰テスト確認

- [x] T013 `pytest tests/ -v` を実行して既存テストを含む全テストがリグレッションなしでパスすることを確認する（SC-004）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能
- **Foundational (Phase 2)**: Phase 1 完了後 — T002, T003 は T001 に依存
- **US1 (Phase 3)**: Phase 2 完了後 — T004（テスト）は T002/T003 の存在前提で記述可能、T005〜T007（実装）は T004 の fail 確認後
- **US2 (Phase 4)**: Phase 2 完了後（US1 と独立）— T008→T009 の順
- **US3 (Phase 5)**: Phase 2 完了後（US1/US2 と独立）— T010→T011→T012 の順
- **Polish (Phase 6)**: 全 US 完了後

### User Story Dependencies

- **US1 (P1)**: Foundational 完了後に開始。他の US と独立。
- **US2 (P2)**: Foundational 完了後に開始。US1 と独立（すべて同一ファイルだが設定箇所は別）。
- **US3 (P3)**: Foundational 完了後に開始。US1/US2 と独立。

### Within Each User Story

1. テストファイルを作成して **FAIL** を確認してから実装を開始する（Constitution I）
2. 実装後にテストが PASS することを確認してから次のストーリーへ

### Parallel Opportunities

- T004/T008/T010（各 US のテストファイル）は別ファイルのため並列作成可能
- T005〜T012（player.py 変更）は同一ファイルのため順次実行
- T013（最終テスト）は全実装完了後

---

## Parallel Example: US1 と US2 のテスト並列作成

```bash
# US1 と US2 のテストファイルは別ファイルのため同時作成可能:
Task A: "T004: test_button_icons_p1.py を新規作成"
Task B: "T008: test_button_icons_p2.py を新規作成"
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1: Setup（T001）
2. Phase 2: Foundational（T002, T003）
3. Phase 3: US1（T004→T005→T006→T007）
4. **停止して検証**: `pytest tests/integration/test_button_icons_p1.py -v`
5. 主要再生ボタンのアイコン化が完了

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. US1 → 主要再生ボタン → テスト確認 → コミット
3. US2 → ABループボタン → テスト確認 → コミット
4. US3 → その他ボタン + ツールチップ → テスト確認 → コミット
5. Polish → 全テスト確認 → コミット

---

## Notes

- `_apply_btn_icon()` と `_update_play_btn_appearance()` は Foundational フェーズで作成し、US1〜3 の全テストが前提とする
- player.py の変更はすべて同一ファイルへの追記であり、各タスクは独立した Edit 操作として実行可能
- テストファイルの `player` fixture は `tests/integration/test_tooltips.py` と同じパターン（BookmarkStore + VideoPlayer + timer.stop()）を使用
- FR-009 のフォールバックテストは `unittest.mock.patch.object(player, 'style')` を使って `standardIcon()` が `QIcon()` を返すようモックする
