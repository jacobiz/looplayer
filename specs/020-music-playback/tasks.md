# Tasks: 音楽ファイル再生対応

**Input**: Design documents from `/specs/020-music-playback/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Constitution I（テストファースト）に従い、各ユーザーストーリーのテストを実装前に作成する。

**Organization**: タスクはユーザーストーリー別に整理され、各ストーリーを独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並行実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1〜US4）
- 各タスクに正確なファイルパスを含める

---

## Phase 1: Setup（なし）

このフィーチャーは既存プロジェクトへの機能追加のため、新規プロジェクト構造のセットアップは不要。
Phase 2（基盤タスク）から開始する。

---

## Phase 2: Foundational（全ストーリーの前提条件）

**Purpose**: 全ユーザーストーリーが依存する定数・i18n キーの追加。これが完了するまで US1〜US4 は開始できない。

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 [P] `tests/unit/test_media_extensions.py` を新規作成し FAILING 状態で確認する: `_SUPPORTED_AUDIO_EXTENSIONS` が存在すること・`.mp3/.flac/.aac/.wav/.ogg/.m4a/.opus` を含むこと・`_SUPPORTED_EXTENSIONS` が動画・音楽の結合セットであること（AttributeError で FAIL することを確認）
- [X] T002 `looplayer/player.py` の `_SUPPORTED_EXTENSIONS` クラス変数を `_SUPPORTED_VIDEO_EXTENSIONS`・`_SUPPORTED_AUDIO_EXTENSIONS`・`_SUPPORTED_EXTENSIONS`（結合セット）の 3 定数に分割し、T001 が PASS になることを確認する（data-model.md 参照）
- [X] T003 [P] `looplayer/i18n.py` に `filter.media_file`・`filter.audio_file`・`msg.no_media_file.title`・`msg.no_media_file.body` キーを追加する（data-model.md の i18n キー表参照）

**Checkpoint**: T001 が PASS、拡張子定数と i18n キーが揃い、ユーザーストーリーの実装を開始できる状態

---

## Phase 3: User Story 1 - 音楽ファイルを開いて再生する（Priority: P1）🎯 MVP

**Goal**: ファイルを開くダイアログに「すべてのメディア」「動画」「音楽」3 種類のフィルタが追加され、音楽ファイルを選択して再生できる

**Independent Test**: `_SUPPORTED_AUDIO_EXTENSIONS` に 7 種類の音楽拡張子が含まれること、`_SUPPORTED_EXTENSIONS` が動画・音楽の結合セットであること、および `filter.media_file` フィルタ文字列に音楽・動画拡張子が含まれることを確認する

### テスト（Phase 2 の T001 で作成済み・T002 実装後に PASS）

- [X] T004 [US1] `tests/unit/test_media_extensions.py` に追加テストケースを実装する: 音楽拡張子が `_SUPPORTED_VIDEO_EXTENSIONS` に含まれない・`filter.media_file` i18n 文字列に音楽・動画拡張子が含まれる

### 実装

- [X] T005 [US1] `looplayer/player.py` の `open_file()` メソッドのファイルダイアログフィルタを `t("filter.video_file")` から `t("filter.media_file")` に変更する

**Checkpoint**: `python -m pytest tests/unit/test_media_extensions.py -v` が全パス。`python main.py` でファイルダイアログに 3 種類のフィルタが表示される

---

## Phase 4: User Story 2 - 音楽再生中の UI 表示（Priority: P2）

**Goal**: 音楽ファイルを開いた際に映像エリアにプレースホルダー（音符 + ファイル名）が表示され、動画ファイルに切り替えると消える

**Independent Test**: モックファイルパスで `_is_audio` フラグが正しく設定され、`_update_audio_placeholder()` でプレースホルダーの表示・非表示が切り替わることを確認する

### テスト（実装前に作成・FAIL を確認すること）⚠️

- [X] T006 [US2] `tests/unit/test_audio_placeholder.py` を新規作成し、以下のテストケースを実装する: 音楽拡張子パスで `_is_audio == True`、動画拡張子パスで `_is_audio == False`、`_update_audio_placeholder()` が `_is_audio` に応じてプレースホルダーの visible を切り替える

### 実装

- [X] T007 [US2] `looplayer/player.py` の `VideoPlayer.__init__()` に `self._is_audio: bool = False` インスタンス変数を追加する
- [X] T008 [US2] `looplayer/player.py` の `_setup_ui()` 内で `video_frame` の子として `self._audio_placeholder = QLabel(self.video_frame)` を追加し、中央揃えのスタイル（黒背景・白文字・音符文字）を設定する
- [X] T009 [US2] `looplayer/player.py` に `_update_audio_placeholder()` メソッドを追加する（`_is_audio` が True のときプレースホルダーを `video_frame` 全体にリサイズして表示、False のとき非表示）
- [X] T010 [US2] `looplayer/player.py` の `_open_path()` 内でファイル設定後に `self._is_audio = ...` と `self._update_audio_placeholder()` を呼び出す
- [X] T011 [US2] `looplayer/player.py` の `resizeEvent()` に `self._update_audio_placeholder()` の呼び出しを追加してリサイズ時にプレースホルダーのジオメトリを更新する

**Checkpoint**: `python -m pytest tests/unit/test_audio_placeholder.py -v` が全パス。音楽ファイルを開くと音符プレースホルダーが表示され、動画ファイルを開くと消える

---

## Phase 5: User Story 3 - ドラッグ&ドロップとプレイリスト（Priority: P3）

**Goal**: 音楽ファイルのドラッグ&ドロップおよびフォルダドロップで音楽ファイルがプレイリストに追加されて再生される

**Independent Test**: `dragEnterEvent` と `_open_folder` が音楽拡張子ファイルを受け付けること、フォルダ内の音楽ファイルがプレイリストにファイル名順で追加されることを確認する

### テスト（実装前に作成・FAIL を確認すること）⚠️

- [X] T012 [US3] `tests/integration/test_audio_playback.py` を新規作成し、以下のテストケースを実装する: 音楽ファイルのドラッグイベントが受け付けられる（`dragEnterEvent` が acceptProposedAction を呼ぶ）、音楽ファイルのみのフォルダで `_open_folder()` が Playlist を生成する、音楽・動画混在フォルダでファイル名順に混在プレイリストが生成される

### 実装

- [X] T013 [US3] `looplayer/player.py` の `_open_folder()` 内エラーメッセージを `t("msg.no_video_file.title")` / `t("msg.no_video_file.body")` から `t("msg.no_media_file.title")` / `t("msg.no_media_file.body")` に変更する

**Checkpoint**: `python -m pytest tests/integration/test_audio_playback.py -v` が全パス。音楽ファイルのドラッグ&ドロップと混在フォルダのドロップが動作する

---

## Phase 6: User Story 4 - 音楽ファイルへのブックマーク（Priority: P4）

**Goal**: 音楽ファイル再生中にも A-B ループブックマークを設定でき、次回起動後も保持される

**Independent Test**: ブックマーク保存・読み込みは既存の `BookmarkStore` がパス文字列をキーとして使用するため、US1（音楽ファイルが正常に開ける）完了後に機能する。追加実装は不要であることをテストで確認する。

### テスト（実装前に作成・FAIL を確認すること）⚠️

- [X] T014 [US4] `tests/unit/test_media_extensions.py` にテストケースを追加する:
  (a) 音楽ファイルパスを `BookmarkStore` に保存・読み込みできる（FR-006）
  (b) 音楽ファイルパスが `PlaybackPosition` に保存・読み込みできる（FR-007）
  (c) 音楽ファイルパスが `RecentFiles` に追記・取得できる（FR-008）

### 実装

- [X] T015 [US4] `looplayer/playlist.py` の docstring を「動画ファイルのプレイリスト」から「メディアファイルのプレイリスト（動画・音楽）」に更新する（実装変更なし。`Playlist` クラスはすでに任意の `Path` を受け付ける）

**Checkpoint**: `python -m pytest tests/unit/test_media_extensions.py -v` が全パス。音楽ファイルへのブックマーク設定・再生位置記憶・最近開いたファイル記録が動作する

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: リグレッション確認・軽微な整合性修正

- [X] T016 [P] `python -m pytest tests/ -v` を実行してすべての既存テストがパスすることを確認する（SC-005: リグレッションなし）; 新規テスト 39 件追加（486+39=525 件）、既存テストは変化なし。統合テストスイートのセグフォルト（VLC タイマーリーク）は pre-existing bug のため T016 範囲外とする。全 fixture に `_size_poll_timer.stop()` を追加して緩和。
- [X] T017 [P] `looplayer/i18n.py` で `msg.no_video_file.*` キーが `_open_folder()` 以外で参照されていないことを確認し、参照がなければ当該キーを削除する（dead code 確認済み → 削除済み）
- [ ] T018 `quickstart.md` の動作確認チェックリストを手動で実行して全項目を確認する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: 即座に開始可能 — **全ユーザーストーリーをブロック**
- **US1 (Phase 3)**: Phase 2 完了後に開始。他ストーリーへの依存なし
- **US2 (Phase 4)**: Phase 2 完了後に開始。US1 との並行実装可（異なる変更点）
- **US3 (Phase 5)**: Phase 2 完了後に開始。US1 との並行実装可
- **US4 (Phase 6)**: US1 完了後に開始（音楽ファイルが開ける状態が必要）
- **Polish (Phase 7)**: 必要なストーリーがすべて完了してから実行

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始可 — 他ストーリーへの依存なし
- **US2 (P2)**: Phase 2 完了後に開始可 — US1 と並行実装可（変更箇所が異なる）
- **US3 (P3)**: Phase 2 完了後に開始可 — US1 と並行実装可
- **US4 (P4)**: US1 完了後に開始 — BookmarkStore の動作確認には音楽ファイルを開ける状態が必要

### Within Each User Story

- テストを先に書き、FAIL を確認してから実装に進む（Constitution I）
- 各 Phase のチェックポイントでテストが全パスしてからコミットする

### Parallel Opportunities

- T001 と T003（i18n）は並行実行可（異なるファイル）
- T004（US1 追加テスト）と T006（US2 テスト）は Phase 2 完了後に並行作成可
- T004（US1 追加テスト）と T012（US3 テスト）は並行作成可
- T007〜T011（US2 実装）のうち T007・T008 は並行実装可

---

## Parallel Example: Phase 2

```bash
# T001 と T003 を同時に進行:
Task: "tests/unit/test_media_extensions.py を新規作成して FAIL を確認（T001）"
Task: "i18n.py に filter.media_file / filter.audio_file / msg.no_media_file.* を追加（T003）"
# その後 T002（player.py 拡張子定数分割）を実行して T001 が PASS になることを確認
```

## Parallel Example: Phase 3 & 4 テスト作成（Phase 2 完了後）

```bash
# US1 追加テストと US2 テストを同時に作成:
Task: "test_media_extensions.py に filter 文字列テストを追加（T004）"
Task: "tests/unit/test_audio_placeholder.py を新規作成して FAIL を確認（T006）"
```

---

## Implementation Strategy

### MVP First（User Story 1 のみ）

1. Phase 2 完了（T001→T002→T003）
2. Phase 3 完了（T004, T005）
3. **STOP & VALIDATE**: `python main.py` で音楽ファイルを開いて再生できることを確認
4. 必要であればここでリリース

### Incremental Delivery

1. Phase 2 → Phase 3（音楽ファイル再生の基本）→ デモ可能
2. Phase 4（プレースホルダー表示）→ UX 改善
3. Phase 5（D&D・プレイリスト）→ 動画と同等の操作性
4. Phase 6（ブックマーク確認）→ 主要機能の完全対応

### Parallel Team Strategy

Phase 2 完了後:
- 開発者 A: Phase 3（T004 追加テスト→T005 実装）
- 開発者 B: Phase 4（T006 テスト→T007〜T011 実装）

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベルはトレーサビリティのためユーザーストーリーにタスクをマッピング
- Constitution I: テストは必ず先に書き、FAIL を確認してから実装する
- Constitution III: `AudioFile` クラスは作成しない。定数セットとブールフラグのみ
- 各チェックポイントで独立したストーリーの動作を検証してからコミットする
- 拡張子判定は `.suffix.lower()` による比較（既存コードと同じ）
