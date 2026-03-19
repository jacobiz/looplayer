# Tasks: 再生速度拡張・ミラー表示（F-101 / F-203）

**Input**: Design documents from `/specs/018-speed-mirror/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ui-contracts.md ✅

**Tests**: 憲法「I. テストファースト」に従い、全 US にテストタスクを含む（RED → GREEN）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup（なし）

このフィーチャーは既存プロジェクト構造に対する最小追加。新規プロジェクト初期化・依存追加は不要。

---

## Phase 2: Foundational（ブロッキング前提条件）

**Purpose**: 全 US が共有する基盤変更。このフェーズ完了まで US 実装は開始しない。
TDD 順: テスト（RED）→ 実装（GREEN）の順を厳守する。

**⚠️ CRITICAL**: 以下が完了するまで US フェーズへ進んではならない。

- [X] T001 [P] `looplayer/i18n.py` に新規 i18n キーを追加する: `menu.view.mirror_display`（日: 左右反転 / 英: Mirror Display）、`status.speed_fine_up`（日: 速度 +0.05x / 英: Speed +0.05x）、`status.speed_fine_down`（日: 速度 -0.05x / 英: Speed -0.05x）
- [X] T002 [P] `tests/unit/test_mirror_display.py` を新規作成し、`AppSettings.mirror_display` プロパティの基本テストを記述して RED を確認する:
  - `test_mirror_display_default_is_false`: `AppSettings()` の `mirror_display` が `False`
  - `test_mirror_display_setter_saves`: setter で `True` にすると `settings.json` に反映される
- [X] T003 `looplayer/app_settings.py` に `mirror_display` getter/setter プロパティを追加して T002 を GREEN にする（getter: `bool(self._data.get("mirror_display", False))`, setter: `self._data["mirror_display"] = value; self.save()`）
- [X] T004 `tests/unit/test_speed_menu_expansion.py` を新規作成し、`_PLAYBACK_RATES` の基本テストを記述して RED を確認する:
  - `test_playback_rates_has_10_stages`: `_PLAYBACK_RATES` が 10 要素であること
  - `test_playback_rates_includes_0_25`: 0.25 が含まれること
  - `test_playback_rates_includes_3_0`: 3.0 が含まれること
  - `test_playback_rates_includes_1_75_and_2_5`: 新規追加の 1.75, 2.5 が含まれること
- [X] T005 `looplayer/player.py` の `_PLAYBACK_RATES` 定数を 10 段階に更新して T004 を GREEN にする: `[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]`（既存 6 段階から置き換え）

**Checkpoint**: `pytest tests/unit/test_mirror_display.py tests/unit/test_speed_menu_expansion.py -v` が全通過。Foundational 完了。

---

## Phase 3: User Story 1 — 速度連続微調整ショートカット（Priority: P1）🎯 MVP

**Goal**: `Shift+]` / `Shift+[` で再生速度を 0.05x 刻みで上下できる。0.25x〜3.0x の範囲でクリップし、上下限到達時はステータスバーにメッセージを表示する。

**Independent Test**: `Shift+]` を押して速度が 0.05x 増加すること・3.0x で頭打ちになること・0.25x で下限になることを手動または自動テストで単独確認できる。

### テスト（先に作成して RED を確認）

- [X] T006 [US1] `tests/unit/test_speed_fine_adjustment.py` を新規作成し、以下の失敗テストを記述する:
  - `test_speed_fine_up_increments_by_0_05`: 1.0x → 1.05x
  - `test_speed_fine_up_at_max_stays_at_3_0`: 3.0x → 3.0x（変化なし）
  - `test_speed_fine_down_decrements_by_0_05`: 1.0x → 0.95x
  - `test_speed_fine_down_at_min_stays_at_0_25`: 0.25x → 0.25x（変化なし）
  - `test_speed_fine_up_clips_to_max`: 2.98x → 3.0x（丸め + クリップ）
  - `test_speed_fine_down_clips_to_min`: 0.27x → 0.25x（丸め + クリップ）
  - `test_speed_fine_up_float_rounding`: 0.28x + 0.05 = 0.33x（`round(..., 2)` 適用）

### 実装

- [X] T007 [US1] `looplayer/player.py` に `_speed_fine_up()` メソッドを実装する: `new_rate = min(3.0, round(self._playback_rate + 0.05, 2))` → `_set_playback_rate(new_rate)`; 上限到達時は `t("status.max_speed")` を 2000ms ステータスバー表示
- [X] T008 [US1] `looplayer/player.py` に `_speed_fine_down()` メソッドを実装する: `new_rate = max(0.25, round(self._playback_rate - 0.05, 2))` → `_set_playback_rate(new_rate)`; 下限到達時は `t("status.min_speed")` を 2000ms ステータスバー表示
- [X] T009 [US1] `looplayer/player.py` の `_build_shortcuts()` に `QShortcut(QKeySequence("Shift+]"), self)` と `QShortcut(QKeySequence("Shift+["), self)` を追加し、それぞれ `_speed_fine_up` / `_speed_fine_down` に接続する

**Checkpoint**: `pytest tests/unit/test_speed_fine_adjustment.py -v` が全通過。Shift+[/] で速度が 0.05x 刻みで変化することを確認できる。

---

## Phase 4: User Story 2 — 速度段階メニュー 10 段階（Priority: P2）

**Goal**: 速度メニューに 0.25x / 0.5x / 0.75x / 1.0x / 1.25x / 1.5x / 1.75x / 2.0x / 2.5x / 3.0x の 10 段階が表示される。T005 の `_PLAYBACK_RATES` 変更により `_build_menus()` ループが自動対応するため、追加実装は不要。

**Independent Test**: 速度メニューを開き 10 段階の選択肢が表示されること・`[`/`]` キーが 10 段階を循環することを確認できる。

### テスト（先に作成して RED を確認）

- [X] T010 [US2] `tests/unit/test_speed_menu_expansion.py` に以下のテストを追記し、RED を確認する:
  - `test_speed_menu_actions_count_equals_playback_rates`: メニューアクション数が `len(_PLAYBACK_RATES)` と一致すること
  - `test_speed_up_cycles_through_all_10_stages`: `_speed_up()` が 0.25x から 3.0x まで 10 段階すべてを昇順に循環すること（FR-106）
  - `test_speed_down_cycles_through_all_10_stages`: `_speed_down()` が 3.0x から 0.25x まで 10 段階すべてを降順に循環すること（FR-106）

### 実装（検証のみ）

- [X] T011 [US2] `looplayer/player.py` の `_build_menus()` 速度メニュー生成ループが `_PLAYBACK_RATES` を動的に参照していることを Read で確認し、変更不要であることを検証して T010 を GREEN にする（T005 の変更のみで自動対応）

**Checkpoint**: `pytest tests/unit/test_speed_menu_expansion.py -v` が全通過。

---

## Phase 5: User Story 3 — ミラー表示トグル（Priority: P2）

**Goal**: 「表示 > 左右反転」メニューで映像を左右反転できる。状態は `settings.json` に保存され、動画切り替え・アプリ再起動後も維持される。

**Independent Test**: ミラートグル ON/OFF で映像が反転/復元されること・別動画を開いてもミラー状態が継続すること・`settings.json` に `mirror_display` が保存されることを独立確認できる。

### テスト（先に作成して RED を確認）

- [X] T012 [US3] `tests/unit/test_mirror_display.py` に以下のテストを追記し、RED を確認する:
  - `test_mirror_display_persists_across_instances`: 保存後に別インスタンスで `True` を読み込める
  - `test_toggle_mirror_updates_setting`: `_toggle_mirror_display()` 呼び出しで `mirror_display` が反転する
  - `test_open_path_adds_hflip_option_when_mirror_on`: `mirror_display=True` 時に `media.add_option` が `':video-filter=transform'` と `':transform-type=hflip'` で呼ばれる
  - `test_open_path_no_hflip_option_when_mirror_off`: `mirror_display=False` 時に hflip オプションが付加されない
  - `test_toggle_mirror_without_video_changes_setting_only`: `_current_video_path` が `None` の状態でトグルしても `_open_path` が呼ばれず設定のみ変更される（エッジケース）

### 実装

- [X] T013 [US3] `looplayer/player.py` の `_build_menus()` 表示メニューに `mirror_action`（`setCheckable(True)`, `setChecked(self._app_settings.mirror_display)`, `t("menu.view.mirror_display")`）を追加し、`triggered` を `_toggle_mirror_display` に接続する
- [X] T014 [US3] `looplayer/player.py` に `_toggle_mirror_display()` メソッドを実装する: `new_val = not self._app_settings.mirror_display` → `self._app_settings.mirror_display = new_val` → `mirror_action.setChecked(new_val)` → `self._current_video_path` が `None` でなければ `pos = self.media_player.get_time()` を保存してから `_open_path(self._current_video_path)` を呼び出し、再生開始後に `self.media_player.set_time(pos)` で位置を復元する
- [X] T015 [US3] `looplayer/player.py` の `_open_path()` でメディア生成直後に mirror 分岐を追加する: `if self._app_settings.mirror_display: media.add_option(':video-filter=transform'); media.add_option(':transform-type=hflip')`

**Checkpoint**: `pytest tests/unit/test_mirror_display.py -v` が全通過。映像の左右反転 ON/OFF・設定永続化を確認できる。

---

## Phase 6: Polish & 横断的懸念事項

**Purpose**: 全 US の最終確認とバージョン更新

- [X] T016 `pytest tests/ -v` を実行して全テストが通過することを確認し、失敗があれば修正する
- [X] T017 `looplayer/version.py` のバージョンを `1.8.0` に更新する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: 依存なし — 即座に開始可能
  - T001（i18n）と T002（AppSettings テスト）は並列実行可（別ファイル）
  - T003 は T002 の RED 確認後（TDD 順序）
  - T004 は T001/T003 と並列可（別ファイル）
  - T005 は T004 の RED 確認後（TDD 順序）
- **US1 (Phase 3)**: T005 完了後に開始。T006（テスト）→ T007/T008/T009（実装）の順
- **US2 (Phase 4)**: T005 完了後に開始。US1 と並列実行可能
- **US3 (Phase 5)**: T003（AppSettings）完了後に開始。T012（テスト）→ T013/T014/T015（実装）の順
- **Polish (Phase 6)**: 全 US 完了後

### User Story Dependencies

- **US1 (P1)**: T005 依存（`_PLAYBACK_RATES` 拡張により速度範囲 0.25x〜3.0x が有効）
- **US2 (P2)**: T005 依存（自動対応のため追加実装なし）
- **US3 (P2)**: T001（i18n）+ T003（AppSettings）依存

### Parallel Opportunities

- T001（i18n）と T002（AppSettings テスト）は別ファイルのため並列実行可能（Phase 2 内）
- T004（_PLAYBACK_RATES テスト）は T001/T002/T003 と並列実行可能（別ファイル）
- US2 の T010/T011 は US1 の T006–T009 と並列実行可能（異なるファイル）
- US3 の T012–T015 は US1/US2 完了後に独立実行可能

---

## Parallel Example: Phase 2 Foundational 並列実行

```bash
# T001 と T002 は別ファイルで並列可
Task T001: i18n キー追加（looplayer/i18n.py）
Task T002: AppSettings テスト作成（tests/unit/test_mirror_display.py）
Task T004: _PLAYBACK_RATES テスト作成（tests/unit/test_speed_menu_expansion.py）

# T003 は T002 完了後（TDD: RED → GREEN）
Task T003: AppSettings.mirror_display 実装（looplayer/app_settings.py）
# T005 は T004 完了後（TDD: RED → GREEN）
Task T005: _PLAYBACK_RATES 更新（looplayer/player.py）
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 2: T001–T005 を完了（Foundational）
2. Phase 3: T006（テスト RED）→ T007, T008, T009（GREEN）
3. **STOP & VALIDATE**: `pytest tests/unit/test_speed_fine_adjustment.py -v` 全通過
4. デモ: `Shift+]` / `Shift+[` で 0.05x 刻み速度調整が動作する

### Incremental Delivery

1. Foundational → 基盤完了（T001–T005）
2. US1 追加 → `Shift+]`/`Shift+[` 微調整動作（T006–T009）→ MVP
3. US2 追加 → 10 段階メニュー確認（T010–T011）
4. US3 追加 → ミラー表示動作（T012–T015）
5. Polish → 全テスト通過 + バージョン更新（T016–T017）

---

## Notes

- [P] tasks = 別ファイル、依存なし — 並列実行可
- 憲法 I. テストファーストに従い、Phase 2 基盤変更にも事前テストタスクを配置（T002→T003、T004→T005）
- テストが RED（失敗）であることを確認してから実装（GREEN）に進むこと
- `round(..., 2)` を必ず使用すること（浮動小数点誤差防止）
- VLC ミラー実装: `media.add_option(':video-filter=transform')` + `':transform-type=hflip'` をペアで使用
- ミラートグル時の再生位置保持: `self.media_player.get_time()` で取得し `set_time()` で復元（`_current_video_path` で動画パスを参照）
- 各チェックポイントで `pytest` を実行してから次フェーズへ進む
