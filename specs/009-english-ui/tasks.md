# Tasks: 英語 UI 対応

**Input**: Design documents from `/specs/009-english-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, contracts/strings.md ✅, quickstart.md ✅

**Tests**: 憲法 I（テストファースト）に従い、`looplayer/i18n.py` の実装前にユニットテストを記述する。

**Organization**: US1（OS ロケール自動検出 + 全 UI テキストの英語化）のみ。1 ユーザーストーリー構成。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup（共有インフラ）

**Purpose**: 新規モジュール `looplayer/i18n.py` の骨格確認・テストファイル準備

- [X] T001 `looplayer/i18n.py` の新規ファイルを作成し、モジュール構造（`_STRINGS`, `_lang`, `t(key)` のスタブ）を用意する

---

## Phase 2: Foundational（ブロッキング前提条件）

**Purpose**: `i18n.py` の `t()` 関数と `_STRINGS` 辞書が完成するまで UI 側の置換作業は開始できない

**⚠️ CRITICAL**: T001〜T004 完了後に UI 置換フェーズを開始する

- [X] T002 `tests/unit/test_i18n.py` を新規作成し、以下の **失敗するテスト** を記述する（実装前に FAIL を確認すること）:
  - `test_t_returns_japanese_when_lang_is_ja`: `_lang="ja"` のとき `t("menu.file")` が `"ファイル(&F)"` を返す
  - `test_t_returns_english_when_lang_is_en`: `_lang="en"` のとき `t("menu.file")` が `"File(&F)"` を返す
  - `test_t_fallback_returns_key_for_unknown_key`: 未登録キーのとき `t("unknown.key")` がキー文字列 `"unknown.key"` を返す
  - `test_all_keys_have_both_languages`: `_STRINGS` の全エントリが `"ja"` と `"en"` キーを持つことを検証する

- [X] T003 `looplayer/i18n.py` に `_STRINGS` 辞書を実装する。`contracts/strings.md` の全 51 件のキー・日本語・英語テキストを記述する（`menu.*`, `label.*`, `btn.*`, `msg.*`, `status.*`, `dialog.*`, `bookmark.*` 各グループ）

- [X] T004 `looplayer/i18n.py` に `_detect_lang()` 関数と `_lang` 変数、`t(key: str) -> str` 関数を実装する:
  - `_detect_lang()`: `QLocale.system().language() == QLocale.Language.Japanese` なら `"ja"`、それ以外は `"en"` を返す
  - `_lang = _detect_lang()` をモジュールレベルで評価
  - `t(key)`: `_STRINGS.get(key, {}).get(_lang, key)` を返す

**Checkpoint**: `pytest tests/unit/test_i18n.py -v` が全パスすること。

---

## Phase 3: User Story 1 — OS ロケール自動検出で UI テキストを英語/日本語表示 (Priority: P1) 🎯 MVP

**Goal**: `player.py`・`bookmark_panel.py`・`bookmark_row.py` の全ハードコード日本語文字列を `t("key")` に置換し、英語ロケール環境で英語 UI が表示される。

**Independent Test**: `LANG=en_US.UTF-8 python main.py` で起動しメニュー・ボタン・ラベルがすべて英語で表示されること、および `pytest tests/unit/test_i18n.py -v` 全パス。

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T005 [US1] `tests/unit/test_i18n.py` に以下の追加テストを記述する（T002 ファイルに追記）:
  - `test_t_menu_playback_en`: `_lang="en"` で `t("menu.playback")` が `"Playback(&P)"` を返す
  - `test_t_btn_play_ja`: `_lang="ja"` で `t("btn.play")` が `"再生"` を返す
  - `test_t_bookmark_panel_title_en`: `_lang="en"` で `t("bookmark.panel.title")` が `"Bookmarks"` を返す
  - `test_t_msg_file_not_found_en`: `_lang="en"` で `t("msg.file_not_found.title")` が `"File Not Found"` を返す

### Implementation for User Story 1

- [X] T006 [US1] `looplayer/player.py` の先頭に `from looplayer.i18n import t` を追加し、以下のメニュー文字列を置換する（`_build_menus` メソッド内、合計 28 件）:
  - `"ファイル(&F)"` → `t("menu.file")`, `"最近開いたファイル(&R)"` → `t("menu.file.recent")`
  - `"再生(&P)"` → `t("menu.playback")`, `"再生速度"` → `t("menu.playback.speed")`
  - `"再生終了時の動作(&E)"` → `t("menu.playback.end_action")`, 各終了動作ラベル → 対応する `t()` キー
  - `"音声トラック(&A)"` → `t("menu.playback.audio_track")`, `"字幕(&S)"` → `t("menu.playback.subtitle")`
  - `"表示(&V)"` → `t("menu.view")`, `"ヘルプ(&H)"` → `t("menu.help")`, `"キーボードショートカット一覧"` → `t("menu.help.shortcuts")`
  - View メニュー各アクション → 対応する `t()` キー

- [X] T007 [US1] `looplayer/player.py` の `_build_controls` / `__init__` 内のコントロール文字列を置換する:
  - `QLabel("音量:")` → `QLabel(t("label.volume"))`
  - `QPushButton("再生")` / `QPushButton("一時停止")` の初期テキストを `t("btn.play")` / `t("btn.pause")` に変更
  - `self.play_btn.setText(...)` の各呼び出しを対応する `t()` キーに変更
  - `ABループ: ON` / `ABループ: OFF` を `t("btn.ab_loop_on")` / `t("btn.ab_loop_off")` に変更

- [X] T008 [P] [US1] `looplayer/player.py` のダイアログ・エラーメッセージ・ステータスバー文字列を置換する（T006・T007 と並行可能）:
  - `QMessageBox.warning` の各タイトル・本文を対応する `t()` キー＋`.format()` に変更
  - `self.statusBar().showMessage(f"保存しました: {path}", ...)` → `t("status.screenshot_saved").format(path=path)`
  - `"最大速度です"` → `t("status.max_speed")`, `"最小速度です"` → `t("status.min_speed")`
  - `dialog.setWindowTitle("動画情報")` → `t("dialog.video_info.title")`
  - `dialog.setWindowTitle("キーボードショートカット一覧")` → `t("dialog.shortcuts.title")`

- [X] T009 [P] [US1] `looplayer/widgets/bookmark_panel.py` の全日本語文字列を置換する（T006 と並行可能）:
  - ファイル先頭に `from looplayer.i18n import t` を追加
  - `QLabel("ブックマーク一覧")` → `QLabel(t("bookmark.panel.title"))`
  - `QPushButton("連続再生")` → `QPushButton(t("bookmark.panel.seq_play"))`
  - `self.seq_btn.setText("連続再生")` / `"連続再生 停止"` → `t()` キー
  - `self.seq_status_label.setText(f"▶ 現在: {cur}  →  次: {nxt}")` → `t("bookmark.panel.seq_status").format(cur=cur, nxt=nxt)`
  - `QInputDialog.getMultiLineText(self, "メモを編集", f"「{bm.name}」のメモ:", ...)` → `t()` キー使用

- [X] T010 [P] [US1] `looplayer/widgets/bookmark_row.py` の全日本語文字列を置換する（T006 と並行可能）:
  - ファイル先頭に `from looplayer.i18n import t` を追加
  - `self.enabled_checkbox.setToolTip("連続再生の対象にする")` → `t("bookmark.row.enabled_tip")`
  - `self.name_label.setToolTip("ダブルクリックで名前を編集")` → `t("bookmark.row.name_tip")`
  - `QLabel("繰返:")` → `QLabel(t("bookmark.row.repeat"))`
  - `del_btn.setToolTip("削除")` → `t("bookmark.row.delete_tip")`
  - `self.memo_btn.setToolTip("メモ")` → `t("bookmark.row.memo_tip")`
  - `self.memo_btn.setToolTip(f"メモ: {notes}")` → `t("bookmark.row.memo_tip_content").format(notes=notes)`

**Checkpoint**: `pytest tests/unit/test_i18n.py -v` 全パス。手動で `LANG=en_US.UTF-8 python main.py` を確認する（quickstart.md シナリオ 1）。

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: 全体テスト実行・クリーンアップ

- [X] T011 [P] `pytest tests/ -v` を実行し全テストがパスすることを確認する（リグレッションゼロ）
- [ ] T012 quickstart.md のシナリオ 1〜3 に従い、英語・日本語・その他ロケールでの手動検証を実施する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし・即開始可能
- **Foundational (Phase 2)**: T001 完了後。テスト(T002) → 辞書実装(T003) → `t()` 実装(T004) の順を厳守
- **US1 (Phase 3)**: T001〜T004 完了後（`t()` が動作することが前提）
- **Polish (Phase 4)**: US1 完了後

### User Story Dependencies

- **US1 (P1)**: Foundational 完了後に開始。T006・T007・T008・T009・T010 のうち、異なるファイルを扱うものは並行可能

### Within Each User Story

- T005（追加テスト）を先に書き、FAIL を確認してから T006〜T010 に進む（憲法 I）
- T006（player.py メニュー）→ T007（player.py コントロール）の順（同一ファイル）
- T008（player.py ダイアログ）は T006 と同一ファイルだが変更箇所が独立 → T006 完了後に実施
- T009（bookmark_panel.py）と T010（bookmark_row.py）は T006 と並行可能 [P]

### Parallel Opportunities

- T003 と T002 は同一ファイル（test_i18n.py）に依存するため逐次
- T009（bookmark_panel.py）と T010（bookmark_row.py）は完全に別ファイル → 並行可能 [P]
- T011 と T012 は並行可能 [P]

---

## Parallel Example: User Story 1

```bash
# i18n.py 完成後、UI 側の3ファイルを並行実装できる:
Task A: "T006-T008: player.py の日本語文字列を t() に置換"
Task B: "T009: bookmark_panel.py の日本語文字列を t() に置換"
Task C: "T010: bookmark_row.py の日本語文字列を t() に置換"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 完了: T001（i18n.py 骨格）
2. Foundational: T002（テスト記述・FAIL 確認）→ T003（辞書実装）→ T004（t() 実装）→ テストパス確認
3. US1 テスト追加: T005（追加テスト・FAIL 確認）
4. US1 実装: T006→T007→T008（player.py）、T009（bookmark_panel.py）[P]、T010（bookmark_row.py）[P]
5. **STOP and VALIDATE**: `pytest tests/ -v` + 手動確認（quickstart.md）
6. Polish: T011〜T012

### Incremental Delivery

1. T001〜T004: `i18n.py` 完成、テストパス → ロケール検出ロジックが動作
2. T005〜T007: player.py のメニュー・コントロール英語化 → 最も目立つ UI が英語化される
3. T008〜T010: player.py ダイアログ + ブックマークパネル英語化 → 全面英語化完成
4. T011〜T012: 全体検証 → マージ準備

---

## Notes

- [P] tasks = different files, no dependencies
- **憲法 I 必須**: T002・T005 は T003・T006 より前に書き、必ず FAIL を確認する
- `t(key)` の返り値は文字列（f-string ではなく `.format()` で変数埋め込み）
- `_STRINGS` 辞書はフラット（ネストなし）。キーはドット区切りの命名のみ
- 字幕・音声トラック名はメディア由来のため翻訳不要
- 再生速度値（`0.5x`, `1.0x` 等）は数値表現のため翻訳不要
