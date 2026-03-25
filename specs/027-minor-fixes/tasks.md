# Tasks: 細かな修正（バージョン更新キャッシュ短縮・B点アイコン改善）

**Input**: Design documents from `/specs/027-minor-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, quickstart.md ✅

**Tests**: Constitution I（テストファースト）により全ストーリーにテストタスクを含む。テストは実装前に作成し、失敗を確認してから実装に進むこと。

**Organization**: ユーザーストーリー単位でフェーズを構成。US1（updater.py 1行変更）と US2（player.py 1行変更）は完全に独立しており並列実行可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可（異なるファイル・依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2）
- 各タスクに正確なファイルパスを記載

---

## Phase 1: Setup（ベースライン確認）

**Purpose**: 変更前に既存テストスイートが全パスすることを確認する

- [x] T001 既存の updater テストと button_icons テストが PASS することを確認する（`pytest tests/unit/test_updater.py tests/integration/test_button_icons_p2.py -v`）

---

## Phase 2: Foundational（共通前提条件）

**Purpose**: なし。US1・US2 は独立しており Foundational フェーズ不要。Phase 1 完了後に直接 US1・US2 を並列開始できる。

*このフィーチャーは 2 ファイルの局所変更のみのため Phase 2 はスキップ。*

---

## Phase 3: User Story 1 - バージョン更新通知をより早く受け取る (Priority: P1) 🎯 MVP

**Goal**: `_CHECK_INTERVAL_SECS` を 86400 → 21600 に変更し、更新確認のキャッシュ期間を 24h から 6h に短縮する。

**Independent Test**: アプリ起動時に前回チェックから 5h の場合はスキップし、7h の場合は GitHub API チェックが実行されることをテストで確認できる。

### Tests for User Story 1 ⚠️（先に書いて失敗を確認すること）

- [x] T002 [P] [US1] `test_check_interval_is_6h` を書く: `from looplayer.updater import _CHECK_INTERVAL_SECS` でインポートし `_CHECK_INTERVAL_SECS == 21600` を assert する in `tests/unit/test_updater.py`
- [x] T003 [P] [US1] `test_update_checker_skips_within_6h` を書く: `last_ts=time.time() - 5*3600`（5時間前）の settings モックで `UpdateChecker` を起動し `urlopen` が呼ばれないことを検証 in `tests/unit/test_updater.py`
- [x] T004 [P] [US1] `test_update_checker_runs_after_6h` を書く: `last_ts=time.time() - 7*3600`（7時間前）の settings モックで `UpdateChecker` を起動し `urlopen` が 1 回呼ばれることを検証（API レスポンスは既存のモックパターンを流用） in `tests/unit/test_updater.py`

### Implementation for User Story 1

- [x] T005 [US1] `_CHECK_INTERVAL_SECS` を `86400` から `21600` に変更し、同行コメントを `# 6時間キャッシュ` に、`run()` 内コメントを `# 6h キャッシュ:` に更新する in `looplayer/updater.py`（T002〜T004 のテストが FAIL していること確認後）
- [x] T006 [US1] `test_update_checker_skips_when_checked_recently` の docstring を「24h 未満」→「6h 未満」に更新する in `tests/unit/test_updater.py`（テストロジック自体は変更不要 — `time.time()` を `last_ts` に使用しているため境界変更に依存しない）

**Checkpoint**: T002〜T004 の全テストが PASS し、既存の updater テストも引き続き PASS すること（`pytest tests/unit/test_updater.py -v`）

---

## Phase 4: User Story 2 - B点セットボタンのアイコンをA点と対になる形に統一する (Priority: P1)

**Goal**: `set_b_btn` に適用する `QStyle.StandardPixmap` を `SP_FileDialogEnd` → `SP_MediaSkipForward` に変更し、A点ボタン（`SP_MediaSkipBackward` = ⏮）と左右対称のペア（⏭）にする。

**Independent Test**: アプリ起動後に `set_b_btn.icon().cacheKey()` が `style().standardIcon(SP_MediaSkipForward).cacheKey()` と一致することをテストで確認できる。

### Tests for User Story 2 ⚠️（先に書いて失敗を確認すること）

- [x] T007 [P] [US2] `test_set_b_btn_icon_matches_sp_media_skip_forward` を書く: `player.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward).cacheKey()` と `player.set_b_btn.icon().cacheKey()` が等しいことを assert する in `tests/integration/test_button_icons_p2.py`
- [x] T008 [P] [US2] `test_set_a_and_b_icons_are_symmetric_pair` を書く: A点ボタンのアイコン cacheKey が `SP_MediaSkipBackward` と一致し、B点ボタンのアイコン cacheKey が `SP_MediaSkipForward` と一致することを同時に検証する in `tests/integration/test_button_icons_p2.py`

### Implementation for User Story 2

- [x] T009 [US2] `_apply_btn_icon(self.set_b_btn, ...)` の引数を `QStyle.StandardPixmap.SP_FileDialogEnd` → `QStyle.StandardPixmap.SP_MediaSkipForward` に変更する in `looplayer/player.py`（T007〜T008 のテストが FAIL していること確認後）

**Checkpoint**: T007〜T008 の全テストが PASS し、既存の `test_set_b_btn_has_icon`・`test_set_b_btn_has_tooltip` も引き続き PASS すること（`pytest tests/integration/test_button_icons_p2.py -v`）

---

## Phase 5: Polish（回帰確認・手動検証）

**Purpose**: 全回帰確認とアイコン目視確認

- [x] T010 `pytest tests/unit/test_updater.py tests/integration/test_button_icons_p2.py tests/integration/test_auto_update.py -v` を実行して全テスト PASS を確認する（FR-003: `check_update_on_startup` 無効時の動作維持も含む回帰確認）
- [x] T011 [P] `pytest tests/unit/test_ab_loop_logic.py tests/integration/test_ab_loop.py -v` を実行して ABループ回帰がないことを確認する
- [ ] T012 `quickstart.md` の Step 2（US1 境界確認）と Step 3（US2 アイコン目視確認）に従って実機動作を確認する

---

## Dependencies & Execution Order

### フェーズ依存関係

- **Phase 1（Setup）**: 依存なし・即開始可能
- **Phase 3（US1）**: Phase 1 完了後。テスト（T002〜T004）→ 実装（T005〜T006）の順を厳守
- **Phase 4（US2）**: Phase 1 完了後。US1 との直接依存なし（異なるファイル）
- **Phase 5（Polish）**: Phase 3・Phase 4 の完了後

### ユーザーストーリー依存関係

- **US1 と US2 は完全独立**: 異なるファイルへの変更のため並列実行可能

### 並列実行例: Phase 3 と Phase 4

```bash
# Phase 1 完了後、US1・US2 を並列で開始できる

[ファイルA] tests/unit/test_updater.py への追記:
  T002: test_check_interval_is_6h
  T003: test_update_checker_skips_within_6h
  T004: test_update_checker_runs_after_6h

[ファイルB] tests/integration/test_button_icons_p2.py への追記:
  T007: test_set_b_btn_icon_matches_sp_media_skip_forward
  T008: test_set_a_and_b_icons_are_symmetric_pair

# テスト失敗を確認後、実装へ（これも並列可能）

[ファイルA] looplayer/updater.py:
  T005: _CHECK_INTERVAL_SECS = 21600

[ファイルB] looplayer/player.py:
  T009: SP_FileDialogEnd → SP_MediaSkipForward
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1: ベースライン確認（T001）
2. Phase 3 テスト: T002〜T004 を書いて失敗確認
3. Phase 3 実装: T005〜T006 で実装してテスト PASS
4. **STOP & VALIDATE**: updater テスト全 PASS 確認
5. 十分であればここでコミット

### Incremental Delivery

1. Setup → US1（キャッシュ短縮）→ コミット
2. US2（B点アイコン）→ コミット
3. Polish（回帰・手動確認）→ コミット

---

## Notes

- [P] タスク = 異なるファイル or 論理的に独立したテストケース（並列作業可）
- **Constitution I 厳守**: テストが「失敗」してから実装を始めること
- 変更量は極めて小さい（合計 2〜3 行の実装変更）が、テストファーストの手順は省略しない
- `test_update_checker_skips_within_6h` と `test_update_checker_skips_when_checked_recently` は異なるテスト：前者は 5h 境界（新規）、後者は即時（既存）
- B点アイコンの cacheKey 比較は環境・テーマに依存することがある。もし cacheKey が 0 を返す場合（アイコン未ロード等）は `isNull()` の否定と pixmap のサイズ比較に切り替えること
- `test_button_icons_p2.py` の player fixture は `scope="module"` のため、アイコン変更（T009）後に既存セッションのキャッシュが残る場合がある。テスト実行時は `pytest --cache-clear tests/integration/test_button_icons_p2.py -v` または新規シェルセッションで実行すること
- FR-004（`check_update_on_startup` 無効時の既存動作維持）は T010 の `test_auto_update.py` 回帰確認でカバーされる
