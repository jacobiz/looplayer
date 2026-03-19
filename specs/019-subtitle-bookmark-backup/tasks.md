# Tasks: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Input**: Design documents from `/specs/019-subtitle-bookmark-backup/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ui-contracts.md ✅, quickstart.md ✅

**テスト方針**: constitution I.「テストファースト」に従い、各ユーザーストーリーのテストを先に書いて失敗を確認してから実装する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー (US1, US2, US3)
- 各タスクに正確なファイルパスを含める

---

## Phase 1: Setup（既存環境確認）

**目的**: テスト環境と既存コードベースが正常であることを確認する

- [X] T001 既存テストスイートを実行して全テストがパスすることを確認する (`pytest tests/ -v`)

---

## Phase 2: Foundational（共通基盤 — 全ユーザーストーリーの前提）

**目的**: F-202・F-402 で使用する i18n 文字列を追加する。全ストーリーが参照するため先に完了させる。

**⚠️ CRITICAL**: このフェーズ完了後でないとユーザーストーリーの実装に進めない

- [X] T002 F-202・F-402 用 UI 文字列（メニュー項目・メッセージ）を `looplayer/i18n.py` に追加する（追加キー: `menu.playback.subtitle.generate_bookmarks`, `menu.file.backup_data`, `menu.file.restore_data`, `msg.subtitle_generate_success`, `msg.subtitle_not_loaded`（字幕未読み込みエラー、既存の `msg.subtitle_no_video` とは別キー）, `msg.backup_success`, `msg.backup_no_data`, `msg.backup_write_error`, `msg.restore_confirm`, `msg.restore_success`, `msg.restore_invalid`, `msg.restore_corrupt`, `msg.restore_write_error`, `msg.encoding_error`）

**Checkpoint**: i18n 文字列追加完了 — 各ストーリーの実装開始可能

---

## Phase 3: User Story 1 — 字幕からブックマーク一括生成 (Priority: P1) 🎯 MVP

**Goal**: SRT/ASS 字幕ファイルの各エントリを A/B 点付きブックマークとして一括登録し、Ctrl+Z で取り消しできる

**Independent Test**: SRT ファイルを読み込んだ状態で「字幕からブックマーク生成」を実行し、ブックマークパネルに字幕区間が登録され、Ctrl+Z で全件削除されることを確認できる

### US1 テスト（先に書いて失敗を確認してから実装）⚠️

> **NOTE: 先にテストを書き → `pytest` で FAIL を確認 → 実装 → PASS を確認**

- [X] T003 [P] [US1] `tests/unit/test_subtitle_parser.py` を新規作成してパーサー全関数の失敗テストを書く（SRT 正常パース・タイムスタンプ ms 変換・ASS タグ除去・80 文字切り詰め・`start_ms >= end_ms` スキップ・UTF-8/cp932 エンコーディング・空ファイル・非対応拡張子・**重複/入れ子字幕区間が独立したブックマークとして登録されること**）
- [X] T004 [P] [US1] `tests/integration/test_subtitle_bookmark_integration.py` を新規作成して字幕→ブックマーク→Undo 統合テストの失敗テストを書く（BookmarkStore を実際に使用・`tmp_path` でストレージ分離）

### US1 実装

- [X] T005 [US1] `looplayer/subtitle_parser.py` を新規作成する（`SubtitleEntry` dataclass・`BulkAddResult` dataclass・`parse_srt(text: str) -> list[SubtitleEntry]`・`parse_ass(text: str) -> list[SubtitleEntry]`・`parse_subtitle_file(path: Path) -> list[SubtitleEntry]`・`entries_to_bookmarks(entries, start_order) -> BulkAddResult` を実装）
- [X] T006 [US1] `looplayer/bookmark_store.py` に `add_many(video_path: str, bookmarks: list[LoopBookmark]) -> None` メソッドを追加する（既存 `add()` を繰り返し呼び出す最小実装）
- [X] T007 [US1] `looplayer/widgets/bookmark_panel.py` に `set_last_bulk_add(bookmarks: list[LoopBookmark]) -> None` と `undo_bulk_add() -> None` を追加する（既存 `_undo_delete` パターンを参考に、追加したブックマークを全件削除）
- [X] T008 [US1] `looplayer/player.py` に「字幕からブックマーク生成」メニューアクションを追加し `_generate_bookmarks_from_subtitles()` ハンドラを実装する（再生 > 字幕 サブメニュー内・`_rebuild_subtitle_menu()` に追加・有効化条件: 動画かつ外部字幕が読み込まれている）

**Checkpoint**: US1 完了 — SRT/ASS から一括生成・Undo が独立して動作する

---

## Phase 4: User Story 2 — データをバックアップする (Priority: P2)

**Goal**: 「ファイル > データをバックアップ...」から `~/.looplayer/` 以下の全 JSON ファイルをマニフェスト付き ZIP に保存できる

**Independent Test**: 「データをバックアップ」を実行し、`looplayer-backup-YYYYMMDD-HHMMSS.zip` が作成され ZIP 内に全データファイルとマニフェストが含まれることを確認できる

### US2 テスト（先に書いて失敗を確認してから実装）⚠️

- [X] T009 [P] [US2] `tests/unit/test_data_backup.py` を新規作成して `create_backup()` の失敗テストを書く（ZIP 作成・マニフェスト内容検証・ファイルが 1 件も存在しない場合の `BackupError`・書き込み権限なしの `OSError` 伝播・`generate_backup_filename()` フォーマット検証）

### US2 実装

- [X] T010 [US2] `looplayer/data_backup.py` を新規作成する（`BackupError` 例外クラス・`generate_backup_filename() -> str`・`create_backup(dest_path: Path, data_dir: Path | None = None) -> None` を実装・`BackupManifest` は dict として扱い別クラスは作らない）
- [X] T011 [US2] `looplayer/player.py` に「データをバックアップ...」メニューアクションを追加し `_backup_data()` ハンドラを実装する（ファイル > クリップ書き出しの前にセパレータ付きで配置・`QFileDialog.getSaveFileName` でパス取得・`BackupError` と `OSError` をそれぞれ異なるメッセージで表示）

**Checkpoint**: US2 完了 — バックアップ ZIP 作成が独立して動作する

---

## Phase 5: User Story 3 — バックアップからデータを復元する (Priority: P3)

**Goal**: 「ファイル > データを復元...」から looplay! バックアップ ZIP を選択し、確認後に全データを復元してアプリを終了できる

**Independent Test**: US2 で作成した ZIP を選択して復元を実行し、データが元の状態に戻りアプリが終了することを確認できる。非 looplay! ZIP を選択するとエラーになることも確認する。

**前提**: US2 が完了していること（`data_backup.py` が存在）

### US3 テスト（先に書いて失敗を確認してから実装）⚠️

- [X] T012 [P] [US3] `tests/unit/test_data_backup.py` に `restore_backup()` の失敗テストを追加する（バックアップ→復元サイクル・非 looplay! ZIP の `BackupError`・破損 ZIP の `BackupError`・**書き込み権限なし `OSError` 時に既存データが変更されないことの検証**・既存データが変更されないことの検証）

### US3 実装

- [X] T013 [US3] `looplayer/data_backup.py` に `restore_backup(zip_path: Path, data_dir: Path | None = None) -> None` を追加する（マニフェスト `app_name` 検証・`zipfile.BadZipFile` を `BackupError` でラップ・検証成功後に各ファイルを `data_dir` に展開）。`BackupError` には `reason: str` 属性を持たせ `"invalid"`（非対応ファイル）と `"corrupt"`（破損 ZIP）を区別できるようにする
- [X] T014 [US3] `looplayer/player.py` に「データを復元...」メニューアクションを追加し `_restore_data()` ハンドラを実装する（`QFileDialog.getOpenFileName` で ZIP 取得・確認ダイアログ表示・`BackupError.reason == "invalid"` → `msg.restore_invalid`・`BackupError.reason == "corrupt"` → `msg.restore_corrupt`・`OSError` → `msg.restore_write_error` を表示・成功時は `QApplication.instance().quit()` で終了）

**Checkpoint**: US3 完了 — バックアップ/復元サイクルが独立して動作する

---

## Phase 6: Polish & Cross-Cutting Concerns

**目的**: 全ストーリー横断の品質確認と仕上げ

- [X] T015 [P] 全テストを実行して既存テストの非退行と新規テストのパスを確認する (`pytest tests/ -v`)
- [X] T016 500 件超の字幕エントリでパフォーマンステストを行い 5 秒以内に完了することを確認する（SC-001 検証・`tests/unit/test_subtitle_parser.py` に追加）
- [X] T017 [P] `looplayer/subtitle_parser.py` と `looplayer/data_backup.py` のコードを PEP 8 に準拠しているか確認・整理する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし — 即座に開始可能
- **Phase 2 (Foundational)**: Phase 1 完了後 — **全ユーザーストーリーをブロック**
- **Phase 3 (US1)**: Phase 2 完了後 — 他ストーリーとは独立して実装可能
- **Phase 4 (US2)**: Phase 2 完了後 — US1 とは独立して実装可能
- **Phase 5 (US3)**: Phase 4 完了後 — `data_backup.py` の `create_backup()` が必要
- **Phase 6 (Polish)**: 全ストーリー完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 後に開始可 — US2/US3 との依存なし
- **US2 (P2)**: Phase 2 後に開始可 — US1 との依存なし
- **US3 (P3)**: US2 完了後に開始 — `data_backup.py` を共有

### Within Each User Story

1. テストを書く（T003/T004、T009、T012）
2. `pytest` で FAIL を確認
3. 実装（T005-T008、T010-T011、T013-T014）
4. `pytest` で PASS を確認
5. コミット

### Parallel Opportunities

- T003・T004 は並列実行可（異なるファイル）
- T005（subtitle_parser.py）・T006（bookmark_store.py）・T007（bookmark_panel.py）は並列実行可
- T009（test_data_backup.py）は T003/T004 と並列実行可
- T010（data_backup.py）・T011（player.py US2）は並列実行可
- T015・T016・T017 は並列実行可

---

## Parallel Example: User Story 1

```bash
# テストを先に並列で書く
Task: "T003 tests/unit/test_subtitle_parser.py を作成"
Task: "T004 tests/integration/test_subtitle_bookmark_integration.py を作成"

# FAIL 確認後、実装を並列で進める
Task: "T005 looplayer/subtitle_parser.py を作成"
Task: "T006 looplayer/bookmark_store.py に add_many() を追加"
Task: "T007 looplayer/widgets/bookmark_panel.py に undo_bulk_add() を追加"
# T008 (player.py) は T005/T006/T007 完了後
```

---

## Implementation Strategy

### MVP First (User Story 1 のみ)

1. Phase 1: Setup — テスト環境確認
2. Phase 2: Foundational — i18n 文字列追加
3. Phase 3: US1 — 字幕→ブックマーク生成
4. **STOP & VALIDATE**: US1 を独立してテスト・デモ
5. 必要であればリリース

### Incremental Delivery

1. Setup + Foundational → 基盤完了
2. US1 → 独立テスト → デモ（MVP）
3. US2 → 独立テスト → デモ
4. US3 → 独立テスト → デモ
5. 各ストーリーが前のストーリーを壊さない形で追加

---

## Notes

- [P] タスク = 異なるファイル・完了済みタスクへの依存なし
- テストは実装前に FAIL することを必ず確認する（constitution I.）
- 各フェーズの Checkpoint でテストをパスしてからコミットする
- `subtitle_parser.py` は副作用なしの純粋関数のみ → テストが書きやすい
- `data_backup.py` は `data_dir` パラメータで `tmp_path` に差し替え可能 → テストが書きやすい
- `player.py` の変更はメニュー追加とハンドラ実装のみ → 既存機能への影響を最小化

