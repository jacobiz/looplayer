# Tasks: 自動更新機能 (010-auto-update)

**Input**: Design documents from `/specs/010-auto-update/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 新規ファイルの作成と i18n キーの追加

- [x] T001 [P] `looplayer/i18n.py` に 13 個の i18n キーを追加する（`menu.help.check_update`、`menu.help.auto_check`、`msg.update_available.title/body`、`msg.update_latest.title/body`、`msg.update_check_failed.title/body`、`msg.update_download_failed.title`、`dialog.download.title`、`btn.download_now`、`btn.later`、`btn.retry`、`status.update_checking`）。`msg.update_available.body` は `{current_ver}` と `{ver}` の 2 プレースホルダーを含める（FR-002: 現在と新バージョン両方を明示）
- [x] T002 [P] `looplayer/app_settings.py` に `check_update_on_startup: bool`（デフォルト `True`）プロパティを追加する

---

## Phase 2: Foundational（ブロッキング前提条件）

**Purpose**: UpdateChecker・DownloadThread の実装。US1/US2/US3 すべての前提。

**⚠️ CRITICAL**: この Phase が完了するまで US フェーズの実装は開始しない

### US1/US2/US3 共通テスト（テストファースト）

> **NOTE: 以下のテストを先に書き、FAIL することを確認してから実装する**

- [x] T003 `tests/unit/test_updater.py` を作成し、`_is_newer()` バージョン比較関数のユニットテストを書く（新しい場合・同じ場合・古い場合・"v" プレフィックスの剥離）
- [x] T004 `tests/unit/test_updater.py` に `UpdateChecker` のユニットテストを追加する（`update_available`・`up_to_date`・`check_failed` 各シグナルの発行を `unittest.mock.patch` で GitHub API をモック）
- [x] T005 `tests/unit/test_updater.py` に `AppSettings.check_update_on_startup` のユニットテストを追加する（デフォルト値・保存・読み込み）

### Foundational 実装

- [x] T006 `looplayer/updater.py` を新規作成し、`from looplayer.version import VERSION` でバージョンを取得・`_is_newer()` 関数・`_parse_version()` ヘルパーを実装する（`looplayer/version.py::VERSION = "1.1.0"` が既存のため新規定数作成不要）
- [x] T007 `looplayer/updater.py` に `UpdateChecker(QThread)` を実装する（`update_available(str, str)`・`up_to_date()`・`check_failed(str)` シグナル、GitHub API 呼び出し、タイムアウト 5 秒、プラットフォーム別アセット選択。Windows・macOS 以外は download_url を空文字列で `update_available` を発行してダウンロードをスキップする）

**Checkpoint**: `pytest tests/unit/test_updater.py -v` がすべてパスすること

---

## Phase 3: User Story 1 — 起動時に新バージョンを通知する（Priority: P1）🎯 MVP

**Goal**: アプリ起動時にバックグラウンドで更新を確認し、新バージョンがある場合はダイアログを表示する

**Independent Test**: `python main.py` 起動後に更新通知ダイアログが表示され（または最新の場合は何も表示されず）、アプリが正常に動作することを確認する

### US1 テスト（テストファースト）

> **NOTE: 以下のテストを先に書き、FAIL することを確認してから実装する**

- [x] T008 [US1] `tests/integration/test_auto_update.py` を作成し、`VideoPlayer` 起動時に `check_update_on_startup=True` の場合 `UpdateChecker.start()` が 1 回だけ呼ばれることのテストを書く（SC-005: 同一セッション中の再通知なしを確認）
- [x] T009 [US1] `tests/integration/test_auto_update.py` に、`check_update_on_startup=False` の場合 `UpdateChecker` が起動しないことのテストを追加する

### US1 実装

- [x] T010 [US1] `looplayer/updater.py` に `DownloadThread(QThread)` を実装する（`progress(int)`・`finished(str)`・`failed(str)` シグナル、`urllib.request.urlretrieve` + reporthook、`isInterruptionRequested()` でキャンセル対応）
- [x] T011 [US1] `looplayer/updater.py` に `DownloadDialog(QDialog)` を実装する（`QProgressBar`・キャンセルボタン・`DownloadThread` との接続・`exec()` によるモーダル表示・完了後にインストーラー起動・`QApplication.instance().quit()` でアプリを終了する。FR-004）
- [x] T012 [US1] `looplayer/player.py` の `__init__` に `AppSettings` から `check_update_on_startup` を読み込んで `UpdateChecker` をバックグラウンド起動する処理を追加する（`update_available` シグナル → `_on_update_available` スロット接続）
- [x] T013 [US1] `looplayer/player.py` に `_on_update_available(version, url)` スロットを実装する（更新通知 `QMessageBox` に「今すぐダウンロード」・「あとで」ボタン、ダイアログ本文は `t("msg.update_available.body").format(current_ver=VERSION, ver=version)` で現在と新バージョン両方を表示（FR-002）。「今すぐ」選択時に `DownloadDialog` を表示）

**Checkpoint**: 手動で `CURRENT_VERSION = "0.0.1"` に変更してアプリ起動、更新通知ダイアログが表示されることを確認

---

## Phase 4: User Story 2 — 手動で更新確認を実行する（Priority: P2）

**Goal**: ヘルプメニューから「更新を確認...」を選択していつでも手動確認できる

**Independent Test**: ヘルプメニュー → 「更新を確認...」を選択し、最新の場合は「最新バージョンです」ダイアログ、新バージョンがある場合は通知ダイアログが表示されることを確認する

### US2 テスト（テストファースト）

> **NOTE: 以下のテストを先に書き、FAIL することを確認してから実装する**

- [x] T014 [US2] `tests/integration/test_auto_update.py` に、ヘルプメニューに「更新を確認...」項目が存在することのテストを追加する
- [x] T015 [US2] `tests/integration/test_auto_update.py` に、手動確認でネットワークエラー時にエラーダイアログが表示されることのテストを追加する（`UpdateChecker.check_failed` シグナルをモック）

### US2 実装

- [x] T016 [US2] `looplayer/player.py` のヘルプメニューに「更新を確認...」(`t("menu.help.check_update")`) アクションを追加する
- [x] T017 [US2] `looplayer/player.py` に `_check_for_updates_manually()` スロットを実装する（`UpdateChecker` を起動し `up_to_date` → 「最新バージョンです」ダイアログ、`check_failed` → エラーダイアログを表示。タイムアウトは起動時と同じ 5 秒で SC-003「10 秒以内」を充足する）

**Checkpoint**: ヘルプメニューから手動確認が動作し、各状態（最新・新バージョン・エラー）に応じた適切なダイアログが表示されることを確認

---

## Phase 5: User Story 3 — 起動時チェックの有効/無効を設定する（Priority: P3）

**Goal**: ヘルプメニューのチェック付き項目で起動時の自動確認を ON/OFF できる

**Independent Test**: チェックを外してアプリを再起動しても更新通知が表示されないことを確認する

### US3 テスト（テストファースト）

> **NOTE: 以下のテストを先に書き、FAIL することを確認してから実装する**

- [x] T018 [US3] `tests/integration/test_auto_update.py` に、ヘルプメニューに「起動時に更新を確認する」チェック付き項目が存在することのテストを追加する
- [x] T019 [US3] `tests/integration/test_auto_update.py` に、チェックを外すと `AppSettings.check_update_on_startup` が `False` に保存されることのテストを追加する

### US3 実装

- [x] T020 [US3] `looplayer/player.py` のヘルプメニューに「起動時に更新を確認する」(`t("menu.help.auto_check")`) チェック付き `QAction` を追加し、`AppSettings` の現在値で初期状態を設定する
- [x] T021 [US3] `looplayer/player.py` に `_toggle_auto_check(checked: bool)` スロットを実装する（`AppSettings.check_update_on_startup = checked` を保存）

**Checkpoint**: `~/.looplayer/settings.json` を確認して `check_update_on_startup` フィールドが正しく保存・読み込みされることを確認

---

## Phase 6: ポリッシュ・横断的関心事

**Purpose**: テスト最終確認・エッジケース対応

- [x] T022 `pytest tests/ -v` を実行してすべてのテスト（322+）がパスすることを確認する
- [x] T023 ダウンロード失敗時のエラーダイアログに「再試行」ボタンを追加し、`DownloadThread` を再起動できるようにする（`looplayer/updater.py` の `DownloadDialog`）

---

## Dependencies（依存関係グラフ）

```
T001 || T002（Setup・並列可）
    ↓
T003 → T004 → T005（テスト・順次: 同一ファイル）
    ↓
T006 → T007（UpdateChecker）
    ↓
Phase 3 (US1): T008, T009 → T010 → T011, T012, T013
    ↓
Phase 4 (US2): T014, T015 → T016, T017
    ↓
Phase 5 (US3): T018, T019 → T020, T021
    ↓
Phase 6 (Polish): T022, T023
```

US2・US3 は US1 の実装（UpdateChecker 起動パターン）に依存するため順次実装する。

---

## Parallel Execution（並列実行の機会）

### Phase 1 内の並列作業

```
Worker A: T001（i18n キー追加）
Worker B: T002（AppSettings 拡張）
```

### Phase 2 内の作業（順次: 同一ファイル）

```
T003 → T004 → T005（tests/unit/test_updater.py を段階的に構築）
```

---

## Implementation Strategy（実装戦略）

### MVP（最小価値製品）= Phase 1 + 2 + 3

- US1 のみで「起動時に新バージョンを通知しダウンロードできる」価値を届けられる
- US2・US3 は US1 完成後に順次追加する

### テストファースト手順（各フェーズ共通）

1. テストを書く
2. テストが FAIL することを確認する（`pytest tests/unit/test_updater.py -v`）
3. 最小限のコードで PASS させる
4. リファクタリング（必要な場合のみ）
5. `pytest tests/ -v` で全テスト通過を確認してからコミット
