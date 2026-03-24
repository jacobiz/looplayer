# Tasks: シークバークリックによる任意位置再生（ループ中）

**Input**: Design documents from `/specs/026-seekbar-click-seek/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Constitution I（テストファースト）により全ストーリーにテストタスクを含む。テストは実装前に作成し、失敗を確認してから実装に進むこと。

**Organization**: ユーザーストーリー単位でフェーズを構成。変更対象は `looplayer/player.py` のみ（4 箇所の局所変更）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可（異なるファイル・依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2）
- 各タスクに正確なファイルパスを記載

---

## Phase 1: Setup（ベースライン確認）

**Purpose**: 変更前に既存テストスイートが全パスすることを確認する

- [x] T001 既存テストスイートを実行し、全テストが PASS することを確認する（`pytest tests/ -v`）

---

## Phase 2: Foundational（全ストーリー共通の前提条件）

**Purpose**: B点クロッシング検出に必要な状態フィールドを追加する。US1・US2 の実装前に完了必須。

**⚠️ CRITICAL**: このフェーズが完了するまで US1・US2 の実装タスクは開始しないこと

- [x] T002 `VideoPlayer.__init__()` に `self._prev_timer_ms: int | None = None` フィールドを追加する（`_b_handled_cooldown` の近くに配置）in `looplayer/player.py`

**Checkpoint**: `_prev_timer_ms` フィールドが存在し、型アノテーション付きで初期化されていること

---

## Phase 3: User Story 1 - ループ中のシークバークリックで任意位置に移動 (Priority: P1) 🎯 MVP

**Goal**: ABループ有効中にシークバーをクリックしたとき、クリック位置から再生が開始される。B点以降をクリックしても即座に A点に飛ばない。一時停止中クリックでは一時停止維持。ズームモードでも正しく動作する。

**Independent Test**: ABループ設定済みの状態でシークバーの任意位置をクリックし、そのポイントから再生が開始されることを確認できる（通常・ズームモード両方、一時停止状態も含む）。

### Tests for User Story 1 ⚠️（先に書いて失敗を確認すること）

- [x] T003 [P] [US1] `test_click_past_b_does_not_jump_to_a` を書く: B点以降の位置を `_on_seek_ms()` でセット後に `_on_timer()` を呼び出しても `set_time(ab_point_a)` が呼ばれないことを検証 in `tests/unit/test_seekbar_click_loop.py`
- [x] T004 [P] [US1] `test_natural_b_crossing_triggers_loop` を書く: prev < B ≤ current の状態を直接セットして `_on_timer()` を呼び出したとき `set_time(ab_point_a)` が呼ばれることを検証 in `tests/unit/test_seekbar_click_loop.py`
- [x] T005 [P] [US1] `test_prev_timer_ms_reset_on_seek` を書く: `_on_seek_ms(ms)` 呼び出し後に `_prev_timer_ms == ms` になることを検証 in `tests/unit/test_seekbar_click_loop.py`
- [x] T006 [P] [US1] `test_click_within_loop_starts_from_click_position` を書く: `qtbot` でシークバークリックをシミュレートし、`media_player.set_time` がクリック位置の ms で呼ばれることを検証 in `tests/integration/test_seekbar_click_during_loop.py`
- [x] T007 [P] [US1] `test_pause_state_preserved_on_click` を書く: 一時停止中にシークバーをクリックしたとき `media_player.play()` が呼ばれないことを検証（US1 受け入れシナリオ3・FR-004 対応）in `tests/integration/test_seekbar_click_during_loop.py`
- [x] T008 [P] [US1] `test_zoom_mode_click_seeks_correctly` を書く: ズームモード有効中にシークバーをクリックしたとき `media_player.set_time` がズーム範囲内の正しい ms で呼ばれることを検証（FR-001 ズームモード要件対応）in `tests/integration/test_seekbar_click_during_loop.py`

### Implementation for User Story 1

- [x] T009 [US1] `_on_timer()` の B点判定を「絶対値比較」から「クロッシング検出（`_prev_timer_ms < ab_point_b <= current_ms`）」に変更し、タイマー末尾で `self._prev_timer_ms = current_ms` を更新する in `looplayer/player.py`（T003・T004 のテストが失敗していること確認後）※ early return がある場合はその前にも `_prev_timer_ms = current_ms` または `= None` を設定すること
- [x] T010 [US1] `_on_seek_ms()` 内に `self._prev_timer_ms = ms` を追加する（`media_player.set_time(ms)` の直後）in `looplayer/player.py`（T005 のテストが失敗していること確認後）

**Checkpoint**: T003〜T008 の全テストが PASS し、既存の ABループテスト（`tests/unit/test_ab_loop_logic.py`, `tests/integration/test_ab_loop.py`）も引き続き PASS すること

---

## Phase 4: User Story 2 - ループ範囲外クリック後のループ継続動作 (Priority: P2)

**Goal**: ループ範囲外にシークした後、B点に自然到達したとき正常に A点へ戻るループ動作が継続される。

**Independent Test**: A点=30秒・B点=60秒のループ有効状態で 10秒をクリック後に再生し、60秒到達で 30秒に戻ることを確認できる。

### Tests for User Story 2 ⚠️（先に書いて失敗を確認すること）

- [x] T011 [P] [US2] `test_seek_before_b_then_loop_triggers` を書く: `_on_seek_ms(10000)` 後に `_prev_timer_ms=59800`, `current_ms=60000` の状態でタイマーを呼び出したとき `set_time(ab_point_a)` が呼ばれることを検証 in `tests/unit/test_seekbar_click_loop.py`
- [x] T012 [P] [US2] `test_click_outside_loop_then_loop_resumes` を書く: ループ範囲外（A点前・10秒）をクリック後、`_prev_timer_ms=59800` → `current_ms=60000` のタイマー実行で `set_time(ab_point_a)` が呼ばれること（クリック位置確認＋その後のB点ループトリガーまで）を検証 in `tests/integration/test_seekbar_click_during_loop.py`

### Implementation for User Story 2

- [x] T013 [US2] `_resume_after_pause()` 内に `self._prev_timer_ms = self.ab_point_a` を追加する（A点シーク後のクロッシング基点をリセット）in `looplayer/player.py`（T011 のテストが失敗していること確認後）（T009 のクロッシング検出実装後に実施すること）

**Checkpoint**: T011・T012 のテストが PASS し、US1 のテストも引き続き PASS すること

---

## Phase 5: Polish（エッジケース・回帰）

**Purpose**: 仕様で定義されたエッジケースのテスト追加と全回帰確認

- [x] T014 [P] `test_loop_toggle_off_preserves_position` を書く: ループ有効中にシーク後、`toggle_ab_loop(False)` を呼んでも `set_time()` がループ関連で呼ばれないことを検証（FR-006 対応）in `tests/unit/test_seekbar_click_loop.py` ※ このテストが FAIL する場合は `toggle_ab_loop()` に `self._prev_timer_ms = None` リセットを追加する実装タスクを設けること
- [x] T015 [P] `test_a_only_no_loop_behavior` を書く: A点のみ設定（B点 = None）でシークバーをクリックしてもループ動作（A点ジャンプ）が発生しないことを検証（FR-005 の一部として ループ無効時の動作変化なしを明示確認）in `tests/unit/test_seekbar_click_loop.py`
- [x] T016 [P] `test_video_end_after_seek_past_b_follows_app_settings` を書く: B点以降にシーク後に動画末尾到達をシミュレートしたとき、ABループによる A点ジャンプではなく既存の再生終了動作（`app_settings` の `end_of_playback_action`）が適用されることを検証（Edge Case: 動画末尾処理 対応）in `tests/integration/test_seekbar_click_during_loop.py`
- [x] T017 [P] `test_drag_seek_not_affected_by_loop_change` を書く: ABループ有効中にドラッグシークを行っても crossing detection の変更によって動作が変わらないことを回帰確認（連続ドラッグ後は prev >= B となりクロッシング不成立 → A点ジャンプなし）in `tests/integration/test_seekbar_click_during_loop.py`
- [x] T018 全テストスイートを実行して回帰なし（0 failures）を確認する（`pytest tests/ -v`）※ FR-005「ループ無効時の既存動作維持」も暗黙的にカバーされることを確認すること
- [ ] T019 `quickstart.md` の手動検証手順（Step 3）に従って実機動作を確認する

---

## Dependencies & Execution Order

### フェーズ依存関係

- **Phase 1（Setup）**: 依存なし・即開始可能
- **Phase 2（Foundational）**: Phase 1 完了後 → **US1・US2 実装をブロック**
- **Phase 3（US1）**: Phase 2 完了後に開始。テスト（T003〜T008）→ 実装（T009〜T010）の順を厳守
- **Phase 4（US2）**: Phase 2 完了後に開始。T013 は T009（クロッシング検出）の完了後に実施すること
- **Phase 5（Polish）**: Phase 3・Phase 4 の完了後

### ユーザーストーリー依存関係

- **US1（P1）**: Phase 2 完了後に開始可能・US2 との直接依存なし
- **US2（P2）**: Phase 2 完了後に開始可能。T013 は T009（`_on_timer()` のクロッシング検出）完了後に実施すること

### 各ストーリー内の並列実行

- テストタスク（T003〜T008, T011〜T012）は [P] マーク付き → 同ファイル内追記は論理並列
  - `tests/unit/test_seekbar_click_loop.py` への追記（T003〜T005, T011）は順次
  - `tests/integration/test_seekbar_click_during_loop.py` への追記（T006, T007, T008, T012）は順次
- 実装タスク（T009 → T010）は順次（T009 の変更が T010 の前提）

### 並列実行例: Phase 3（US1）

```bash
# unit と integration のテストファイルは並列で書ける
# （ファイルが分かれているため）
[ファイルA] tests/unit/test_seekbar_click_loop.py:
  T003: test_click_past_b_does_not_jump_to_a
  T004: test_natural_b_crossing_triggers_loop
  T005: test_prev_timer_ms_reset_on_seek

[ファイルB] tests/integration/test_seekbar_click_during_loop.py:
  T006: test_click_within_loop_starts_from_click_position
  T007: test_pause_state_preserved_on_click
  T008: test_zoom_mode_click_seeks_correctly

# テスト失敗を確認 → 実装へ
T009: _on_timer() クロッシング検出
T010: _on_seek_ms() リセット追加（T009 後）
```

---

## Implementation Strategy

### MVP First（User Story 1 のみ）

1. Phase 1: ベースライン確認（T001）
2. Phase 2: `_prev_timer_ms` フィールド追加（T002）
3. Phase 3 テスト: T003〜T008 を書いて失敗確認
4. Phase 3 実装: T009〜T010 を実装してテストをパス
5. **STOP & VALIDATE**: 全テスト PASS + 手動動作確認
6. 十分であればここでコミット

### Incremental Delivery

1. Setup + Foundational → 基盤準備完了
2. US1 実装 → テスト PASS → コミット（MVP）
3. US2 実装 → テスト PASS → コミット
4. Polish（エッジケース・回帰）→ コミット

---

## Notes

- [P] タスク = 異なるファイル or 論理的に独立したテストケース（並列作業可）
- [Story] ラベルはユーザーストーリーとのトレーサビリティ
- **Constitution I 厳守**: テストが「失敗」してから実装を始めること
- 変更対象ファイルは `looplayer/player.py` のみ（`bookmark_slider.py` は変更不要）
- 各フェーズのチェックポイントで `pytest tests/ -v` を実行して回帰確認
- コミットはチェックポイント単位で行う
- T014（FR-006）が FAIL した場合は `toggle_ab_loop()` への `_prev_timer_ms = None` リセット追加を検討すること
- T009 の `_on_timer()` 変更時：early return パスがある場合（動画未読込・停止中など）、その前でも `_prev_timer_ms` を更新すること
