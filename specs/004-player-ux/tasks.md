# Tasks: プレイヤー UX 改善

**Input**: Design documents from `/specs/004-player-ux/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.
**Note**: テストファースト必須（Constitution I）— テストタスクは必ず実装タスクより先に実行すること。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- 各テストタスクは「RED（失敗確認）」後に実装タスクを開始すること

---

## Phase 1: Setup（既存プロジェクト確認）

**Purpose**: 既存プロジェクトの動作確認と共有基盤の準備

- [X] T001 既存テストスイートが全パスすることを確認する: `pytest tests/ -v`
- [X] T002 `open_file()` のコアロジックを `_open_path(path: str)` として `looplayer/player.py` に切り出す（US1・US2 共通呼び出し口）。**TDD 適用**: T001 で確認済みの既存テスト群がリファクタ後も全パスすることをもって RED→GREEN サイクルとみなす（新規機能ではなく動作保持リファクタのため）

**Checkpoint**: `pytest tests/ -v` が全パス、`_open_path()` が既存の `open_file()` から呼ばれている

---

## Phase 2: Foundational（ブロッキング前提なし）

**Purpose**: 本フィーチャーにはアーキテクチャ変更の前提条件はないため Phase 2 は省略。各 US は Phase 1 完了後に独立して着手可能。

---

## Phase 3: User Story 1 — ドラッグ＆ドロップ (Priority: P1) 🎯 MVP

**Goal**: ファイルマネージャーから動画ファイルをドロップするだけで再生できる

**Independent Test**: `pytest tests/integration/test_drag_drop.py -v` が全パス

### Tests for User Story 1 ⚠️ RED FIRST

> **これらのテストを先に書き、FAIL することを確認してから実装を開始すること**

- [X] T003 [P] [US1] `tests/integration/test_drag_drop.py` を作成する（`dragEnterEvent` 受付・`dropEvent` ファイルオープン・非対応拡張子無視・複数ファイル先頭のみのテストを含む）

### Implementation for User Story 1

- [X] T004 [US1] `looplayer/player.py` に `setAcceptDrops(True)`・`dragEnterEvent()`・`dropEvent()` を実装し、`_open_path()` 経由でファイルを開く（`os.path.normpath` でパス正規化）

**Checkpoint**: `pytest tests/integration/test_drag_drop.py -v` 全パス — US1 単独で動作確認可能

---

## Phase 4: User Story 2 — 最近開いたファイル (Priority: P1)

**Goal**: アプリ再起動後も「ファイル > 最近開いたファイル」から過去の動画を素早く開ける

**Independent Test**: `pytest tests/unit/test_recent_files.py tests/integration/test_recent_files_menu.py -v` が全パス

### Tests for User Story 2 ⚠️ RED FIRST

- [X] T005 [P] [US2] `tests/unit/test_recent_files.py` を作成する（`RecentFiles.add()` 先頭挿入・重複排除・MAX10件・永続化のテストを含む）
- [X] T006 [P] [US2] `tests/integration/test_recent_files_menu.py` を作成する（メニュー表示・ファイル名のみ・ツールチップフルパス・存在しないファイル選択時削除のテストを含む）

### Implementation for User Story 2

- [X] T007 [US2] `looplayer/recent_files.py` を新規作成し `RecentFiles` クラス（`add()`・`remove()`・`files` プロパティ・`~/.looplayer/recent_files.json` アトミック書き込み）を実装する
- [X] T008 [US2] `looplayer/player.py` に `_recent: RecentFiles`・`_recent_menu: QMenu`・`_rebuild_recent_menu()`・`_open_recent()` を追加し、ファイルメニューにサブメニューとして組み込む

**Checkpoint**: `pytest tests/unit/test_recent_files.py tests/integration/test_recent_files_menu.py -v` 全パス

---

## Phase 5: User Story 3 — ウィンドウを動画解像度にリサイズ (Priority: P2)

**Goal**: 動画を開いたとき、ウィンドウが動画のアスペクト比に自動調整される

**Independent Test**: `pytest tests/integration/test_window_resize.py -v` が全パス

### Tests for User Story 3 ⚠️ RED FIRST

- [X] T009 [P] [US3] `tests/integration/test_window_resize.py` を作成する（`_resize_to_video()` 呼び出し・最小サイズ 800×600 クランプ・ディスプレイサイズ上限クランプ・フルスクリーン中スキップ・手動トリガーメニュー存在・**ユーザー手動リサイズ後に `_size_poll_timer` が再発動しないこと**のテストを含む）

### Implementation for User Story 3

- [X] T010 [US3] `looplayer/player.py` に `_video_changed = pyqtSignal()`・`MediaPlayerVideoChanged` イベントアタッチ・`_size_poll_timer`（50ms）・`_poll_video_size()`・`_resize_to_video(w, h)` を実装する（スクリーンサイズ上限・最小 800×600 クランプ・フルスクリーン中 return）
- [X] T011 [US3] `looplayer/player.py` の 表示メニュー に「ウィンドウを動画サイズに合わせる」QAction を追加し `_start_size_poll()` を呼び出す

**Checkpoint**: `pytest tests/integration/test_window_resize.py -v` 全パス

---

## Phase 6: User Story 4 — フルスクリーン中カーソル自動非表示 (Priority: P2)

**Goal**: フルスクリーン中に 3 秒無操作でカーソルが消え、マウス移動で即座に再表示される

**Independent Test**: `pytest tests/integration/test_cursor_hide.py -v` が全パス

### Tests for User Story 4 ⚠️ RED FIRST

- [X] T012 [P] [US4] `tests/integration/test_cursor_hide.py` を作成する（フルスクリーン中タイマー発火で `BlankCursor` セット・マウス移動で `unsetCursor`・通常ウィンドウでは非発動・フルスクリーン解除時に `unsetCursor` のテストを含む）

### Implementation for User Story 4

- [X] T013 [US4] `looplayer/player.py` に `_cursor_hide_timer`（3000ms singleShot）・`_hide_cursor()`・`_show_cursor()` を追加し、`mouseMoveEvent()` でフルスクリーン時のみタイマーリセット・`toggle_fullscreen()` でタイマー起動・`_exit_fullscreen()` でタイマー停止と `unsetCursor()` 呼び出しを実装する

**Checkpoint**: `pytest tests/integration/test_cursor_hide.py -v` 全パス

---

## Phase 7: User Story 5 — ブックマーク削除の取り消し (Priority: P2)

**Goal**: 削除直後 5 秒以内に Ctrl+Z で全属性込みでブックマークを復元できる

**Independent Test**: `pytest tests/unit/test_bookmark_undo.py -v` が全パス

### Tests for User Story 5 ⚠️ RED FIRST

- [X] T014 [P] [US5] `tests/unit/test_bookmark_undo.py` を作成する（削除後タイマー内 Undo で復元・元の order 復元・5秒経過後 Undo 無効・連続削除で前の保留確定・動画切替で保留クリアのテストを含む）

### Implementation for User Story 5

- [X] T015 [US5] `looplayer/widgets/bookmark_panel.py` に `_pending_delete: dict | None`・`_undo_timer`（5000ms singleShot）・`_commit_delete()`・`_undo_delete()` を追加し、`_on_delete()` を「即時削除→保留」パターンに変更する。`load_video()` 内でも `_commit_delete()` を呼ぶ
- [X] T016 [US5] `looplayer/player.py` に Ctrl+Z の QAction（ApplicationShortcut）を追加し `bookmark_panel._undo_delete()` を呼び出す

**Checkpoint**: `pytest tests/unit/test_bookmark_undo.py -v` 全パス

---

## Phase 8: User Story 6 — ブックマーク エクスポート＆インポート (Priority: P3)

**Goal**: ブックマークを JSON ファイルとして書き出し・読み込みできる

**Independent Test**: `pytest tests/unit/test_bookmark_io.py tests/integration/test_export_import.py -v` が全パス

### Tests for User Story 6 ⚠️ RED FIRST

- [X] T017 [P] [US6] `tests/unit/test_bookmark_io.py` を作成する（`export_bookmarks()` JSON 出力・id フィールドなし・`import_bookmarks()` 正常パース・無効 JSON の ValueError・型キャスト（float混入対策）のテストを含む）
- [X] T018 [P] [US6] `tests/integration/test_export_import.py` を作成する（エクスポートメニュー有効/無効・インポート時重複スキップ・インポート先が現在の動画・無効 JSON エラーメッセージのテストを含む）

### Implementation for User Story 6

- [X] T019 [US6] `looplayer/bookmark_io.py` を新規作成し `export_bookmarks(bookmarks, dest_path)`・`import_bookmarks(src_path)` を実装する（スキーマ: `version:1`, `exported_at`, `bookmarks[]`; id 含まず; `(point_a_ms, point_b_ms)` 重複チェック）
- [X] T020 [US6] `looplayer/player.py` のファイルメニューに「ブックマークをエクスポート」（動画未選択時無効）・「ブックマークをインポート」QAction を追加し、`bookmark_io` 呼び出しと重複排除・エラーハンドリングを実装する

**Checkpoint**: `pytest tests/unit/test_bookmark_io.py tests/integration/test_export_import.py -v` 全パス

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: 全ストーリー完了後の最終確認

- [X] T021 全テストスイートを実行してリグレッションがないことを確認する: `pytest tests/ -v`
- [X] T022 `specs/004-player-ux/quickstart.md` の US1〜US6 手動検証シナリオを実行して全て合格することを確認する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし — 即着手可能
- **Phase 3 (US1)**: Phase 1 完了後 — `_open_path()` に依存
- **Phase 4 (US2)**: Phase 1 完了後 — `_open_path()` に依存
- **Phase 5 (US3)**: Phase 1 完了後 — 独立
- **Phase 6 (US4)**: Phase 1 完了後 — 既存の `toggle_fullscreen()` に依存（Phase 3 不要）
- **Phase 7 (US5)**: Phase 1 完了後 — 独立（`BookmarkStore` 既存）
- **Phase 8 (US6)**: Phase 1 完了後 — 独立（`LoopBookmark` 既存）
- **Phase 9 (Polish)**: 全フェーズ完了後

### User Story Dependencies

- **US1 (P1)**: `_open_path()` リファクタ（T002）完了後
- **US2 (P1)**: `_open_path()` リファクタ（T002）完了後; US1 と並行実装可能
- **US3 (P2)**: US1/US2 完了不要; Phase 1 後即着手可能
- **US4 (P2)**: US1/US2/US3 完了不要; Phase 1 後即着手可能
- **US5 (P2)**: 全 US と独立; Phase 1 後即着手可能
- **US6 (P3)**: US5 完了後推奨（BookmarkPanel の変更が安定してから）

### Parallel Opportunities

- T003 (US1 テスト) と T005/T006 (US2 テスト) は同時並行可能
- T007 (RecentFiles クラス) と T004 (D&D 実装) は別ファイルなので並行可能
- T009/T012/T014/T017/T018 の各テスト作成は相互に並行可能

---

## Parallel Example: US1 + US2 (P1 同時開発)

```bash
# Phase 1 完了後、US1 と US2 を並行開始:

# 開発者 A — US1
Task: T003  # test_drag_drop.py 作成 (RED)
Task: T004  # D&D 実装 (GREEN)

# 開発者 B — US2
Task: T005  # test_recent_files.py 作成 (RED)
Task: T006  # test_recent_files_menu.py 作成 (RED)
Task: T007  # recent_files.py 実装 (GREEN)
Task: T008  # player.py メニュー統合 (GREEN)
```

---

## Implementation Strategy

### MVP First (US1 のみ)

1. Phase 1: Setup → T001, T002
2. Phase 3: US1 → T003, T004
3. **STOP and VALIDATE**: `pytest tests/integration/test_drag_drop.py -v`
4. Demo: ファイルドロップで動画が開くことを確認

### Incremental Delivery

1. Setup (T001-T002) → Foundation ready
2. US1 (T003-T004) → D&D 動作 → Demo
3. US2 (T005-T008) → 最近開いたファイル動作 → Demo
4. US3 (T009-T011) → ウィンドウリサイズ動作 → Demo
5. US4 (T012-T013) → カーソル非表示動作 → Demo
6. US5 (T014-T016) → Undo 動作 → Demo
7. US6 (T017-T020) → エクスポート/インポート動作 → Demo
8. Polish (T021-T022) → 全体確認

---

## Notes

- **テストファースト厳守**: 各 US のテストタスクを先に完了し、FAIL を確認してから実装着手
- **T002 の `_open_path()` リファクタ**: US1・US2 の前提。既存テストが全パスすることを確認してから進める
- **VLC コールバック注意**: T010 の `_on_vlc_video_changed` は VLC スレッドから呼ばれるため `pyqtSignal` 経由必須（直接 UI 操作禁止）
- **lambda キャプチャ注意**: T008 の `_rebuild_recent_menu` の lambda は `p=path` デフォルト引数で束縛すること（late-binding 問題回避）
- **`blockSignals` 注意**: `_set_volume()` 等、スライダー更新時は `blockSignals(True/False)` で循環シグナルを防止（既存パターン踏襲）
