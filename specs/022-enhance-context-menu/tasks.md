# Tasks: コンテキストメニューの充実

**Input**: Design documents from `/specs/022-enhance-context-menu/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Organization**: 3つのユーザーストーリー（P1→P2→P3）を優先度順に、テストファーストで実装する。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並行実行可能（異なるファイル、未完タスクへの依存なし）
- **[Story]**: 対応ユーザーストーリー（US1=動画エリア, US2=ブックマーク行, US3=パネル空白）

---

## Phase 1: Setup — 共通基盤

> 全ストーリーに先立って完了させる必要がある共有リソース。

- [x] T001 `looplayer/i18n.py` に `ctx.*` および `bookmark.copy_suffix` キーを日本語・英語で追加する（data-model.md 参照 14キー）

---

## Phase 2: Foundational — BookmarkStore 拡張

> US2（複製）で必要な `insert_after()` を先行実装する。US1・US3 の実装と並行して進めることができる。

- [x] T002 `tests/unit/test_bookmark_store_insert_after.py` を作成して `insert_after()` の以下をテストする（赤フェーズ）:
  - 中間位置への挿入後の order が正しいこと
  - after_id が存在しない場合は末尾に追加されること
  - 挿入後に `_save_all()` が呼ばれて JSON に永続化されること
- [x] T003 `looplayer/bookmark_store.py` に `insert_after(video_path, bookmark, after_id)` を実装してテストをパスさせる

---

## Phase 3: US1 — 動画エリアの右クリックメニュー（P1）

> **Story Goal**: 動画エリアを右クリックするとコンテキストメニューが表示され、再生制御・A/B 点設定・ブックマーク追加・スクリーンショット・フルスクリーン切り替えが 1クリックで実行できる。
>
> **Independent Test**: 動画を開いた状態で動画エリアを右クリックしてメニューが出現し、各項目が動作することで完結する。

- [x] T004 [US1] `tests/integration/test_video_ctx_menu.py` を作成して以下をテストする（赤フェーズ）:
  - `_video_ctx_overlay` が video_frame の子ウィジェットとして存在すること
  - `_show_video_context_menu()` が QMenu を生成してアクションを含むこと
  - ファイル未開時に再生系アクションが disabled であること
  - A/B 両方設定済み時のみ「ここにブックマークを追加」が enabled であること
- [x] T005 [US1] `looplayer/player.py` の `_build_ui()` 末尾に `_build_video_context_overlay()` の呼び出しを追加し、`WA_TranslucentBackground` 付き透明 QWidget を video_frame の子として生成する
- [x] T006 [US1] `looplayer/player.py` に `_show_video_context_menu(pos: QPoint)` を実装する:
  - 「再生 / 一時停止」「停止」（ファイル未開時 disabled）
  - 「A点を設定」「B点を設定」（ファイル未開時 disabled）
  - 「ここにブックマークを追加」（A/B 両方設定済み時のみ enabled）
  - 「スクリーンショット」（`_screenshot_action` の enabled 状態に連動）
  - 「フルスクリーン切り替え」（`fullscreen_action` を再利用）
- [x] T007 [US1] `looplayer/player.py` の `resizeEvent` と `_enter_fullscreen_overlay_mode` / `_exit_fullscreen_overlay_mode` を更新してオーバーレイが video_frame に追従・フルスクリーン時も正しく表示されるようにする

---

## Phase 4: US2 — ブックマーク行の右クリックメニュー拡充（P2）

> **Story Goal**: ブックマーク行を右クリックして「A点へジャンプ」「名前を変更」「複製」「削除」を含む 8 項目のメニューを操作できる。削除は既存 Undo フローと連動し、複製は直後に挿入される。
>
> **Independent Test**: ブックマーク行を右クリックしてすべての新規項目が動作し、A点ジャンプが再生状態を変えないことを確認することで完結する。

- [x] T008 [US2] `tests/unit/test_bookmark_row_ctx_menu.py` を作成して以下をテストする（赤フェーズ）:
  - コンテキストメニューに「A点へジャンプ」「名前を変更」「複製」「削除」が存在すること
  - コンテキストメニューの総項目数（セパレータ除く）が 8 件であること（SC-002 検証）
  - 「A点へジャンプ」選択時に `jump_to_a_requested(bookmark_id)` が emit されること
  - 「複製」選択時に `duplicate_requested(bookmark_id)` が emit されること
  - 「削除」選択時に既存の `deleted(bookmark_id)` が emit されること
  - A/B 未設定時に「クリップを書き出す」が disabled であること
- [x] T009 [US2] `looplayer/widgets/bookmark_row.py` を変更する:
  - `jump_to_a_requested = pyqtSignal(str)` / `duplicate_requested = pyqtSignal(str)` シグナルを追加
  - `eventFilter` の名前変更ダイアログ処理を `_start_rename()` メソッドに抽出
  - `_show_context_menu()` に「A点へジャンプ」「名前を変更」「複製」「削除」を追加（順序は plan.md 参照）
- [x] T010 [US2] `tests/unit/test_bookmark_panel_ctx_menu.py` を作成して以下をテストする（赤フェーズ）:
  - `_on_jump_to_a(bookmark_id)` 呼び出し時に `seek_to_ms_requested(a_ms)` が emit されること
  - `_on_duplicate(bookmark_id)` 呼び出し時にストアに複製ブックマークが追加されること
  - 複製ブックマークの name 末尾に「のコピー」が付くこと
  - 複製ブックマークが元の直後の order に挿入されること
- [x] T011 [P] [US2] `looplayer/widgets/bookmark_panel.py` を変更する:
  - `seek_to_ms_requested = pyqtSignal(int)` シグナルを追加
  - `_on_jump_to_a(bookmark_id)` ハンドラを追加（bookmark lookup → emit seek_to_ms_requested）
  - `_on_duplicate(bookmark_id)` ハンドラを追加（複製 LoopBookmark 作成 → `store.insert_after()` → `_refresh_list()`）
  - `_refresh_list()` 内で `row.jump_to_a_requested` と `row.duplicate_requested` を接続
- [x] T012 [US2] `looplayer/player.py` に `_on_seek_to_ms(ms: int)` を追加し、`bookmark_panel.seek_to_ms_requested` に接続する（再生状態を変えずに `media_player.set_time(ms)` のみ呼ぶ）

---

## Phase 5: US3 — ブックマークパネル空白エリアの右クリックメニュー（P3）

> **Story Goal**: ブックマークパネルの空白エリアを右クリックするとインポート・エクスポートメニューが表示され、既存の処理を呼び出せる。
>
> **Independent Test**: パネルの空白エリアを右クリックしてメニューが表示され、インポート/エクスポートが既存ダイアログを開くことで完結する。

- [x] T013 [US3] `tests/unit/test_bookmark_panel_empty_ctx_menu.py` を作成して以下をテストする（赤フェーズ）:
  - `_show_panel_context_menu()` が空白クリック時にのみ発火し、行クリック時は無視されること
  - `import_requested` シグナルがメニューから発火されること
  - `export_from_panel_requested` シグナルがブックマーク1件以上のとき発火されること
  - ブックマーク0件時に「エクスポート」が disabled であること
- [x] T014 [US3] `looplayer/widgets/bookmark_panel.py` を変更する:
  - `import_requested = pyqtSignal()` / `export_from_panel_requested = pyqtSignal()` シグナルを追加
  - `_build_ui()` 内で `list_widget.setContextMenuPolicy(CustomContextMenu)` を設定
  - `_show_panel_context_menu(pos)` を実装（`itemAt(pos) is None` のみ動作、ブックマーク0件時エクスポート disabled）
- [x] T015 [US3] `looplayer/player.py` で `bookmark_panel.import_requested` を `_import_bookmarks` に、`bookmark_panel.export_from_panel_requested` を `_export_bookmarks` に接続する

---

## Final Phase: Polish — 完成確認

- [x] T016 `pytest tests/ -v` を実行して全テストがパスすることを確認し、リグレッションがないことを保証する

---

## Dependencies

```
T001 (i18n)
  ├─→ T004..T007 (US1)
  ├─→ T008..T012 (US2)
  └─→ T013..T015 (US3)

T002..T003 (insert_after)
  └─→ T010..T011 (US2 複製機能)

T004 (US1 テスト)
  └─→ T005..T007 (US1 実装)

T008 (US2 row テスト)
  └─→ T009 (US2 row 実装)     ※ T009 は T008 完了後に開始（直列）

T010 (US2 panel テスト)
  └─→ T011 [P] (US2 panel 実装、T009 と並行可)
       └─→ T012 (player 接続)

T013 (US3 テスト)
  └─→ T014 (US3 実装)
       └─→ T015 (US3 player 接続)
            └─→ T016 (最終確認)
```

## Parallel Execution Examples

**T001 完了後、US1 と US2/US3 の基盤は並行して進められる:**

```
（T001 完了後）
Worker A: T004 → T005 → T006 → T007
Worker B: T002 → T003 → T008 → T009 → T010
                                         ↓
                                    T011（T009 と並行可）→ T012 → T013 → T014 → T015 → T016
```

**US2 内で T009 と T011 は T008・T010 それぞれ完了後に並行可:**

```
（T008 完了後）        （T010 完了後）
Worker A: T009         Worker B: T011
→ 両方完了後に T012
```

> ⚠️ T009 は T008（赤フェーズ）完了後に開始すること。`[P]` マーカーは T011 との並行を示し、T008 との並行ではない。

## Implementation Strategy

| フェーズ | 内容 | 価値 |
|---------|------|------|
| **MVP** | Phase 1 + Phase 3 (T001, T004-T007) | 動画エリア右クリックが動作する最小完成形 |
| **拡充** | Phase 2 + Phase 4 (T002-T003, T008-T012) | ブックマーク行のメニューが充実する |
| **完成** | Phase 5 + Final (T013-T016) | パネル空白エリアメニューとリグレッション確認 |
