# Tasks: プレイヤー機能強化

**Input**: Design documents from `/specs/007-player-enhancements/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Constitution I（テストファースト）**: 各 US の実装前にテストを作成し、失敗することを確認してから実装する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1〜US7）

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 全 US で使用するフィードバック基盤の追加

- [X] T001 `looplayer/player.py` の `_build_ui()` 末尾に `self.statusBar()` を呼び出して QStatusBar を初期化し、フルスクリーン切替（`_toggle_fullscreen`）で `self.statusBar().hide()/show()` を追加する

---

## Phase 2: Foundational（全 US の前提条件）

**Purpose**: ブックマークデータモデルの変更（US6 だけでなく既存ブックマーク機能全体に影響するため先行実施）

**⚠️ CRITICAL**: このフェーズ完了前にブックマーク関連 US を開始しない

- [X] T002a `tests/unit/test_bookmark_notes.py` に `LoopBookmark` の `notes` フィールドのテストを事前追加する（デフォルト値が `""`、旧 JSON（notes キーなし）からの読み込みで `""` にフォールバックすること）。このテストは T002 実装前に **失敗する** ことを確認する（Constitution I 対応）
- [X] T002 `looplayer/bookmark_store.py` の `LoopBookmark` データクラスに `notes: str = ""` フィールドを追加し、`_load_all()` のデシリアライズ箇所に `notes=raw.get("notes", "")` を追加して後方互換性を確保する
- [X] T003 [P] `looplayer/bookmark_io.py` の `export_bookmarks()` で各ブックマーク辞書に `"notes": bm.notes` を追加し、`import_bookmarks()` の重複チェックロジックに `notes` を含めてデシリアライズできるよう修正する

**Checkpoint**: ブックマーク永続化が notes フィールドに対応 → US6 の実装が可能

---

## Phase 3: User Story 1 - 精細な再生操作 (Priority: P1) 🎯 MVP

**Goal**: キーボードのみでフレームコマ送り・±1/10秒シーク・速度段階変更が完結する

**Independent Test**: 動画ファイルを開き `.` `,` `Shift+←→` `Ctrl+←→` `[` `]` を順に押してすべて期待通りに動作することを手動確認できる

> **⚠️ テストファースト**: T004 を先に書いて失敗させてから T005〜T007 を実装する

- [X] T004 [US1] `tests/unit/test_playback_speed.py` に速度ショートカットのユニットテスト（`_speed_up`・`_speed_down` で速度リストの境界動作）を追記する
- [X] T005 [P] [US1] `looplayer/player.py` に `_PLAYBACK_RATES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]` クラス定数を定義し、`_speed_up()` / `_speed_down()` メソッドを実装して `QShortcut("]")` / `QShortcut("[")` に接続する。速度の端では `self.statusBar().showMessage("最大速度です", 2000)` / `"最小速度です"` を表示する
- [X] T006 [P] [US1] `looplayer/player.py` に `Shift+Right` / `Shift+Left` で `_seek_relative(1000)` / `_seek_relative(-1000)` を呼ぶ `QShortcut` を追加し、`Ctrl+Right` / `Ctrl+Left` で `±10000ms` シークを追加する
- [X] T007 [US1] `looplayer/player.py` に `_frame_forward()` / `_frame_backward()` を実装し `QShortcut(".")` / `QShortcut(",")` に接続する。再生中の場合は `self.media_player.pause()` してからフレーム操作する。後退は `get_fps()` を使用し、0以下の場合は 25fps（40ms）にフォールバックする
- [X] T008 [US1] `looplayer/player.py` の `_show_shortcuts()` に US1 の新規ショートカット（`.` `,` `Shift+←→` `Ctrl+←→` `[` `]`）を追記する

**Checkpoint**: US1 の全ショートカットが動作し、ショートカット一覧ダイアログに表示されること

---

## Phase 4: User Story 2 - マルチトラック対応（音声・字幕） (Priority: P2)

**Goal**: 複数音声・字幕トラックを持つ動画でメニューからトラックを切り替えられる

**Independent Test**: 複数音声トラックを持つ MKV ファイルを開き「再生 → 音声トラック」メニューで切り替えが動作することを確認

> **⚠️ テストファースト**: T009 を先に書いて失敗させてから T010〜T011 を実装する

- [X] T009 [US2] `tests/integration/test_player_enhancements.py` を新規作成し、音声・字幕トラックメニューの存在チェック（`QAction` 数の確認）テストを追加する
- [X] T010 [US2] `looplayer/player.py` の `_build_menu()` に `self._audio_track_menu` サブメニューを追加し、`aboutToShow` シグナルで `_rebuild_audio_track_menu()` を呼ぶよう実装する。`_rebuild_audio_track_menu()` は `audio_get_track_description()` で一覧取得し、`QActionGroup` で排他選択・現在選択にチェックマークを付ける。トラックが1種類以下の場合はメニューをグレーアウトする
- [X] T011 [US2] `looplayer/player.py` に `self._subtitle_menu` サブメニューを追加し `_rebuild_subtitle_menu()` を実装する。「字幕なし」オプション（`video_set_spu(-1)`）を先頭に追加し、`video_get_spu_description()` でトラック一覧を構築する。`_open_path()` の動画ロード後にメニューをリセット（空 + グレーアウト）する

**Checkpoint**: 複数トラック動画でのメニュー表示・切り替えが動作すること

---

## Phase 5: User Story 3 - スクリーンショット保存 (Priority: P3)

**Goal**: `Ctrl+Shift+S` またはメニューで現在フレームをデスクトップに PNG 保存できる

**Independent Test**: 動画を一時停止して `Ctrl+Shift+S` を押し、デスクトップに `LoopPlayer_*.png` ファイルが保存され、ステータスバーにパスが表示されること

> **⚠️ テストファースト**: T012 を先に書いて失敗させてから T013 を実装する

- [X] T012 [US3] `tests/integration/test_player_enhancements.py` にスクリーンショット機能のテスト（メニュー項目の存在、動画未ロード時のグレーアウト確認）を追加する
- [X] T013 [US3] `looplayer/player.py` に `_take_screenshot()` を実装する。`Path.home() / "Desktop"` が存在すればそこに、なければ `Path.home()` に `LoopPlayer_YYYYMMDD_HHMMSS.png` として `media_player.video_take_snapshot(0, str(path), 0, 0)` で保存し、完了後 `self.statusBar().showMessage(f"保存しました: {path}", 3000)` を表示する。ファイルメニューに「スクリーンショット(&P)」を `Ctrl+Shift+S` ショートカット付きで追加し、動画未ロード時はグレーアウトする
- [X] T014 [US3] `looplayer/player.py` の `_show_shortcuts()` に `Ctrl+Shift+S`（スクリーンショット）を追記する

**Checkpoint**: スクリーンショットがデスクトップに保存されステータスバーに通知されること

---

## Phase 6: User Story 4 - 再生終了時の自動動作 (Priority: P4)

**Goal**: 動画終端到達時の動作（停止・先頭に戻る・ループ）を設定・永続化できる

**Independent Test**: `AppSettings` のユニットテストが通り、「ループ再生」設定で動画を最後まで再生すると先頭から自動再生されること

> **⚠️ テストファースト**: T015 を先に書いて失敗させてから T016〜T018 を実装する

- [X] T015 [US4] `tests/unit/test_app_settings.py` を新規作成し、`AppSettings` の読み書き・デフォルト値・不正値フォールバック・アトミック保存のユニットテストを実装する
- [X] T016 [US4] `looplayer/app_settings.py` を新規作成する。`~/.looplayer/settings.json` に `{"end_of_playback_action": "stop"}` を保存・読み込みし、アトミック書き込みパターン（`.tmp` → rename）を使用する。`end_of_playback_action` プロパティに setter で即時保存する
- [X] T017 [US4] `looplayer/player.py` に `self._app_settings = AppSettings()` を初期化し、`_error_occurred` と同じパターンで `_playback_ended = pyqtSignal()` を追加して `MediaPlayerEndReached` イベントに購読する。`_handle_playback_ended()` では ABループ有効時・連続再生有効時はスキップし、`end_of_playback_action` に従って stop/rewind/loop を実行する
- [X] T018 [US4] `looplayer/player.py` の `_build_menu()` 再生メニューに「再生終了時の動作(&E)」サブメニューを追加し、「停止」「先頭に戻る」「ループ再生」の3択を `QActionGroup` で排他選択として実装する。選択変更時に `app_settings.end_of_playback_action` を更新する。起動時に保存済み設定をチェックマーク反映する

**Checkpoint**: `test_app_settings.py` がパスし、再生終了動作設定がアプリ再起動後も維持されること

---

## Phase 7: User Story 5 - 再生位置の記憶と復元 (Priority: P5)

**Goal**: 同じファイルを再度開くと前回の再生位置から一時停止状態で再開される

**Independent Test**: `PlaybackPosition` のユニットテストが通り、動画を途中まで再生してから同じファイルを開くと前回位置から再開されること

> **⚠️ テストファースト**: T019 を先に書いて失敗させてから T020〜T021 を実装する

- [X] T019 [US5] `tests/unit/test_playback_position.py` を新規作成し、`save()` / `load()` の基本動作・95%以上リセット・5秒未満保存スキップ・10件上限・ファイル不在のハンドリングのユニットテストを実装する
- [X] T020 [US5] `looplayer/playback_position.py` を新規作成する。`~/.looplayer/positions.json` に `{filepath: position_ms}` を保存・読み込みし、上限10件を dict 挿入順で管理する。`save()` は 5000ms 未満・95% 以上の場合はスキップ（または削除）し、アトミック書き込みパターンを使用する
- [X] T021 [US5] `looplayer/player.py` に `self._playback_position = PlaybackPosition()` を初期化し、`_open_path()` 内でファイルロード後に `load()` した位置があれば `set_time()` で復元する。別ファイルを開く直前・`closeEvent()` で `save()` を呼び出す

**Checkpoint**: `test_playback_position.py` がパスし、動画を途中で閉じて再度開くと前回位置から再開されること

---

## Phase 8: User Story 6 - ブックマークへのメモ追加 (Priority: P6)

**Goal**: 各ブックマーク行にメモアイコンを追加し、テキストメモを入力・保存・表示できる

**Independent Test**: ブックマークを作成してメモアイコンをクリックし、テキスト入力後に保存、再クリックで内容が表示され、`bookmarks.json` に `notes` フィールドが保存されること

> **⚠️ テストファースト**: T022 を先に書いて失敗させてから T023〜T024 を実装する（T002 完了が前提）

- [X] T022 [US6] `tests/unit/test_bookmark_notes.py` を新規作成し、`LoopBookmark.notes` フィールドのデフォルト値・保存・復元・旧 JSON（notes なし）からのフォールバック読み込みのユニットテストを実装する
- [X] T023 [US6] `looplayer/widgets/bookmark_row.py` に `memo_clicked = pyqtSignal(str)` シグナルを追加し、メモアイコンボタン（`QPushButton("✎")`、24×24px）をレイアウトに追加する。メモが存在する場合はボタンのツールチップに内容を表示してスタイルを変更（例: フォントを太字）し、空の場合は通常スタイルにする。ボタンクリックで `memo_clicked.emit(self.bookmark_id)` を発火する
- [X] T024 [US6] `looplayer/widgets/bookmark_panel.py` で `BookmarkRow.memo_clicked` シグナルに `_on_memo_clicked(bookmark_id: str)` スロットを接続する。`_on_memo_clicked` では対象ブックマークを取得し `QInputDialog.getMultiLineText()` でメモを表示・編集し、保存時に `BookmarkStore.update_notes(bookmark_id, text)` を呼ぶ。`BookmarkStore` に `update_notes()` メソッドを追加する

**Checkpoint**: メモの入力・保存・再表示が動作し、エクスポート JSON に `notes` フィールドが含まれること

---

## Phase 9: User Story 7 - フォルダドロップでプレイリスト (Priority: P7)

**Goal**: フォルダをドロップすると動画をファイル名順に自動順再生する

**Independent Test**: `Playlist` のユニットテストが通り、複数動画を含むフォルダをドロップすると最初のファイルが再生され終了後に次に進むこと

> **⚠️ テストファースト**: T025 を先に書いて失敗させてから T026〜T028 を実装する（T017 の `_handle_playback_ended` 完了が前提）

- [X] T025 [US7] `tests/unit/test_playlist.py` を新規作成し、`Playlist` の `current()` / `advance()` / `has_next()` / `__len__()` の動作・境界値（1ファイル・最後のファイル終了後）のユニットテストを実装する
- [X] T026 [US7] `looplayer/playlist.py` を新規作成する。`Playlist` データクラスに `files: list[Path]`・`index: int = 0` を持たせ、`current()` / `advance()` / `has_next()` / `__len__()` を実装する
- [X] T027 [US7] `looplayer/player.py` の `dropEvent()` を拡張し、ドロップ対象がディレクトリの場合に `_open_folder(folder: Path)` を呼ぶ。`_open_folder()` は隠しファイル除外・1階層のみ・ファイル名昇順で動画ファイルをリストアップし、0件の場合は警告ダイアログ、1件の場合は `self._playlist = None` で単体再生、2件以上の場合は `Playlist` を生成して `_open_path()` で最初のファイルを開く。単一ファイルを開いた場合は `self._playlist = None` でリセットする
- [X] T028 [US7] `looplayer/player.py` の `_handle_playback_ended()` （T017 で実装済み）にプレイリスト自動進行ロジックを追加する。`self._playlist` が存在し `has_next()` が True の場合は `advance()` して次のファイルを `_open_path()` で開き、`has_next()` が False の場合は再生停止のみ行う

**Checkpoint**: `test_playlist.py` がパスし、フォルダドロップで自動順再生が動作すること

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 全 US を横断する品質確認と仕上げ

- [X] T029 [P] `looplayer/player.py` の `_show_shortcuts()` を確認し、US1〜US3 で追加したすべてのショートカット（`.` `,` `Shift+←→` `Ctrl+←→` `[` `]` `Ctrl+Shift+S`）が漏れなく記載されていることを確認・修正する
- [X] T030 `quickstart.md` のテスト手順（US1〜US7）に従って手動統合テストを実施し、各 Success Criteria（SC-001〜SC-008）を確認する。問題があれば該当タスクに戻って修正する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし。即時開始可能
- **Foundational (Phase 2)**: Phase 1 完了後。**全 US をブロック**（特に US6）
- **US1 (Phase 3)**: Phase 1 完了後（QStatusBar が前提）。他 US と並列可能
- **US2 (Phase 4)**: Phase 1 完了後。US1 と並列可能
- **US3 (Phase 5)**: Phase 1 完了後（statusBar が前提）。US1/US2 と並列可能
- **US4 (Phase 6)**: Phase 1 完了後。US7 の `_handle_playback_ended` が US4 の実装に依存
- **US5 (Phase 7)**: Phase 1 完了後。他 US と並列可能
- **US6 (Phase 8)**: Phase 2 完了後（notes フィールドが前提）
- **US7 (Phase 9)**: Phase 6 完了後（`_handle_playback_ended` の実装が前提）
- **Polish (Phase 10)**: US1〜US7 完了後

### Critical Path

```
Phase 1 (T001) → US4 (T015-T018) → US7 (T025-T028) → Polish
             ↘ US1, US2, US3, US5 (並列可能)
Phase 2 (T002-T003) → US6 (T022-T024)
```

### Parallel Opportunities

- T005, T006 は同一フェーズ内で異なる機能のため並列実装可能
- T002, T003 はそれぞれ異なるファイルのため並列実装可能
- US1・US2・US3・US5 は互いに独立しており並列実装可能
- US4 と US6 は独立して並列実装可能

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1 (T001) を完了
2. Phase 3 (T004〜T008) を完了
3. **STOP & VALIDATE**: キーボードのみでコマ送り・精細シーク・速度変更が完結することを確認
4. 追加 US を順次実装

### Incremental Delivery

1. Phase 1 + Phase 3 → US1（コマ送り・精細シーク・速度ショートカット）
2. + Phase 4 → US2（マルチトラック）
3. + Phase 5 → US3（スクリーンショット）
4. + Phase 6 → US4（再生終了動作）
5. + Phase 2 + Phase 8 → US6（ブックマークメモ）
6. + Phase 7 → US5（再生位置記憶）
7. + Phase 9 → US7（フォルダドロップ）
8. Phase 10（Polish）

---

## Notes

- Constitution I（テストファースト）に従い、各 US のテストタスクを実装タスクの前に実施し、テストが **失敗する** ことを確認してから実装を開始する
- `[P]` タスクは異なるファイルを対象とするため並列実行可能
- `player.py` への変更が集中するため、同一フェーズ内の `player.py` 変更タスクは逐次実施すること
- 各フェーズのチェックポイントで `pytest tests/ -v` を実行してリグレッションがないことを確認する
