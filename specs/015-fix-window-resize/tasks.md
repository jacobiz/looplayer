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

## Phase 2: User Story 1 - アスペクト比修正（UIオフセット加算） (Priority: P1) 🎯 MVP

**Goal**: `_resize_to_video` がUIコントロール分の高さを加算してウィンドウをリサイズする

**Independent Test**: 動画解像度 (w, h) を渡したとき、動画フレームの高さが h になることをユニットテストで確認できる

### テスト for User Story 1

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること**

- [ ] T002 [US1] `TestResizeToVideo.test_video_frame_height_matches_video` を書く — `_resize_to_video(1280, 720)` 後に `player.video_frame.height() == 720` となることを assert する in tests/unit/test_window_resize.py
- [ ] T003 [US1] `TestResizeToVideo.test_window_height_includes_ui_offset` を書く — ウィンドウ高さが `720 + ui_h_offset` になることを assert する in tests/unit/test_window_resize.py
- [ ] T004 [US1] `TestResizeToVideo.test_fullscreen_skips_resize` を書く — `isFullScreen()` が True のとき resize が呼ばれないことを assert する in tests/unit/test_window_resize.py
- [ ] T005 [US1] `TestResizeToVideo.test_no_video_skips_resize` を書く — `video_get_size` が (0, 0) を返す状態で `_poll_video_size` を呼んでも `_resize_to_video` が呼ばれないことを assert する（FR-008: 動画なしでクラッシュしない）in tests/unit/test_window_resize.py
- [ ] T006 [US1] `TestResizeToVideo.test_window_size_clamped_to_screen` を書く — 動画解像度がスクリーンサイズを超える場合（例: 9999×9999）にウィンドウが `avail.width()` / `avail.height()` 以下にクランプされることを assert する（FR-007）in tests/unit/test_window_resize.py
- [ ] T007 [US1] T002〜T006 のテストが FAIL することを `pytest tests/unit/test_window_resize.py::TestResizeToVideo -v` で確認する

### 実装 for User Story 1

- [ ] T008 [US1] `_resize_to_video` の高さ計算を修正する — `ui_h_offset = self.height() - self.video_frame.height()` を求め、`target_h = max(600, min(h + ui_h_offset, max_h))` に変更する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py::TestResizeToVideo -v` が全件 PASS すること

---

## Phase 3: User Story 2 - ポーリングタイムアウト追加 (Priority: P2)

**Goal**: `_poll_video_size` が 100 回（5秒）経過後にタイマーを自動停止する

**Independent Test**: `video_get_size` が常に (0, 0) を返す状態で 100 回ポーリングしたとき、タイマーが停止していることをユニットテストで確認できる

### セットアップ for User Story 2

- [ ] T009 [US2] `__init__` に `self._size_poll_count: int = 0` を追加する in looplayer/player.py（US2 の実装が依存するカウンタ変数の初期化）

### テスト for User Story 2

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること**

- [ ] T010 [US2] `TestPollTimeout.test_timer_stops_after_100_polls` を書く — `video_get_size` を (0,0) に patch した状態で `_poll_video_size` を 100 回呼び、タイマーが停止していることを assert する in tests/unit/test_window_resize.py
- [ ] T011 [US2] `TestPollTimeout.test_timer_stops_immediately_on_valid_size` を書く — `video_get_size` が (1280, 720) を返す状態で `_poll_video_size` を 1 回呼び、タイマーが停止していることを assert する in tests/unit/test_window_resize.py
- [ ] T012 [US2] `TestPollTimeout.test_start_size_poll_resets_count` を書く — `_start_size_poll` 呼び出し後に `_size_poll_count == 0` であることを assert する in tests/unit/test_window_resize.py
- [ ] T013 [US2] T010〜T012 のテストが FAIL することを `pytest tests/unit/test_window_resize.py::TestPollTimeout -v` で確認する

### 実装 for User Story 2

- [ ] T014 [US2] `_start_size_poll` を修正する — `self._size_poll_count = 0` のリセットを追加する（`_user_resized` の削除は US3 で行うため、ここでは削除しない）in looplayer/player.py
- [ ] T015 [US2] `_poll_video_size` にタイムアウト処理を追加する — メソッド冒頭で `self._size_poll_count += 1` し、`>= 100` なら `self._size_poll_timer.stop()` して return する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py::TestPollTimeout -v` が全件 PASS すること

---

## Phase 4: User Story 3 - デッドコード削除 (Priority: P3)

**Goal**: `_user_resized` フラグと `_on_vlc_video_changed` メソッドが存在しない状態にする

**Independent Test**: `_start_size_poll()` 呼び出し後に `_user_resized` が存在しないこと、および `_on_vlc_video_changed` が存在しないことをユニットテストで確認できる

### テスト for User Story 3

> **Constitution I 必須: テストを書き、FAIL することを確認してから実装すること**

- [ ] T016 [US3] `TestDeadCode.test_user_resized_flag_does_not_exist` を書く — `player._start_size_poll()` を呼び出した後に `hasattr(player, '_user_resized')` が False であることを assert する（呼び出し後に確認することで _start_size_poll に `_user_resized = False` が残っている場合に FAIL させる）in tests/unit/test_window_resize.py
- [ ] T017 [US3] `TestDeadCode.test_on_vlc_video_changed_does_not_exist` を書く — `hasattr(player, '_on_vlc_video_changed')` が False であることを assert する in tests/unit/test_window_resize.py
- [ ] T018 [US3] T016〜T017 のテストが FAIL することを `pytest tests/unit/test_window_resize.py::TestDeadCode -v` で確認する

### 実装 for User Story 3

- [ ] T019 [US3] デッドコードを削除する — `_start_size_poll` から `self._user_resized = False` を削除し、`_on_vlc_video_changed` メソッド全体を削除する in looplayer/player.py

**Checkpoint**: `pytest tests/unit/test_window_resize.py -v` が全件 PASS すること

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 全体の動作確認と回帰テスト

- [ ] T020 全テストスイートを実行して回帰がないことを確認する — `pytest tests/ --ignore=tests/unit/test_updater.py --ignore=tests/integration/test_auto_update.py -v` を実行し 442 件以上が PASS すること
- [ ] T021 変更内容をコミットして 015-fix-window-resize ブランチを push する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 即開始可能
- **US1 (Phase 2)**: Phase 1 完了後に開始可能
- **US2 (Phase 3)**: Phase 2 完了後に開始可能（同一ファイルのため順次）
- **US3 (Phase 4)**: Phase 3 完了後（T014 で _start_size_poll が修正済みのため、T016 の FAIL が正しく機能する）
- **Polish (Phase 5)**: 全 US 完了後

### User Story Dependencies

- **US1**: Phase 1 後に開始可能。他 US に非依存
- **US2**: Phase 2 完了後。T009（カウンタ初期化）が先行必須
- **US3**: Phase 3 完了後。T014 完了後に T016 の FAIL 確認が正しく機能する

### Parallel Opportunities

- T002〜T006（US1 テスト）は同一ファイル内だが独立したメソッドのため並行記述可
- T010〜T012（US2 テスト）も同様
- T016・T017（US3 テスト）は並行記述可

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 完了: テストファイル作成
2. Phase 2 完了: アスペクト比修正（最重要バグ）
3. **STOP and VALIDATE**: `TestResizeToVideo` が全件 PASS することを確認
4. US2・US3 は後続で対応

### Incremental Delivery

1. Setup → テスト基盤完成
2. US1 → アスペクト比修正（MVP）→ 動作確認
3. US2 → タイムアウト追加 → 確認
4. US3 → デッドコード削除 → 全件テスト確認

---

## Notes

- `player.py` はすべての US で共通ファイルのため、フェーズを順次実行すること
- T016 は `_start_size_poll()` 呼び出し後に `_user_resized` を確認する。これにより T014 完了前は FAIL、T019 完了後は PASS する（Constitution I 準拠）
- 最小ウィンドウサイズクランプ（幅 800px・高さ 600px）は変更しない
- FR-008 は T005 で、FR-007 は T006 で明示的にテストする
