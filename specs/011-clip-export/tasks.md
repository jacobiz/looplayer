# Tasks: AB ループ区間クリップ書き出し

**Input**: Design documents from `/specs/011-clip-export/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: テストファースト（憲法 I）に従い、各フェーズでテストを先に書いてから実装する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: ユーザーストーリー対応（US1, US2）

---

## Phase 1: Setup（共有インフラ）

**Purpose**: i18n キーの追加。新規ファイルなし。既存 looplayer/ パッケージに追記のみ。

- [X] T001 looplayer/i18n.py にクリップ書き出し用 i18n キーを追加する（`menu.file.export_clip`、`dialog.export.title`、`msg.export_success.title`、`msg.export_success.body`、`msg.ffmpeg_not_found.title`、`msg.ffmpeg_not_found.body`、`btn.open_folder`）

---

## Phase 2: Foundational（ブロッキング前提タスク）

**Purpose**: ClipExportJob と ExportWorker は US1・US2 の両方が依存する共有コンポーネント。これが揃ってからユーザーストーリーの実装に入る。

**⚠️ CRITICAL**: Phase 2 完了まで US1・US2 の実装を開始しない

- [X] T002 [P] tests/unit/test_clip_export.py を作成し ClipExportJob のユニットテストを書く（デフォルトファイル名フォーマット `{stem}_00m15s-01m30s.mp4`、ms → HH:MM:SS.mmm 変換、ファイル名サニタイズ `\ / : * ? " < > |` → `_`、start_ms >= end_ms のバリデーション）
- [X] T003 [P] tests/unit/test_clip_export.py に ExportWorker のユニットテストを追記する（subprocess モック: returncode=0 で `finished` シグナル、returncode=1 で `failed` シグナル、`shutil.which` → None で `failed` シグナル、`requestInterruption()` でファイル削除、ffmpeg コマンド順序 `-ss START -to END -i INPUT -c copy OUTPUT`）
- [X] T004 looplayer/clip_export.py を新規作成し ClipExportJob dataclass を実装する（フィールド: `source_path: Path`、`start_ms: int`、`end_ms: int`、`output_path: Path`、プロパティ: `duration_ms`、メソッド: `default_filename() -> str`、`_ms_to_label(ms) -> str`、`_sanitize(name) -> str`、`_ms_to_ffmpeg_time(ms) -> str`）。T002 のテストを通過させる
- [X] T005 looplayer/clip_export.py に ExportWorker(QThread) を追記する（シグナル: `finished(str)`、`failed(str)`、`run()` で `shutil.which("ffmpeg")` 検出 → ffmpeg subprocess 起動 `[ffmpeg, -ss, START, -to, END, -i, INPUT, -c, copy, OUTPUT, -y]` → 100ms ポーリング + `isInterruptionRequested()` チェック → `terminate()/wait()` キャンセル → ファイル削除）。T003 のテストを通過させる

**Checkpoint**: ClipExportJob と ExportWorker が完成し全ユニットテストがパスする

---

## Phase 3: User Story 1 - 現在の AB ループ区間を書き出す (Priority: P1) 🎯 MVP

**Goal**: ファイルメニュー「クリップを書き出す...」から AB ループ区間を書き出せる

**Independent Test**: AB ループを設定した状態でメニュー項目が有効化され、実行すると保存ダイアログ → 書き出し → 成功通知の一連の流れが完結する

### テスト（テストファースト）

- [X] T006 [US1] tests/integration/test_clip_export_integration.py を新規作成し、ファイルメニュー統合テストを書く（AB ループ未設定時にアクション disabled、AB ループ設定済みでアクション enabled、A点=B点でアクション disabled）。conftest.py の player フィクスチャを参考に ExportWorker をモック

### 実装

- [X] T007 [US1] looplayer/widgets/export_dialog.py を新規作成し ExportProgressDialog(QDialog) を実装する（ウィンドウタイトル `t("dialog.export.title")`、QLabel「書き出し中...」、QProgressBar `setRange(0,0)` 不確定表示、「キャンセル」ボタン、`ExportWorker.finished` → `accept()`（成功通知は呼び出し元の `_export_clip()` が担当）、`ExportWorker.failed` → ラベルにエラー表示 + `reject()`、`closeEvent` で `requestInterruption() + wait()`）
- [X] T008 [US1] looplayer/player.py の「ファイル」メニューにセパレーター＋「クリップを書き出す... (Ctrl+E)」QAction を追加する（初期状態: disabled）
- [X] T009 [US1] looplayer/player.py の AB ループ状態変更箇所（A点設定・B点設定・クリア）で export アクションの enabled 状態を更新する（`loop_a_ms is not None and loop_b_ms is not None and loop_a_ms < loop_b_ms` のとき有効）。T006 のテストを通過させる
- [X] T010 [US1] looplayer/player.py に `_export_clip()` スロットを実装する（① `shutil.which("ffmpeg")` 検出、未検出時は `t("msg.ffmpeg_not_found.title")` エラーダイアログ表示して終了、② `ClipExportJob` のデフォルトファイル名を生成、③ `QFileDialog.getSaveFileName` でデフォルト先=元動画フォルダ、④ `job = ClipExportJob(source_path, start_ms, end_ms, output_path)` を生成し `ExportProgressDialog(job, parent=self).exec()` で書き出し、⑤ `exec()` が `QDialog.Accepted` を返したとき `QMessageBox.information` で「フォルダを開く」ボタン付き成功通知を表示（H2: 通知はここで一元管理）、⑥ 書き出し中は export アクションを disabled にする）

**Checkpoint**: US1 完了 — AB ループ → 書き出しの一連フローが動作し統合テストがパスする

---

## Phase 4: User Story 2 - ブックマークの A/B 区間を書き出す (Priority: P2)

**Goal**: BookmarkRow のコンテキストメニューからブックマーク区間を書き出せる

**Independent Test**: A点・B点が設定されたブックマーク行を右クリックすると「クリップを書き出す」が有効表示され、実行すると書き出しが完了する

### テスト（テストファースト）

- [X] T011 [US2] tests/integration/test_clip_export_integration.py にブックマークコンテキストメニューテストを追記する（A点・B点設定済みブックマーク → export_requested シグナルが発行される、A点またはB点が None のブックマーク → メニュー項目が disabled）

### 実装

- [X] T012 [US2] looplayer/widgets/bookmark_row.py に `export_requested = pyqtSignal(int, int, str)` シグナル（a_ms, b_ms, label）を追加し、右クリックコンテキストメニューに「クリップを書き出す」項目を追加する（有効条件: `loop_a_ms is not None and loop_b_ms is not None and loop_a_ms < loop_b_ms`、クリック時に `export_requested.emit(loop_a_ms, loop_b_ms, label)` を発行）。T011 のテストを通過させる
- [X] T013 [US2] looplayer/player.py で BookmarkRow の `export_requested` シグナルを受け取るスロット `_export_clip_from_bookmark(a_ms, b_ms, label)` を実装し、`_export_clip()` と同じフロー（ffmpeg 検出 → ファイルダイアログ → ExportProgressDialog）を経由してブックマーク名ベースのデフォルトファイル名で書き出す

**Checkpoint**: US2 完了 — ブックマーク行からの書き出しが動作し全テストがパスする

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T014 [P] 全テストを実行して回帰がないことを確認する: `pytest tests/unit/test_clip_export.py tests/integration/test_clip_export_integration.py -v`
- [X] T015 [P] 既存の統合テスト一式が壊れていないことを確認する: `pytest tests/ -v --ignore=tests/unit/test_clip_export.py --ignore=tests/integration/test_clip_export_integration.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし — 即開始可能
- **Phase 2 (Foundational)**: Phase 1 完了後 — Phase 3・4 をブロック
- **Phase 3 (US1)**: Phase 2 完了後 — US2 と並列可能
- **Phase 4 (US2)**: Phase 2 完了後 — US1 と並列可能（ただし T013 は T010 の `_export_clip` パターンを参照）
- **Phase 5 (Polish)**: Phase 3・4 完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始。他ストーリーへの依存なし
- **US2 (P2)**: Phase 2 完了後に開始。T013 は T010 の実装パターンを参考にするが、独立して動作する

### Within Each Phase

- T002 と T003 は並列実行可（同一ファイルだが内容が独立）
- T004 → T002 通過 → コミット
- T005 → T003 通過 → コミット
- T007 は T005（ExportWorker）完了後に着手

### Parallel Opportunities

```bash
# Phase 2 テスト並列書き出し:
T002: ClipExportJob ユニットテスト
T003: ExportWorker ユニットテスト

# Phase 3 と Phase 4 は Phase 2 完了後に並列:
Phase 3 (US1): T006 → T007 → T008 → T009 → T010
Phase 4 (US2): T011 → T012 → T013
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1: T001（i18n キー）
2. Phase 2: T002 → T004 → T003 → T005（テストファースト）
3. Phase 3: T006 → T007 → T008 → T009 → T010
4. **STOP & VALIDATE**: `pytest tests/unit/test_clip_export.py tests/integration/test_clip_export_integration.py::TestFileMenuExport -v`
5. US1 が独立して動作することを確認

### Incremental Delivery

1. Phase 1 + 2 → 基盤完成
2. Phase 3（US1）→ MVP: AB ループから書き出し
3. Phase 4（US2）→ ブックマーク書き出し追加
4. Phase 5 → 全体検証

---

## Notes

- テストファースト必須（憲法 I）: 各フェーズでテストを書いて失敗確認してから実装
- [P] タスク = 異なるファイルまたは内容が独立
- ExportEngine 抽象クラスは作らない（憲法 III）
- UI ラベルは `t()` 経由で i18n 対応（T001 で先に追加）
- BookmarkPanel は変更不要 — BookmarkRow からのシグナルを VideoPlayer が直接受ける
