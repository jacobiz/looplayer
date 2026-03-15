# Tasks: AB Loop Bookmarks & Sequential Playback

**Input**: Design documents from `/specs/002-ab-loop-bookmarks/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Tests**: 憲法 I（テストファースト）に基づき、各実装タスクの前にテストタスクを含める。

**Organization**: タスクはユーザーストーリー単位でグループ化し、各ストーリーを独立して実装・テスト可能とする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1/US2/US3）
- 各タスクには具体的なファイルパスを含める

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 新規ファイルの骨格を作成し、テスト環境が動作することを確認する

- [x] T001 `bookmark_store.py` を空の骨格（インポート・空クラス）として作成 — `bookmark_store.py`
- [x] T002 [P] ユニットテストファイルの骨格を作成 — `tests/unit/test_bookmark_store.py`
- [x] T003 [P] 連続再生ユニットテストファイルの骨格を作成 — `tests/unit/test_sequential_play.py`
- [x] T004 [P] 統合テストファイルの骨格を作成 — `tests/integration/test_bookmark_integration.py`

**Checkpoint**: `pytest tests/ -v` が収集エラーなく完走すること

---

## Phase 2: Foundational（共通データモデル）

**Purpose**: 全ユーザーストーリーが依存する `LoopBookmark` データクラスと `BookmarkStore` の基本操作（インメモリ）を実装する

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの実装を開始しない

> **テストを先に書き、RED（失敗）を確認してから実装すること**

- [x] T005 `LoopBookmark` の単体テストを作成（バリデーション: point_a_ms < point_b_ms、デフォルト名、repeat_count >= 1） — `tests/unit/test_bookmark_store.py`
- [x] T006 `LoopBookmark` dataclass をバリデーション付きで実装（uuid, name, point_a_ms, point_b_ms, repeat_count=1, order=0） — `bookmark_store.py`（T005 RED確認後）
- [x] T007 `BookmarkStore` のインメモリ操作テストを作成（add/delete/get_bookmarks） — `tests/unit/test_bookmark_store.py`
- [x] T008 `BookmarkStore` インメモリ操作（add/delete/get_bookmarks）を実装 — `bookmark_store.py`（T007 RED確認後）

**Checkpoint**: `pytest tests/unit/test_bookmark_store.py -v` が全件 GREEN であること

---

## Phase 3: User Story 1 - ABループポイントの登録と即時切り替え (Priority: P1) 🎯 MVP

**Goal**: ユーザーがA・B点設定済み状態で「ブックマーク保存」ボタンを押してブックマークを登録し、一覧から選択して即座にループ区間を切り替えられる

**Independent Test**: ブックマーク保存→一覧表示→別ブックマーク選択→ループ切り替え→削除の一連操作が動作すること（`tests/integration/test_bookmark_integration.py`）

> **テストを先に書き、RED（失敗）を確認してから実装すること**

### US1 テスト

- [x] T009 [US1] US1 統合テストを作成（ブックマーク保存・一覧表示・切り替え・削除フロー） — `tests/integration/test_bookmark_integration.py`

### US1 実装

- [x] T010 [P] [US1] `BookmarkRow` カスタムウィジェットを実装（名前ラベル・A/B点時刻表示・削除ボタンを含む横並びレイアウト） — `main.py`（※T011 と同一ファイルだが独立クラスのため並列可、マージ時に注意）
- [x] T011 [P] [US1] `BookmarkPanel` ウィジェットを実装（`QListWidget` ベース、`BookmarkRow` を `setItemWidget` で設定） — `main.py`（※T010 と同一ファイルだが独立クラスのため並列可、マージ時に注意）
- [x] T012 [US1] ABループ UI エリアに「ブックマーク保存」ボタンを追加（A・B点が両方設定済み時のみ有効） — `main.py`（T010, T011完了後）
- [x] T013 [US1] 「ブックマーク保存」ボタン押下時に `BookmarkStore.add()` を呼び出し `BookmarkPanel` の一覧を更新する処理を実装 — `main.py`（FR-001）
- [x] T014 [US1] `BookmarkPanel` の行クリック時に `VideoPlayer` の `ab_point_a/b` と `ab_loop_active` を更新しループ再生に切り替えるロジックを実装 — `main.py`（FR-003）
- [x] T015 [US1] `BookmarkRow` 名前ラベルのダブルクリックで `QInputDialog.getText()` を呼び出して名前を更新する処理を実装 — `main.py`（FR-004）
- [x] T016 [US1] `BookmarkRow` 削除ボタン押下時に `BookmarkStore.delete()` を呼び出し一覧を更新する処理を実装（再生中の場合はABループを解除） — `main.py`（FR-005）
- [x] T016b [US1] `BookmarkStore.add()` が無効な区間（A>=B、B>動画長）で `ValueError` を送出することの単体テストを作成 — `tests/unit/test_bookmark_store.py`（T016b RED確認後に T017 へ進む）
- [x] T017 [US1] FR-011 バリデーション（`point_a_ms >= point_b_ms` または B点が動画長超過）を `BookmarkStore.add()` に追加し、違反時は `ValueError` を送出 — `bookmark_store.py`（T016b RED確認後）
- [x] T018 [US1] `VideoPlayer` の保存処理で `ValueError` を捕捉し日本語警告ダイアログを表示する処理を `main.py` に追加
- [x] T019 [US1] `BookmarkPanel` を `VideoPlayer._build_ui()` に統合（ABループ UI の下に配置） — `main.py`

**Checkpoint**: `pytest tests/integration/test_bookmark_integration.py::test_us1 -v` が GREEN であること。`python main.py` でブックマーク保存・切り替え・削除が動作すること

---

## Phase 4: User Story 2 - ブックマーク一覧からの連続再生 (Priority: P2)

**Goal**: 「連続再生」ボタンを押すとブックマーク一覧の AB 区間を順番に再生し、各区間の繰り返し回数に従って次の区間へ自動遷移する

**Independent Test**: 複数ブックマークを登録して連続再生を開始し、各区間が繰り返し回数分再生されてから次の区間へ移動すること（`tests/unit/test_sequential_play.py`）

> **テストを先に書き、RED（失敗）を確認してから実装すること**

### US2 テスト

- [x] T020 [US2] `SequentialPlayState` の状態遷移テストを作成（B点到達→繰り返し減算→次区間移動→最終区間後の先頭復帰→停止、**および1件リストでの連続再生が単独ループとして動作すること**） — `tests/unit/test_sequential_play.py`
- [x] T021 [US2] US2 統合テストを作成（連続再生開始→複数区間の自動遷移→停止フロー） — `tests/integration/test_bookmark_integration.py`

### US2 実装

- [x] T022 [US2] `SequentialPlayState` dataclass を `main.py` に実装（bookmarks, current_index, remaining_repeats, active フィールド） — `main.py`（T020 RED確認後）
- [x] T023 [US2] `VideoPlayer._on_timer()` を拡張して `SequentialPlayState.active` が True の場合の B点到達処理（繰り返し減算・次区間移動・先頭復帰）を実装 — `main.py`（T022完了後）
- [x] T024 [US2] `BookmarkPanel` に「連続再生」開始/停止ボタンを追加（ブックマーク0件時は無効） — `main.py`（FR-006）
- [x] T025 [US2] 連続再生開始時に `SequentialPlayState` を初期化し最初の区間のA点から再生開始するロジックを `main.py` に実装
- [x] T026 [US2] 連続再生中の「現在区間名 → 次の区間名」表示ラベルを `BookmarkPanel` に追加・更新する処理を実装 — `main.py`（FR-007）
- [x] T027 [US2] 繰り返し回数 `QSpinBox`（最小1、デフォルト1）を `BookmarkRow` に追加し、値変更時に `BookmarkStore` を更新する処理を実装 — `main.py`（FR-010）

**Checkpoint**: `pytest tests/unit/test_sequential_play.py tests/integration/test_bookmark_integration.py::test_us2 -v` が GREEN であること

---

## Phase 5: User Story 3 - ブックマームの永続化と管理 (Priority: P3)

**Goal**: ブックマークデータを `~/.looplayer/bookmarks.json` に永続化し、アプリ再起動後・動画切り替え時に自動復元する。さらにドラッグ＆ドロップで並び替えを可能にする

**Independent Test**: ブックマーク保存→`BookmarkStore` を再インスタンス化→同じ動画パスで `load()`→元のブックマーク一覧が復元されること（`tests/unit/test_bookmark_store.py`）

> **テストを先に書き、RED（失敗）を確認してから実装すること**

### US3 テスト

- [x] T028 [US3] JSON 永続化の単体テストを作成（一時ディレクトリにJSONを書き込み→再ロードで完全復元、複数動画の分離）— `tests/unit/test_bookmark_store.py`
- [x] T029 [US3] US3 統合テストを作成（動画オープン時の自動ロード・動画切り替え時の一覧切り替え・ドラッグ後の並び順永続化） — `tests/integration/test_bookmark_integration.py`

### US3 実装

- [x] T030 [US3] `BookmarkStore` に JSON ロード/セーブを実装（`~/.looplayer/bookmarks.json`、ディレクトリ自動作成） — `bookmark_store.py`（T028 RED確認後）（FR-008）
- [x] T031 [US3] `VideoPlayer.open_file()` の動画オープン処理に `BookmarkStore.load(path)` を追加し `BookmarkPanel` を更新 — `main.py`（FR-008）
- [x] T032 [US3] `BookmarkPanel` の `QListWidget` にドラッグ＆ドロップ並び替えを設定（`InternalMove` モード + `dropEvent` オーバーライドで `BookmarkStore.update_order()` を呼び出し）— `main.py`（FR-009）
- [x] T033 [US3] `BookmarkStore.update_order()` を実装（ID順リストで `order` フィールドを更新し JSON を保存） — `bookmark_store.py`

**Checkpoint**: `pytest tests/unit/ tests/integration/ -v` が全件 GREEN であること。アプリ再起動後にブックマークが復元されること

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: エッジケース処理の確認・UI の細かい改善

- [x] T034 [P] A・B点が未設定の場合にブックマーク保存ボタンが無効（`setEnabled(False)`）になっていることを確認し、A点またはB点セット時に再評価するロジックを `main.py` に追加
- [x] T035 [P] ブックマーク0件時に連続再生ボタンが無効になっていることを確認し、ブックマーク追加・削除時にボタン状態を再評価するロジックを `main.py` に追加
- [x] T036 全テスト実行・全件パス確認 — `pytest tests/ -v`
- [ ] T037 `python main.py` で quickstart.md の実装フロー3ステップ（US1→US2→US3）を手動動作確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能
- **Foundational (Phase 2)**: Phase 1 完了後 — **全ユーザーストーリーをブロック**
- **User Stories (Phase 3+)**: Phase 2 完了後にそれぞれ開始可能（優先度順: P1→P2→P3）
- **Polish (Phase 6)**: 全ユーザーストーリー完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始可能。他のストーリーへの依存なし
- **US2 (P2)**: Phase 2 完了後に開始可能。US1の `BookmarkStore.add()` が必要（Phase 2でカバー済み）
- **US3 (P3)**: Phase 2 完了後に開始可能。US1・US2 のUI統合後に実施するのが自然

### Within Each User Story

1. テストを書いて **RED（失敗）を確認** してから実装開始
2. モデル/データクラス → サービス/ロジック → UI統合の順
3. ストーリー完了後に `pytest` でチェックポイントを確認してからコミット

### Parallel Opportunities

- Phase 1: T002・T003・T004 は並列実行可能（異なるファイル）
- Phase 3: T010・T011 は並列実行可能（どちらも独立したウィジェット）
- Phase 6: T034・T035 は並列実行可能

---

## Parallel Example: User Story 1

```bash
# Phase 3 内の並列可能タスク（Phase 2 完了後）:
# T009（統合テスト作成）完了後、以下を並列:
Task T010: "BookmarkRow カスタムウィジェットを main.py に実装"
Task T011: "BookmarkPanel ウィジェットを main.py に実装"

# T010, T011 完了後に順番に:
Task T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019
```

---

## Implementation Strategy

### MVP First（User Story 1 のみ）

1. Phase 1 完了: ファイル骨格作成
2. Phase 2 完了: データモデル準備（**必須: 全ストーリーをブロック**）
3. Phase 3 完了: US1 ブックマーク登録・切り替え
4. **STOP & VALIDATE**: `pytest tests/integration/test_bookmark_integration.py::test_us1 -v` GREEN → `python main.py` で動作確認
5. 必要なら MVP としてデモ

### Incremental Delivery

1. Setup + Foundational → データモデル準備完了
2. US1 追加 → ブックマーク登録・切り替え（MVP）
3. US2 追加 → 連続再生
4. US3 追加 → 永続化・並び替え

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベルでタスクをユーザーストーリーにトレース
- **憲法 I**: テストを先に書き、RED を確認してから実装する
- **憲法 II/III**: 追加の抽象レイヤーを作らない。`BookmarkStore` は直接操作クラス
- 各チェックポイントで `pytest` をパスしてからコミットする
- ブックマーク保存・削除のたびに JSON 永続化（US3 実装後）
