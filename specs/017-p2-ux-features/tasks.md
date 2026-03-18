# Tasks: P2 UX 機能群

**Input**: Design documents from `/specs/017-p2-ux-features/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ui-contracts.md ✓

**Organization**: Tasks are grouped by user story (US1=F-503, US2=F-401, US3=F-501, US4=F-105)
**TDD**: テストファースト（constitution 必須）— 各ストーリーはテスト RED → 実装 → GREEN の順

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup（共有基盤）

**Purpose**: 全ユーザーストーリーが依存する AppSettings 拡張と i18n キー追加

- [X] T001 Add `onboarding_shown: bool` property (getter/setter/save) to `looplayer/app_settings.py`
- [X] T002 Add all new i18n keys for F-401/F-501/F-105/F-503 (~30 keys) to `looplayer/i18n.py`

**Checkpoint**: `AppSettings.onboarding_shown` が動作し、i18n キーが `t()` で取得できること

---

## Phase 2: Foundational（ブロッキング前提）

**Purpose**: 既存テスト群が引き続きグリーンであることを確認する

- [X] T003 Run `pytest tests/ -v` to confirm baseline tests all pass before feature work begins

**Checkpoint**: 全既存テストがグリーン

---

## Phase 3: User Story 1 — フルスクリーン中コントロールオーバーレイ（F-503, Priority: P1）🎯 MVP

**Goal**: フルスクリーン中にマウスを画面下端10%に移動するとコントロールバーがオーバーレイ表示され、3秒で自動非表示になる

**Independent Test**: `tests/unit/test_fullscreen_overlay.py` の全テストがパスすること。フルスクリーン状態で `controls_panel` が適切に show/hide されること

### テスト（TDD: RED フェーズ）

- [X] T004 [US1] Write failing tests for fullscreen overlay methods in `tests/unit/test_fullscreen_overlay.py`:
  - `test_enter_overlay_mode_removes_panel_from_layout`
  - `test_exit_overlay_mode_reinserts_panel_into_layout`
  - `test_mouse_in_bottom_10_percent_shows_controls`
  - `test_mouse_outside_bottom_does_not_show_controls`
  - `test_overlay_timer_timeout_hides_controls`
  - `test_cursor_unset_when_overlay_visible`

### 実装（TDD: GREEN フェーズ）

- [X] T005 [US1] Add `_overlay_hide_timer: QTimer` initialization (singleShot=True, interval=3000, connected to `controls_panel.hide`) in `VideoPlayer.__init__` in `looplayer/player.py`
- [X] T006 [US1] Add `_enter_fullscreen_overlay_mode()` method: `removeWidget(controls_panel)` → `setGeometry(0, h-overlay_h, w, overlay_h)` → `raise_()` → `hide()` in `looplayer/player.py`
- [X] T007 [US1] Add `_exit_fullscreen_overlay_mode()` method: `insertWidget(1, controls_panel)` → `show()` → `_overlay_hide_timer.stop()` in `looplayer/player.py`
- [X] T008 [US1] Hook `_enter_fullscreen_overlay_mode` / `_exit_fullscreen_overlay_mode` into `changeEvent` (detect `isFullScreen()` transition) in `looplayer/player.py`
- [X] T009 [US1] Override `mouseMoveEvent` to detect bottom-10% zone: `if y > self.height() * 0.9` → `controls_panel.show()` + `unsetCursor()` + `_overlay_hide_timer.start(3000)` (fullscreen only) in `looplayer/player.py`
- [X] T010 [US1] Install EventFilter on `controls_panel` to reset `_overlay_hide_timer` on mouse move over the panel (fullscreen only) in `looplayer/player.py`
- [X] T011 [US1] Update `_hide_cursor()` to skip cursor hiding when `controls_panel.isVisible()` in fullscreen mode in `looplayer/player.py`

**Checkpoint**: `pytest tests/unit/test_fullscreen_overlay.py -v` 全テストグリーン。手動でフルスクリーン → 下端マウス → overlay表示/消去を確認

---

## Phase 4: User Story 2 — 設定画面（F-401, Priority: P2）

**Goal**: 「ファイル > 設定...」メニューから設定ダイアログを開き、全設定項目を一覧・変更できる

**Independent Test**: `tests/unit/test_preferences_dialog.py` の全テストがパスすること。OK/Cancel の挙動が正しいこと

### テスト（TDD: RED フェーズ）

- [X] T012 [US2] Write failing tests for PreferencesDialog in `tests/unit/test_preferences_dialog.py`:
  - `test_dialog_loads_current_settings_values`
  - `test_ok_saves_end_of_playback_action`
  - `test_ok_saves_sequential_play_mode`
  - `test_ok_saves_export_encode_mode`
  - `test_ok_saves_check_update_on_startup`
  - `test_cancel_does_not_modify_settings`
  - `test_preferences_menu_action_exists_in_file_menu`

### 実装（TDD: GREEN フェーズ）

- [X] T013 [P] [US2] Create `PreferencesDialog(QDialog)` with QTabWidget (再生/表示/アップデート 3タブ), OK+Cancel buttons, reads from and writes to `AppSettings` in `looplayer/widgets/preferences_dialog.py`
- [X] T014 [US2] Add "設定..." QAction to File menu in `VideoPlayer._build_menus()` in `looplayer/player.py` (depends on T013)

**Checkpoint**: `pytest tests/unit/test_preferences_dialog.py -v` 全テストグリーン。「ファイル > 設定...」でダイアログが開き OK/Cancel が機能することを手動確認

---

## Phase 5: User Story 3 — 初回起動オンボーディング（F-501, Priority: P3）

**Goal**: 初回起動時に4ステップのオーバーレイチュートリアルが表示され、完了/スキップ後に再表示されない

**Independent Test**: `tests/unit/test_onboarding_overlay.py` の全テストがパスすること。`onboarding_shown=False` で起動するとオーバーレイが表示されること

### テスト（TDD: RED フェーズ）

- [X] T015 [US3] Write failing tests for OnboardingOverlay in `tests/unit/test_onboarding_overlay.py`:
  - `test_overlay_shown_when_onboarding_not_completed`
  - `test_overlay_not_shown_when_already_completed`
  - `test_next_button_advances_step`
  - `test_progress_label_shows_step_number`
  - `test_finish_on_last_step_saves_flag_and_closes`
  - `test_skip_saves_flag_and_closes`
  - `test_close_without_finish_does_not_save_flag`
  - `test_help_menu_tutorial_action_exists`

### 実装（TDD: GREEN フェーズ）

- [X] T016 [P] [US3] Create `OnboardingOverlay(QWidget)` with 4-step content (i18n keys), step progress label (e.g. "1 / 4"), 「次へ」/「完了」/「スキップ」 buttons; Skip and Finish both write `settings.onboarding_shown=True` in `looplayer/widgets/onboarding_overlay.py`
- [X] T017 [US3] Add onboarding launch logic in `VideoPlayer.__init__` tail: check `_app_settings.onboarding_shown` → create and show `OnboardingOverlay` if False in `looplayer/player.py` (depends on T016)
- [X] T018 [US3] Override `VideoPlayer.resizeEvent` (or extend existing) to reposition `OnboardingOverlay` to center on resize in `looplayer/player.py`
- [X] T019 [US3] Add "ヘルプ > チュートリアルを表示" QAction that sets `onboarding_shown=False` and re-creates overlay in `VideoPlayer._build_menus()` in `looplayer/player.py`

**Checkpoint**: `pytest tests/unit/test_onboarding_overlay.py -v` 全テストグリーン。初回起動シミュレーション（`onboarding_shown=False`）でオーバーレイが4ステップ表示されることを手動確認

---

## Phase 6: User Story 4 — ABループ区間のズーム表示（F-105, Priority: P4）

**Goal**: ズームトグルボタンでAB区間がシークバー全幅に拡大表示され、フレーム単位の微調整が可能になる

**Independent Test**: `tests/unit/test_bookmark_slider_zoom.py` の全テストがパスすること。5秒AB区間でズームモード切り替えが機能すること

### テスト（TDD: RED フェーズ）

- [X] T020 [US4] Write failing tests for BookmarkSlider zoom in `tests/unit/test_bookmark_slider_zoom.py`:
  - `test_set_zoom_enables_zoom_mode`
  - `test_clear_zoom_disables_zoom_mode`
  - `test_zoom_enabled_property`
  - `test_ms_to_x_maps_zoom_start_to_groove_left`
  - `test_ms_to_x_maps_zoom_end_to_groove_right`
  - `test_x_to_ms_inverts_ms_to_x_in_zoom_mode`
  - `test_set_zoom_invalid_range_raises_value_error`

### 実装（TDD: GREEN フェーズ）

- [X] T021 [P] [US4] Add `_zoom_enabled: bool`, `_zoom_start_ms: int`, `_zoom_end_ms: int` fields to `BookmarkSlider.__init__` in `looplayer/widgets/bookmark_slider.py`
- [X] T022 [US4] Add `set_zoom(start_ms: int, end_ms: int)` and `clear_zoom()` methods and `zoom_enabled` property to `BookmarkSlider` in `looplayer/widgets/bookmark_slider.py` (depends on T021)
- [X] T023 [US4] Modify `_ms_to_x()` and `_x_to_ms()` to apply zoom coordinate transformation when `_zoom_enabled` is True in `looplayer/widgets/bookmark_slider.py` (depends on T022)
- [X] T024 [US4] Add `_zoom_btn: QPushButton` (toggle, default disabled) to controls panel in `VideoPlayer` in `looplayer/player.py`
- [X] T025 [US4] Add `_toggle_zoom_mode()` method: compute zoom range with ±10% padding → call `slider.set_zoom()` or `slider.clear_zoom()` in `looplayer/player.py`
- [X] T026 [US4] Enable/disable `_zoom_btn` when A/B points are set/cleared in `looplayer/player.py`
- [X] T027 [US4] Auto-update zoom range when AB points change while zoom is active in `looplayer/player.py`
- [X] T028 [US4] Reset zoom mode on video change (`_open_path` and `_reset_ab()`) in `looplayer/player.py`

**Checkpoint**: `pytest tests/unit/test_bookmark_slider_zoom.py -v` 全テストグリーン。短いAB区間でズームモード切り替えを手動確認

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 全ストーリー横断の品質確認

- [X] T029 [P] Run full test suite `pytest tests/ -v` and confirm all tests pass
- [X] T030 [P] PEP 8 check: `python -m pycodestyle looplayer/ --max-line-length=100 --exclude=__pycache__`
- [X] T031 Bump version to `1.7.0` in `looplayer/version.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 開始即可
- **Phase 2 (Foundational)**: Phase 1 完了後
- **US1 (Phase 3)**: Phase 1+2 完了後 — 他のUSに非依存
- **US2 (Phase 4)**: Phase 1+2 完了後 — 他のUSに非依存
- **US3 (Phase 5)**: Phase 1+2 完了後 — T001（`onboarding_shown`プロパティ）が必要
- **US4 (Phase 6)**: Phase 1+2 完了後 — 他のUSに完全非依存
- **Polish (Phase 7)**: 全US完了後

### User Story Dependencies

- **US1 (F-503)**: Phase 1 完了後に開始可能、他USとの依存なし
- **US2 (F-401)**: Phase 1 完了後に開始可能、他USとの依存なし
- **US3 (F-501)**: T001（`AppSettings.onboarding_shown`）完了が必要
- **US4 (F-105)**: Phase 1 完了後に開始可能、他USとの依存なし

### Within Each User Story

- テストを先に書いて失敗（RED）させてから実装（GREEN）
- 同一ファイルへの変更は順次実行
- `player.py` への変更タスクは US をまたいでも順次実行

### Parallel Opportunities

- T001 と T002 は異なるファイルなので並列実行可能
- T013（`preferences_dialog.py` 新規作成）と T004 以降の `player.py` 変更は並列可能（T014 は T013 に依存）
- T016（`onboarding_overlay.py` 新規作成）と `player.py` 変更は並列可能（T017 は T016 に依存）
- T021–T023（`bookmark_slider.py`）と T024–T028（`player.py`）はそれぞれ並列可能（T024 は T022 に依存しない）

---

## Parallel Example: User Story 1

```bash
# テスト（RED）を書いてから実装開始
Task T004: Write failing tests in tests/unit/test_fullscreen_overlay.py

# 実装は player.py 内で順次
Task T005: Add _overlay_hide_timer init in looplayer/player.py
Task T006: Add _enter_fullscreen_overlay_mode() in looplayer/player.py
Task T007: Add _exit_fullscreen_overlay_mode() in looplayer/player.py
Task T008: Hook into changeEvent in looplayer/player.py
Task T009: Override mouseMoveEvent in looplayer/player.py
Task T010: Install EventFilter on controls_panel in looplayer/player.py
Task T011: Update _hide_cursor() in looplayer/player.py
```

---

## Implementation Strategy

### MVP First (US1 のみ)

1. Phase 1: Setup (T001–T002)
2. Phase 2: Baseline check (T003)
3. Phase 3: US1 フルスクリーンオーバーレイ (T004–T011)
4. **STOP & VALIDATE**: `pytest tests/unit/test_fullscreen_overlay.py -v`
5. 手動でフルスクリーン動作確認

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (F-503) → P1 機能完成 → コミット
3. US2 (F-401) → 設定画面完成 → コミット
4. US3 (F-501) → オンボーディング完成 → コミット
5. US4 (F-105) → ズーム機能完成 → コミット
6. Polish → v1.7.0 リリース

---

## Notes

- `player.py` への変更が多い（US1〜US4 全てに影響）— 各フェーズ完了後に必ず `pytest tests/ -v` でリグレッションを確認
- フルスクリーンテスト（US1）は VLC ウィンドウが関係するため可能な限りモックを使用する
- `OnboardingOverlay` テストは `QWidget` の `close()` をモックせず、`settings.onboarding_shown` の値で検証する
- ズームモードは `_duration_ms == 0` のとき無効（`zoom_enabled` でガード）
