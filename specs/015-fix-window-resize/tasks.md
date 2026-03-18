# Tasks: ウィンドウサイズを動画サイズに合わせる機能のバグ修正

**Input**: Design documents from `/specs/015-fix-window-resize/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- 全タスクは Constitution I（テストファースト）に従い、テスト → FAIL 確認 → 実装の順で実行する

---

## Phase 1: Setup

**Purpose**: テストファイルの新規作成

- [ ] T001 テストファイルのスケルトンを新規作成する in tests/unit/test_window_resize.py（必要な import と空のテストクラス TestResizeToVideo / TestPollTimeout / TestDeadCode を定義する）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: US2・US3 が依存する `_size_poll_count` フィールドの初期化

**⚠️ CRITICAL**: このフェーズを完了してから US2・US3 の実装を開始すること

- [ ] T002 `__init__` に `self._size_poll_count: int = 0` を追加する in looplayer/player.py（US2 の実装が依存するカウンタ変数の初期化）

**Checkpoint**: カウンタ変数が定義された状態で US1 以降を並行または順次実装できる

---

## Phase 3: User Story 1 - アスペクト比修正（UIオフセット加算） (Priority: P1) 🎯 MVP

**Goal**: `_resize_to_video` がUIコントロール分の高さを加算してウィンドウをリサイズする

**Independent Test**: 任意の動画解像度 (w, h) を渡したとき、動画フレームの高さが h になることをユニットテストで確認できる

### テスト for User Story 1

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること**

- [ ] T003 [US1] `TestResizeToVideo.test_video_frame_height_matches_video` を書く — `_resize_to_video(1280, 720)` 後に `player.video_frame.height() == 720` となることを assert する in tests/unit/test_window_resize.py
- [ ] T004 [US1] `TestResizeToVideo.test_window_height_includes_ui_offset` を書く — ウィンドウ高さが `720 + ui_h_offset` になることを assert する in tests/unit/test_window_resize.py
- [ ] T005 [US1] `TestResizeToVideo.test_fullscreen_skips_resize` を書く — `isFullScreen()` が True のとき resize が呼ばれないことを assert する in tests/unit/test_window_resize.py
- [ ] T006 [US1] T003〜T005 のテストが FAIL することを `pytest tests/unit/test_window_resize.py -v` で確認する

### 実装 for User Story 1

- [ ] T007 [US1] `_resize_to_video` の高さ計算を修正する — `ui_h_offset = self.height() - self.video_frame.height()` を求め、`target_h = max(600, min(h + ui_h_offset, max_h))` に変更する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py::TestResizeToVideo -v` が全件 PASS すること

---

## Phase 4: User Story 2 - ポーリングタイムアウト追加 (Priority: P2)

**Goal**: `_poll_video_size` が 100 回（5秒）経過後にタイマーを自動停止する

**Independent Test**: `video_get_size` が常に (0, 0) を返す状態で 101 回ポーリングしたとき、タイマーが停止していることをユニットテストで確認できる

### テスト for User Story 2

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること**

- [ ] T008 [US2] `TestPollTimeout.test_timer_stops_after_100_polls` を書く — `video_get_size` を (0,0) に patch した状態で `_poll_video_size` を 100 回呼び、タイマーが停止していることを assert する in tests/unit/test_window_resize.py
- [ ] T009 [US2] `TestPollTimeout.test_timer_stops_immediately_on_valid_size` を書く — `video_get_size` が (1280, 720) を返す状態で `_poll_video_size` を 1 回呼び、タイマーが停止していることを assert する in tests/unit/test_window_resize.py
- [ ] T010 [US2] `TestPollTimeout.test_start_size_poll_resets_count` を書く — `_start_size_poll` 呼び出し後に `_size_poll_count == 0` であることを assert する in tests/unit/test_window_resize.py
- [ ] T011 [US2] T008〜T010 のテストが FAIL することを `pytest tests/unit/test_window_resize.py -v` で確認する

### 実装 for User Story 2

- [ ] T012 [US2] `_start_size_poll` でカウンタをリセットする — `self._size_poll_count = 0` を追加し、既存の `self._user_resized = False` を削除する in looplayer/player.py
- [ ] T013 [US2] `_poll_video_size` にタイムアウト処理を追加する — メソッド冒頭で `self._size_poll_count += 1` し、`>= 100` なら `self._size_poll_timer.stop()` して return する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py::TestPollTimeout -v` が全件 PASS すること

---

## Phase 5: User Story 3 - デッドコード削除 (Priority: P3)

**Goal**: `_user_resized` フラグと `_on_vlc_video_changed` メソッドが存在しない状態にする

**Independent Test**: `hasattr(player, '_user_resized')` および `hasattr(player, '_on_vlc_video_changed')` が False であることをユニットテストで確認できる

### テスト for User Story 3

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること（T012 完了後は _user_resized は既に消えているため T015 で _on_vlc_video_changed のみ確認する）**

- [ ] T014 [US3] `TestDeadCode.test_user_resized_flag_does_not_exist` を書く — `hasattr(player, '_user_resized')` が False であることを assert する in tests/unit/test_window_resize.py
- [ ] T015 [US3] `TestDeadCode.test_on_vlc_video_changed_does_not_exist` を書く — `hasattr(player, '_on_vlc_video_changed')` が False であることを assert する in tests/unit/test_window_resize.py
- [ ] T016 [US3] T015 のテストが FAIL することを `pytest tests/unit/test_window_resize.py::TestDeadCode -v` で確認する（T014 は T012 完了後 PASS しているはず）

### 実装 for User Story 3

- [ ] T017 [US3] `_on_vlc_video_changed` メソッドを削除する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py -v` が全件 PASS すること

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全体の動作確認と回帰テスト

- [ ] T018 全テストスイートを実行して回帰がないことを確認する — `pytest tests/ --ignore=tests/unit/test_updater.py --ignore=tests/integration/test_auto_update.py -v` を実行し 442 件以上が PASS すること
- [ ] T019 [P] quickstart.md のシナリオ 3（デッドコード不在）を目視で確認する in specs/015-fix-window-resize/quickstart.md
- [ ] T020 変更内容をコミットして 015-fix-window-resize ブランチを push する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 即開始可能
- **Foundational (Phase 2)**: Phase 1 完了後
- **US1 (Phase 3)**: Phase 2 完了後に開始可能
- **US2 (Phase 4)**: Phase 2 完了後に開始可能（US1 と独立だが同一ファイルのため順次推奨）
- **US3 (Phase 5)**: Phase 4 完了後（T012 で `_user_resized` 削除済みのため）
- **Polish (Phase 6)**: 全 US 完了後

### User Story Dependencies

- **US1**: Phase 2 後に開始可能。他 US に非依存
- **US2**: Phase 2 後に開始可能。T002 の `_size_poll_count` 初期化が前提
- **US3**: T012 完了後（`_user_resized` 削除が先行するため）

### Parallel Opportunities

- T003〜T005（US1 テスト）は同一ファイル内だが独立したメソッドのため並行記述可
- T008〜T010（US2 テスト）も同様
- T014・T015（US3 テスト）は並行記述可

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 完了: テストファイル作成
2. Phase 2 完了: カウンタ変数初期化
3. Phase 3 完了: アスペクト比修正（最重要バグ）
4. **STOP and VALIDATE**: `TestResizeToVideo` が全件 PASS することを確認
5. US2・US3 は後続で対応

### Incremental Delivery

1. Setup + Foundational → テスト基盤完成
2. US1 → アスペクト比修正（MVP）→ 動作確認
3. US2 → タイムアウト追加 → 確認
4. US3 → デッドコード削除 → 全件テスト確認

---

## Notes

- `player.py` はすべての US で共通ファイルのため、フェーズを順次実行すること
- `_user_resized` は T012（US2 実装）で削除されるため T014 は T012 完了後に自動 PASS する
- 最小ウィンドウサイズクランプ（幅 800px・高さ 600px）は変更しない
