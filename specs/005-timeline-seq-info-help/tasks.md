# Tasks: タイムライン強化・連続再生選択・動画情報・ショートカット一覧

**Input**: Design documents from `/specs/005-timeline-seq-info-help/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: テストファースト原則に従い、各ユーザーストーリーでテスト→実装の順序を維持。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル・依存なし）
- **[Story]**: 対応するユーザーストーリー（US1〜US4）
- 各タスクに具体的なファイルパスを記載

---

## Phase 1: Foundational（ブロッキング前提条件）

**Purpose**: `LoopBookmark.enabled` フィールドの追加。US2の直接依存であり、US1の強調表示にも間接的に関与するため、全ユーザーストーリーより先に完了させる。

**⚠️ CRITICAL**: このフェーズが完了するまで、US1〜US4の実装に着手できない。

- [X] T001 `LoopBookmark.enabled` フィールドの追加・`to_dict`/`from_dict` 変更・後方互換性を検証する失敗テストを書く（テストが**失敗**することを確認） `tests/unit/test_bookmark_enabled.py`
- [X] T002 `LoopBookmark` に `enabled: bool = True` フィールドを追加し `to_dict`/`from_dict` を更新する `looplayer/bookmark_store.py`
- [X] T003 `BookmarkStore.update_enabled(video_path, bookmark_id, enabled)` メソッドを追加する `looplayer/bookmark_store.py`

**Checkpoint**: `pytest tests/unit/test_bookmark_enabled.py -v` がパスすること

---

## Phase 2: User Story 2 - 連続再生対象チェックボックス選択（Priority: P1）

**Goal**: 各ブックマーク行にチェックボックスを追加し、チェックされたブックマークのみを連続再生の対象とする。チェック状態はJSON永続化。

**Independent Test**: ブックマークを3件登録し2件チェック、連続再生開始 → チェックした2件のみ再生されることを確認。

### テスト（実装前に書く）

- [X] T004 [US2] チェック2件で連続再生した場合に未チェック区間が再生されないことを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/integration/test_sequential_filter.py`
- [X] T005 [US2] チェック0件のとき連続再生ボタンが無効化されることを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/unit/test_bookmark_enabled.py`

### 実装

- [X] T006 [US2] `BookmarkRow` に `QCheckBox` を追加し `enabled_changed = pyqtSignal(str, bool)` シグナルを定義する `looplayer/widgets/bookmark_row.py`
- [X] T007 [US2] `BookmarkPanel._on_enabled_changed()` ハンドラを追加し `BookmarkStore.update_enabled()` を呼ぶ `looplayer/widgets/bookmark_panel.py`
- [X] T008 [US2] `BookmarkPanel._refresh_list()` 末尾の `seq_btn.setEnabled()` を `any(bm.enabled for bm in bms)` に変更する `looplayer/widgets/bookmark_panel.py`
- [X] T009 [US2] `BookmarkPanel._on_seq_btn()` で `bms = [bm for bm in all_bms if bm.enabled]` によるフィルタリングを実装する `looplayer/widgets/bookmark_panel.py`
- [X] T009b [US2] 連続再生中に全ブックマークのチェックが解除された場合、現在区間終了後に連続再生が自動停止することを検証する失敗テスト→実装を行う `tests/integration/test_sequential_filter.py` `looplayer/widgets/bookmark_panel.py`

**Checkpoint**: `pytest tests/integration/test_sequential_filter.py tests/unit/test_bookmark_enabled.py -v` がパスすること

---

## Phase 3: User Story 1 - タイムライン上のABループ区間表示（Priority: P1）

**Goal**: シークバー上に各ブックマークのA〜B区間を半透明カラーバーで表示する。クリックでそのブックマークのA点にジャンプしABループを有効化。連続再生中は現在区間を強調表示。

**Independent Test**: ブックマークを2件以上登録した状態でシークバーを確認 → カラーバーが表示され、クリックでABループが切り替わることを確認。

### テスト（実装前に書く）

- [X] T010 [US1] チェックボックス変更後に `BookmarkSlider.set_bookmarks()` が更新されることを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/unit/test_bookmark_slider.py`
- [X] T011 [P] [US1] グルーブ座標計算・ms→X変換・最小幅クランプ・重複クリック判定（後ろ優先）を検証する失敗テストを書く（テストが**失敗**することを確認） `tests/unit/test_bookmark_slider.py`
- [X] T012 [P] [US1] ブックマーク追加後にシークバーバーが表示され、バークリックでABループが有効になることを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/integration/test_timeline_display.py`

### 実装

- [X] T013 [US1] `BookmarkSlider(QSlider)` クラスを新規作成する `looplayer/widgets/bookmark_slider.py`
  - `set_bookmarks(bookmarks, duration_ms, current_id=None)` メソッド
  - `_groove_rect()` で `QStyleOptionSlider` + `subControlRect` によるグルーブ取得
  - `_ms_to_x(ms, groove)` でミリ秒→X座標変換（動画長を超える区間はクリップして描画しない）
  - `paintEvent`: `super().paintEvent()` → 半透明カラーバー重ね描き（最小幅4px）
  - `mousePressEvent`: 重複時は後ろ（最前面）のブックマークを選択
  - `bookmark_bar_clicked = pyqtSignal(str)` シグナル定義
- [X] T014 [US1] `player.py` の `_build_ui()` で `seek_slider` を `BookmarkSlider` に差し替える `looplayer/player.py`
- [X] T015 [US1] `bookmark_bar_clicked` シグナルを `_on_bookmark_selected` に接続する `looplayer/player.py`
- [X] T016 [US1] `_sync_slider_bookmarks()` メソッドを追加し、ブックマーク変更・動画開閉のタイミングで呼び出す `looplayer/player.py`
  - 呼び出しタイミング: `open_file()` 後、`_save_bookmark()` 後、`_on_bookmark_selected()` 後、`_on_sequential_started/stopped()` 後
- [X] T017 [US1] `_on_timer()` 内で連続再生中に `set_bookmarks(..., current_id=...)` を呼び現在区間を強調する `looplayer/player.py`

**Checkpoint**: `pytest tests/unit/test_bookmark_slider.py tests/integration/test_timeline_display.py -v` がパスすること

---

## Phase 4: User Story 3 - 動画情報の表示（Priority: P2）

**Goal**: 動画を開いている状態で「ファイル」メニューの「動画情報...」から7項目（ファイル名・サイズ・長さ・解像度・FPS・映像コーデック・音声コーデック）を表示するダイアログを開く。

**Independent Test**: 任意の動画を開いた状態で「動画情報...」を選択 → 7項目がすべてダイアログに表示されることを確認。

### テスト（実装前に書く）

- [X] T018 [P] [US3] ファイルサイズのバイト→MB/GB表示フォーマット変換を検証する失敗テストを書く（テストが**失敗**することを確認） `tests/unit/test_video_info.py`
- [X] T019 [P] [US3] 動画を開いた後にダイアログが表示され7項目が存在することを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/integration/test_video_info_dialog.py`

### 実装

- [X] T020 [US3] `_show_video_info()` メソッドを追加する `looplayer/player.py`
  - `media_player.get_media().tracks_get()` で VideoTrack・AudioTrack を取得
  - `libvlc_media_get_codec_description()` でコーデック名を取得
  - `os.path.getsize()` でファイルサイズを取得
  - `QDialog` + `QGridLayout` でキー（右寄せ）/ 値（左寄せ）の2列レイアウト
  - 各 `QLabel` に `setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)` を設定してコピー可能にする（FR-013）
  - 取得失敗項目は「不明」と表示
- [X] T021 [US3] `_build_menus()` に `_video_info_action` を追加し、動画開閉に応じて enable/disable を制御する `looplayer/player.py`

**Checkpoint**: `pytest tests/unit/test_video_info.py tests/integration/test_video_info_dialog.py -v` がパスすること

---

## Phase 5: User Story 4 - キーボードショートカット一覧（Priority: P2）

**Goal**: `?` キー押下（またはヘルプメニュー）で全ショートカットをカテゴリ別に一覧表示するダイアログを開く。ダイアログを閉じても再生継続。

**Independent Test**: アプリ起動中に `?` キーを押す → 5カテゴリ以上のショートカット一覧ダイアログが表示されることを確認。

### テスト（実装前に書く）

- [X] T022 [P] [US4] `?` キーでダイアログが表示され全カテゴリが含まれることを検証する失敗テストを書く（テストが**失敗**することを確認） `tests/integration/test_shortcut_dialog.py`

### 実装

- [X] T023 [US4] `_show_shortcut_dialog()` メソッドを `player.py` 内に追加する `looplayer/player.py`
  - `SHORTCUTS` 定数リスト（6カテゴリ: 再生操作・音量操作・ABループ操作・ブックマーク操作・表示操作・ファイル操作）
  - `QDialog` + `QGridLayout` でカテゴリ見出し付き2列テーブル
- [X] T024 [US4] `_build_menus()` にヘルプメニュー（`&H`）と「ショートカット一覧」アクションを追加する `looplayer/player.py`
- [X] T025 [US4] `?` キーを `QShortcut`（`ApplicationShortcut` コンテキスト）で登録する `looplayer/player.py`

**Checkpoint**: `pytest tests/integration/test_shortcut_dialog.py -v` がパスすること

---

## Phase 6: Polish & クロスカッティング

**Purpose**: 回帰確認・後方互換性検証・最終整合

- [X] T026 全テストスイートを実行し既存テストの回帰がないことを確認する。あわせてSC-001（動画オープン後バー表示 < 1秒）・SC-002（バークリック応答 < 0.5秒）を手動タイミング計測で検証する（`pytest tests/ -v`）
- [X] T027 [P] `enabled` フィールドなし旧 `bookmarks.json` を読み込んだ場合に `enabled=True` として正常動作することを確認する `tests/unit/test_bookmark_enabled.py`
- [X] T028 [P] ブックマーク削除・Undo 後に `_sync_slider_bookmarks()` が呼ばれてタイムラインバーが更新されることを統合テストで検証する `tests/integration/test_timeline_display.py`
- [X] T029 [P] `bookmark_io.py` の `export_bookmarks` が `enabled` フィールドを含むこと、および `import_bookmarks` が `enabled` を正しく読み込むことを検証する `tests/unit/test_bookmark_io.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Foundational**: 依存なし → 即開始可能
- **Phase 2 US2**: Phase 1 完了後に開始
- **Phase 3 US1**: Phase 1 完了後に開始（Phase 2 と並列可能）
- **Phase 4 US3**: Phase 1 完了後に開始（Phase 2・3 と並列可能）
- **Phase 5 US4**: Phase 1 完了後に開始（完全独立）
- **Phase 6 Polish**: 全フェーズ完了後

### User Story Dependencies

- **US2（P1）**: Phase 1 依存。`LoopBookmark.enabled` の追加完了が前提
- **US1（P1）**: Phase 1 依存。US2 との並列実行可能（異なるファイル）
- **US3（P2）**: Phase 1 依存のみ。US1・US2 と完全並列可能
- **US4（P2）**: Phase 1 依存のみ。全ストーリーと完全並列可能

### Within Each User Story

1. テストを書く → 失敗を確認 → 実装 → パスを確認 → コミット

### Parallel Opportunities

```bash
# Phase 1 完了後、以下は並列実行可能
T004/T005 (US2テスト) + T010/T011/T012 (US1テスト) + T018/T019 (US3テスト) + T022 (US4テスト)

# US3・US4 の実装は US1・US2 実装と並列実行可能
T020/T021 (US3実装) || T023/T024/T025 (US4実装)
```

---

## Parallel Example: User Story 1 と 2 の並列実行

```bash
# Phase 1 完了後、US1・US2 のテストを並列で書く
Task A: "T004/T005 US2テストを tests/integration/test_sequential_filter.py に書く"
Task B: "T010/T011/T012 US1テストを tests/unit/test_bookmark_slider.py に書く"

# テスト失敗を確認後、実装を並列で進める
Task A: "T006〜T009 BookmarkRow/BookmarkPanel の変更"
Task B: "T013 BookmarkSlider の新規作成"
```

---

## Implementation Strategy

### MVP First（US2 → US1 の順）

1. Phase 1 完了: `enabled` フィールドを追加（テスト→実装）
2. Phase 2 完了: チェックボックス選択（テスト→実装）
3. Phase 3 完了: タイムライン区間表示（テスト→実装）
4. **STOP & VALIDATE**: `pytest tests/ -v` で全テストパスを確認
5. 必要ならリリース/デモ

### Incremental Delivery

1. Phase 1 → Phase 2 (US2) → 動作確認 → コミット
2. Phase 3 (US1) → 動作確認 → コミット
3. Phase 4 (US3) → 動作確認 → コミット
4. Phase 5 (US4) → 動作確認 → コミット
5. Phase 6 → 全テスト → 最終コミット

---

## Notes

- `[P]` タスク = 異なるファイル・依存関係なし（並列実行可能）
- `[Story]` ラベルで各タスクをユーザーストーリーにトレース
- テストが失敗することを確認してから実装に着手（テストファースト原則）
- 各チェックポイントでテストパス後にコミット
- `BookmarkSlider` は新規ファイルだが1箇所だけ使用。`player.py` が肥大化するより分離が適切（描画責務の分離）
