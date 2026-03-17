# Tasks: AB Loop Player Improvements

**Input**: Design documents from `/specs/012-player-improvements/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: テストファースト（憲法 I）に従い、各フェーズでテストを先に書いてから実装する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: ユーザーストーリー対応（US1〜US10）

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 全 US が依存する i18n キーを追加する。新規ファイルなし。

- [X] T001 `looplayer/i18n.py` に全 US 分の i18n キーを追加する（`shortcut.set_a`、`shortcut.set_b`、`btn.frame_minus`、`btn.frame_plus`、`label.pause_interval`、`label.play_count`、`btn.reset_play_count`、`label.tags`、`btn.edit_tags`、`menu.file.open_folder`（既存キーの実装確認）、`seq.one_round`、`seq.infinite`、`dialog.export.mode_copy`、`dialog.export.mode_transcode`、`bookmark.save_title`、`bookmark.save_prompt`）

---

## Phase 2: Foundational（全 US が依存する共有コンポーネント）

**Purpose**: データモデル拡張・連続再生モードの型変更。これが揃うまで US の実装を開始しない。

**⚠️ CRITICAL**: Phase 2 完了まで Phase 3 以降を開始しない

- [X] T002 [P] `tests/unit/test_bookmark_store_extensions.py` を作成し `LoopBookmark` の新フィールドテストを書く（`pause_ms` デフォルト 0・最大 10000・旧 JSON 読み込みで 0 補完、`play_count` デフォルト 0・旧 JSON 読み込みで 0 補完、`tags` デフォルト []・旧 JSON 読み込みで [] 補完、`to_dict`/`from_dict` の往復テスト）
- [X] T003 [P] `tests/unit/test_sequential_one_round.py` を作成し `SequentialPlayState` の1周停止テストを書く（`one_round_mode=True` で最終ブックマーク完了時に `on_b_reached()` が `None` を返す、`one_round_mode=False`（デフォルト）では先頭に戻り `int` を返す）
- [X] T004 `looplayer/bookmark_store.py` の `LoopBookmark` dataclass に `pause_ms: int = 0`、`play_count: int = 0`、`tags: list[str] = field(default_factory=list)` を追加し `to_dict`/`from_dict` を更新する。T002 のテストを通過させる
- [X] T005 `looplayer/sequential.py` の `SequentialPlayState` に `one_round_mode: bool = False` フィールドを追加し `on_b_reached()` の戻り値型を `int | None` に変更する（最終ブックマーク完了かつ `one_round_mode=True` のとき `None` を返す）。T003 のテストを通過させる
- [X] T006 `looplayer/app_settings.py` に `sequential_play_mode` プロパティ（`"infinite"` / `"one_round"`、デフォルト `"infinite"`）と `export_encode_mode` プロパティ（`"copy"` / `"transcode"`、デフォルト `"copy"`）を追加する（既存の `@property` パターンを踏襲）

**Checkpoint**: データモデル拡張・SequentialPlayState 型変更が完了し全ユニットテストがパスする

---

## Phase 3: User Story 1 - A/B 点キーボードショートカット (Priority: P1) 🎯 MVP

**Goal**: `I` キーで A 点、`O` キーで B 点をマウスなしで設定できる

**Independent Test**: 動画再生中に `I`/`O` キーを押すと A/B 点が設定される。テキスト入力中は無効。

### テスト（テストファースト）

- [X] T007 [US1] `tests/integration/test_ab_shortcuts.py` を作成し `I`/`O` ショートカットの統合テストを書く（`I` キーで `ab_point_a` がセットされる、`O` キーで `ab_point_b` がセットされる、ショートカット一覧ダイアログに `I`/`O` が表示される）

### 実装

- [X] T008 [US1] `looplayer/player.py` のショートカット設定箇所（424-451 行付近）に `QShortcut` で `Key_I`（A 点セット）・`Key_O`（B 点セット）を `ApplicationShortcut` コンテキストで追加する。T007 のテストを通過させる
- [X] T009 [US1] `looplayer/player.py` の `_show_shortcut_dialog()` にある一覧テーブルに `I` / `O` の説明行を追加する（`t("shortcut.set_a")` / `t("shortcut.set_b")`）

**Checkpoint**: US1 完了 — `I`/`O` ショートカットが動作しテストがパスする

---

## Phase 4: User Story 2 - A/B 点フレーム単位微調整 (Priority: P1)

**Goal**: 全ブックマーク行に A/B 点の +1F / −1F ボタンを常時表示し、フレーム精度で調整できる

**Independent Test**: ブックマーク行の +1F ボタンをクリックすると A/B 点が 1 フレーム分移動し、ストアに即時保存される

### テスト（テストファースト）

- [X] T010 [P] [US2] `tests/unit/test_frame_adjust.py` を作成しフレーム微調整のユニットテストを書く（+1F でフレーム分だけ増加、−1F で減少、A >= B になる微調整を拒否、B が動画長を超えない、fps=0 時は 25fps フォールバック）
- [X] T011 [P] [US2] `tests/integration/test_frame_adjust_integration.py` を作成し統合テストを書く（ブックマーク行の +1F クリックで bookmark_store が更新される、BookmarkRow の `frame_adjusted` シグナルが emit される）

### 実装

- [X] T012 [US2] `looplayer/widgets/bookmark_row.py` に `frame_adjusted = pyqtSignal(str, str, int)` シグナルを追加し、`_build()` レイアウトに A 点の `[−1F][+1F]` / B 点の `[−1F][+1F]` ボタン（4 個）を追加する（A >= B チェックをボタンクリック時に実施）。T010・T011 のテストを通過させる
- [X] T013 [US2] `looplayer/player.py` に `_on_frame_adjusted(bm_id: str, point: str, new_ms: int)` スロットを実装し、各 `BookmarkRow` の `frame_adjusted` シグナルを接続する（`bookmark_store.update_bookmark()` を呼び出してストアに即時保存する）

**Checkpoint**: US2 完了 — フレーム微調整が動作しテストがパスする

---

## Phase 5: User Story 3 - ブックマーク保存時の名前入力 (Priority: P2)

**Goal**: 「ブックマーク保存」実行時に名前入力ポップアップを表示し、1 ステップで名前付き保存できる

**Independent Test**: 「ブックマーク保存」をクリックすると名前入力ダイアログが現れ、Enter で保存・Escape でキャンセルできる

### テスト（テストファースト）

- [X] T014 [US3] `tests/integration/test_bookmark_save_dialog.py` を作成しブックマーク保存ダイアログの統合テストを書く（OK でデフォルト名保存、OK で入力名保存、Cancel でブックマーク追加なし）

### 実装

- [X] T015 [US3] `looplayer/player.py` の `_save_bookmark()` に `QInputDialog.getText()` を追加する（デフォルト名を事前生成して表示、OK → 入力名で保存、Cancel → 保存しない）。T014 のテストを通過させる

**Checkpoint**: US3 完了 — 保存時名前入力が動作しテストがパスする

---

## Phase 6: User Story 4 - ループ間ポーズ (Priority: P2)

**Goal**: B 点到達後に指定秒数だけ停止してから A 点に戻る。スペースキーでポーズをスキップできる

**Independent Test**: `pause_ms=2000` のブックマークでループ中、B 点到達から 2 秒後に A 点から再開する

### テスト（テストファースト）

- [X] T016 [US4] `tests/unit/test_loop_pause.py` を作成しループ間ポーズのユニットテストを書く（`pause_ms=0` で即シーク、`pause_ms>0` で `_pause_timer` が起動する、`_resume_after_pause()` で A 点にシークして再生再開）

### 実装

- [X] T017 [US4] `looplayer/widgets/bookmark_row.py` に `pause_ms_changed = pyqtSignal(str, int)` シグナルと `pause_spin`（`QDoubleSpinBox`、0.0〜10.0 秒、ステップ 0.5）を `_build()` に追加する（値変更時に `pause_ms_changed.emit(id, int(value * 1000))`）
- [X] T018 [US4] `looplayer/player.py` に `_pause_timer: QTimer | None = None` インスタンス変数と `_resume_after_pause()` メソッドを追加する（`_resume_after_pause` は A 点にシーク + `media_player.play()` + `_pause_timer = None`）
- [X] T019 [US4] `looplayer/player.py` の `_on_timer()` B 点到達処理（通常 AB ループ・連続再生の両方）を更新する（`pause_ms > 0` かつ `_pause_timer` が None のとき `media_player.pause()` → `_pause_timer.start(pause_ms)` / `pause_ms == 0` のとき従来通り即シーク）。T016 のテストを通過させる
- [X] T020 [US4] `looplayer/player.py` の `toggle_play()` を更新し、`_pause_timer` がアクティブな場合はポーズをキャンセルして `_resume_after_pause()` を呼ぶ処理を追加する。`_on_frame_adjusted` / ファイル切替時に `_pause_timer` を停止してクリアする

**Checkpoint**: US4 完了 — ループ間ポーズが動作しテストがパスする

---

## Phase 7: User Story 5 - 連続再生1周停止 (Priority: P2)

**Goal**: 連続再生に「1周停止」と「無限ループ」のモードを追加し、設定を永続化する

**Independent Test**: 1周停止モードで全ブックマークを一巡後に連続再生が自動停止する

### テスト（テストファースト）

- [X] T021 [US5] `tests/integration/test_seq_mode.py` を作成し連続再生モードの統合テストを書く（1周停止モードで `_on_timer()` が `None` を受け取り連続再生が終了する、モード選択が `app_settings` に保存される）

### 実装

- [X] T022 [US5] `looplayer/widgets/bookmark_panel.py` の連続再生ボタン付近に「1周停止 / 無限ループ」トグルボタン（`QToolButton` 等）を追加し、選択変更時に `VideoPlayer` へシグナルで通知する
- [X] T023 [US5] `looplayer/player.py` の `_on_timer()` 連続再生処理を更新する（`next_a = state.on_b_reached()` が `None` を返したとき `_stop_seq_play()` を呼ぶ）。T021 のテストを通過させる
- [X] T024 [US5] `looplayer/player.py` に `_on_seq_mode_toggled(one_round: bool)` スロットを実装する（`SequentialPlayState` の `one_round_mode` と `app_settings.sequential_play_mode` を更新する）

**Checkpoint**: US5 完了 — 1周停止モードが動作しテストがパスする

---

## Phase 8: User Story 6 - 練習カウンター (Priority: P3)

**Goal**: B 点到達ごとに再生回数をインクリメントし、ブックマーク行に表示する。アプリ再起動後も保持される

**Independent Test**: ABループで B 点に到達するたびに `play_count` が 1 増え、再起動後も値が保持される

### テスト（テストファースト）

- [X] T025 [P] [US6] `tests/integration/test_play_count.py` を作成し練習カウンターの統合テストを書く（B 点到達で `play_count` が 1 増える、JSON に保存されて再起動後も保持される）
- [X] T026 [P] [US6] `tests/unit/test_play_count_reset.py` を作成し再生回数リセットのユニットテストを書く（`play_count_reset` シグナルで `play_count` が 0 になりストアに保存される）

### 実装

- [X] T027 [US6] `looplayer/widgets/bookmark_row.py` に `play_count_reset = pyqtSignal(str)` シグナルと `play_count` 表示ラベルを `_build()` に追加する（`play_count == 0` のときは薄く表示または非表示、右クリックメニューに「再生回数をリセット」を追加）
- [X] T028 [US6] `looplayer/player.py` の `_on_timer()` B 点到達処理（通常 AB ループ・連続再生の両方）に `store.increment_play_count(bm_id)` の呼び出しを追加する。`_on_play_count_reset(bm_id)` スロットを実装し `BookmarkRow.play_count_reset` シグナルを接続する。T025・T026 のテストを通過させる

**Checkpoint**: US6 完了 — 練習カウンターが動作しテストがパスする

---

## Phase 9: User Story 7 - フォルダを開くメニュー (Priority: P3)

**Goal**: ファイルメニューに「フォルダを開く...」を追加し、ドラッグ&ドロップと同等のプレイリスト読み込みをメニューから実行できる

**Independent Test**: ファイルメニューに「フォルダを開く...」が存在し、選択するとフォルダ内の動画がプレイリストとして読み込まれる

### テスト（テストファースト）

- [X] T029 [US7] `tests/integration/test_folder_menu.py` を作成しフォルダ開きメニューの統合テストを書く（メニュー項目の存在確認、フォルダ選択でプレイリストが読み込まれる、キャンセルで変化なし）

### 実装

- [X] T030 [US7] `looplayer/player.py` の `_build_menus()` に「フォルダを開く...」`QAction`（`t("menu.file.open_folder")`）を「ファイルを開く」の下に追加し、`open_folder()` スロットを実装する（`QFileDialog.getExistingDirectory()` → `_open_folder(path)` と同じ処理）。T029 のテストを通過させる

**Checkpoint**: US7 完了 — フォルダを開くメニューが動作しテストがパスする

---

## Phase 10: User Story 8 - プレイリスト UI パネル (Priority: P3)

**Goal**: プレイリスト読み込み時にファイル一覧パネルを表示し、ファイルクリックや `Alt+←/→` でファイルを切り替えられる

**Independent Test**: フォルダドロップ後にプレイリストパネルが表示され、クリックでファイルが切り替わる

### テスト（テストファースト）

- [X] T031 [US8] `tests/integration/test_playlist_ui.py` を作成しプレイリスト UI の統合テストを書く（プレイリスト読み込み後にパネルが表示される、ファイルクリックで `file_requested` シグナルが emit される、`Alt+→` で次ファイルへ、`Alt+←` で前ファイルへ、プレイリストなし時にパネルが非表示）

### 実装

- [X] T032 [US8] `looplayer/widgets/playlist_panel.py` を新規作成する（`PlaylistPanel(QWidget)`、`file_requested = pyqtSignal(str)` シグナル、`QListWidget` でファイル名一覧表示、`set_playlist(playlist | None)` で表示切替、`update_current(path)` でハイライト更新）
- [X] T033 [US8] `looplayer/playlist.py` に `retreat()` メソッドを追加する（`index` を 0 以上の範囲でデクリメント）
- [X] T034 [US8] `looplayer/player.py` の右パネルを `QTabWidget`（タブ1「ブックマーク」+ タブ2「プレイリスト」）に変更し、`PlaylistPanel` を接続する（プレイリストなし時はタブ2 を非表示）
- [X] T035 [US8] `looplayer/player.py` のショートカット設定箇所に `Alt+→`（次ファイル）・`Alt+←`（前ファイル）の `QShortcut` を追加する（`_playlist_next()` / `_playlist_prev()` スロットを実装）。T031 のテストを通過させる

**Checkpoint**: US8 完了 — プレイリスト UI が動作しテストがパスする

---

## Phase 11: User Story 9 - ブックマークタグ付け (Priority: P4)

**Goal**: ブックマークにタグを付け、OR フィルタで絞り込んで表示・連続再生できる

**Independent Test**: タグを入力したブックマークがタグフィルタで正しく絞り込まれ、連続再生もフィルタ結果のみを対象とする

### テスト（テストファースト）

- [X] T036 [P] [US9] `tests/unit/test_bookmark_tags.py` を作成しタグ機能のユニットテストを書く（タグの JSON 保存・読み込み、OR フィルタロジック（選択タグのいずれかを持つブックマークを返す）、空フィルタで全件返す、タグのトリム・空文字除去）
- [X] T037 [P] [US9] `tests/integration/test_tag_filter_integration.py` を作成しタグフィルタ UI の統合テストを書く（タグ編集シグナルで bookmark_store が更新される、タグフィルタで BookmarkPanel の表示件数が変わる、フィルタ中の連続再生が対象ブックマークのみ）

### 実装

- [X] T038 [US9] `looplayer/widgets/bookmark_row.py` に `tags_changed = pyqtSignal(str, list)` シグナルとタグ表示ラベル + タグ編集ボタン（🏷）を `_build()` に追加する（クリック時に `QInputDialog.getText()` でカンマ区切り入力、パース後に `tags_changed.emit()`）
- [X] T039 [US9] `looplayer/widgets/bookmark_panel.py` にタグフィルタ UI（使用タグ一覧の `QListWidget` または複数選択対応 `QComboBox` 系 UI）と `_active_tag_filter: list[str] = []` を追加する（フィルタ変更時に `_refresh_list()` を呼び直し、連続再生の `enabled_bms` フィルタにも OR 条件を適用する）。T036・T037 のテストを通過させる

**Checkpoint**: US9 完了 — タグ付け・フィルタリングが動作しテストがパスする

---

## Phase 12: User Story 10 - クリップ書き出しトランスコード (Priority: P4)

**Goal**: クリップ書き出しに「高速（コピー）」と「正確（H.264 再エンコード）」の 2 モードを追加する

**Independent Test**: トランスコードモードで書き出すと `-c:v libx264 -c:a aac` が使われ、選択が次回も維持される

### テスト（テストファースト）

- [X] T040 [P] [US10] `tests/unit/test_transcode_export.py` を作成しエンコードモードのユニットテストを書く（`encode_mode="copy"` で `-c copy` コマンド生成、`encode_mode="transcode"` で `-c:v libx264 -c:a aac -crf 23` コマンド生成、`finished` / `failed` シグナルのテスト）
- [X] T041 [P] [US10] `tests/integration/test_transcode_dialog.py` を作成しダイアログ UI の統合テストを書く（ラジオボタンの存在確認、デフォルトが copy、選択が `app_settings` に保存される）

### 実装

- [X] T042 [US10] `looplayer/clip_export.py` の `ClipExportJob` に `encode_mode: str = "copy"` フィールドを追加し `ExportWorker.run()` の ffmpeg コマンド生成を分岐させる（`"copy"` → `-c copy` / `"transcode"` → `-c:v libx264 -c:a aac -crf 23`）。T040 のテストを通過させる
- [X] T043 [US10] `looplayer/widgets/export_dialog.py` に「高速（ストリームコピー）」と「正確（再エンコード・H.264）」の `QRadioButton` を追加し、初期値を `app_settings.export_encode_mode` から読み込み、`exec()` 内で選択を `ClipExportJob.encode_mode` にセットし `app_settings` に保存する。T041 のテストを通過させる

**Checkpoint**: US10 完了 — トランスコード書き出しが動作しテストがパスする

---

## Phase 13: Polish & Cross-Cutting Concerns

- [X] T044 [P] 全新規テストを実行して全件パスすることを確認する: `pytest tests/unit/test_bookmark_store_extensions.py tests/unit/test_sequential_one_round.py tests/unit/test_frame_adjust.py tests/unit/test_loop_pause.py tests/unit/test_bookmark_tags.py tests/unit/test_transcode_export.py -v`
- [X] T045 [P] 全統合テストを実行して回帰がないことを確認する: `pytest tests/integration/ -v`
- [X] T046 既存テスト 340 件を含む全テストスイートを実行して回帰がないことを確認する: `pytest tests/ -v`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし — 即開始可能
- **Phase 2 (Foundational)**: Phase 1 完了後 — Phase 3〜12 をブロック
- **Phase 3 (US1)**: Phase 2 完了後 — 他 US と並列可能
- **Phase 4 (US2)**: Phase 2 完了後 — US1 と並列可能
- **Phase 5 (US3)**: Phase 2 完了後 — US1/US2 と並列可能
- **Phase 6 (US4)**: Phase 2 完了後 — US1/US2/US3 と並列可能
- **Phase 7 (US5)**: Phase 2 完了後（T005 依存）
- **Phase 8 (US6)**: Phase 2 完了後（T004 の play_count フィールド依存）
- **Phase 9 (US7)**: Phase 2 完了後（T001 の i18n キー依存）
- **Phase 10 (US8)**: Phase 2 完了後（T005 の Playlist.retreat 依存）
- **Phase 11 (US9)**: Phase 2 完了後（T004 の tags フィールド依存）
- **Phase 12 (US10)**: Phase 2 完了後（T006 の AppSettings 依存）
- **Phase 13 (Polish)**: Phase 3〜12 完了後

### Parallel Opportunities

```bash
# Phase 2 内（異なるファイル）:
T002: LoopBookmark 拡張テスト（test_bookmark_store_extensions.py）
T003: SequentialPlayState テスト（test_sequential_one_round.py）

# Phase 3〜12 は Phase 2 完了後に並列開始可能（P1 → P2 → P3 → P4 の優先順）:
Phase 3 (US1): T007 → T008 → T009
Phase 4 (US2): T010/T011 → T012 → T013
Phase 5 (US3): T014 → T015
Phase 6 (US4): T016 → T017/T018 → T019 → T020
Phase 7 (US5): T021 → T022 → T023 → T024

# Phase 8〜12 は US6〜US10 を並列実行可能:
Phase 8 (US6):  T025/T026 → T027 → T028
Phase 9 (US7):  T029 → T030
Phase 10 (US8): T031 → T032/T033 → T034 → T035
Phase 11 (US9): T036/T037 → T038 → T039
Phase 12 (US10):T040/T041 → T042 → T043
```

---

## Implementation Strategy

### MVP First（US1 + US2 のみ）

1. Phase 1: T001（i18n キー）
2. Phase 2: T002 → T004 → T003 → T005 → T006
3. Phase 3 (US1): T007 → T008 → T009
4. Phase 4 (US2): T010/T011 → T012 → T013
5. **STOP & VALIDATE**: `pytest tests/unit/test_frame_adjust.py tests/integration/test_ab_shortcuts.py -v`
6. マウスレス AB ループ操作が独立して動作することを確認

### Incremental Delivery

1. Phase 1 + 2 → 基盤完成
2. Phase 3 + 4 (US1 + US2) → P1 MVP: キーボード中心の AB ループ
3. Phase 5 + 6 + 7 (US3〜5) → P2: 保存フロー・ポーズ・1周停止
4. Phase 8〜10 (US6〜8) → P3: カウンター・フォルダメニュー・プレイリスト UI
5. Phase 11〜12 (US9〜10) → P4: タグ・トランスコード
6. Phase 13 → 全体検証

---

## Notes

- テストファースト必須（憲法 I）: 各フェーズでテストを書いて失敗確認してから実装
- [P] タスク = 異なるファイルまたは内容が独立
- `_pause_timer` は `QTimer.singleShot` ではなく `QTimer` インスタンスを保持（スペースキーキャンセルのため）
- `BookmarkPanel` のタブ切り替えで `QTabWidget` を使う（PlaylistPanel は非表示時にタブを隠す）
- タグフィルタは BookmarkPanel 内で完結（VideoPlayer への変更不要）
- `Playlist.retreat()` は `index` を `max(0, index - 1)` にデクリメント
