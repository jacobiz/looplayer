# Tasks: Bookmark Side Panel Toggle

**Input**: Design documents from `/specs/021-bookmark-sidepanel/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Constitution I（テストファースト）に従い、全ユーザーストーリーでテストを先に書く。

**Organization**: ユーザーストーリー（P1→P2→P3）順にフェーズを構成。各フェーズは独立してテスト・デモ可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル・依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2, US3）
- 各タスクに実ファイルパスを記載

---

## Phase 1: Setup（確認・準備）

**Purpose**: 実装前の既存コード確認と環境準備

- [x] T001 `looplayer/app_settings.py` の `mirror_display` プロパティ直後の挿入位置を確認する（`mirror_display` セッター末尾の行番号を特定）
- [x] T002 [P] `looplayer/player.py` の `controls_layout.addWidget(self._panel_tabs)` の行番号と `layout.addWidget(self.video_frame, stretch=1)` の行番号を確認する
- [x] T003 [P] `looplayer/i18n.py` の `menu.view` セクション末尾と `shortcut.*` セクション末尾の挿入位置を確認する

---

## Phase 2: Foundational（共通基盤）

**Purpose**: 全ユーザーストーリーが依存する AppSettings フィールドと i18n キーを追加する

**⚠️ CRITICAL**: このフェーズ完了前にユーザーストーリーの実装を開始しない

> **Constitution I 準拠**: 実装前にテストを書き、失敗することを確認してから実装する

### テスト（先行作成）

- [x] T004 [P] `tests/unit/test_app_settings_panel.py` を新規作成し、以下のテストを記述する（この時点では FAIL する）:
  - `bookmark_panel_visible` のデフォルト値が `False` であること
  - `bookmark_panel_visible` への代入が永続化されること
  - `bookmark_panel_width` のデフォルト値が `280` であること
  - `bookmark_panel_width` への代入値が最小 240px にクランプされること（例: 100 → 240、300 → 300）

### 実装

- [x] T005 `looplayer/app_settings.py` の `mirror_display` セッター直後に `bookmark_panel_visible` プロパティ（getter/setter）を追加する（quickstart.md §1 参照）
- [x] T006 `looplayer/app_settings.py` に `bookmark_panel_width` プロパティ（getter/setter、最小値クランプ 240px）を追加する（quickstart.md §1 参照）
- [x] T007 [P] `looplayer/i18n.py` の `menu.view` セクションに `menu.view.bookmark_panel` キーを追加する（`"ブックマークパネル (&B)"` / `"Bookmark Panel (&B)"`）
- [x] T008 `looplayer/i18n.py` の `shortcut.*` セクションに `shortcut.bookmark_panel` キーを追加する（`"ブックマークパネル 表示切り替え (B)"` / `"Toggle bookmark panel (B)"`）（T007 完了後に実施）
- [x] T009 `pytest tests/unit/test_app_settings_panel.py -v` を実行して T004 のテストが全通過することを確認する

**Checkpoint**: AppSettings フィールドと i18n キーが利用可能になった。ユーザーストーリー実装を開始できる。

---

## Phase 3: User Story 1 — サイドパネルの表示・非表示切り替え（Priority: P1）🎯 MVP

**Goal**: `B` キーまたはメニュー「表示 → ブックマークパネル」で、動画右側にサイドパネルをワンアクションで表示・非表示切り替えできる

**Independent Test**: アプリを起動 → `B` キー押下でパネルが右側に現れ、再度押下で消える。メニューのチェックマークが状態と同期する。パネル内でブックマーク操作（保存・選択・削除）が正常動作する。

### テスト（先行作成）

> **Constitution I 準拠: T010〜T011 を先に書き、FAIL を確認してから T012 以降を実装する**

- [x] T010 [US1] `tests/unit/test_bookmark_panel_toggle.py` を新規作成し、以下のテストを記述する（この時点では FAIL する）:
  - `_toggle_bookmark_panel()` 呼び出し後に `_panel_tabs.isVisible()` が True になること
  - 再度呼び出し後に `_panel_tabs.isVisible()` が False になること
  - 非表示化時に `_app_settings.bookmark_panel_visible` が False に更新されること
  - 表示化時に `_app_settings.bookmark_panel_visible` が True に更新されること
  - `_bookmark_panel_action.isChecked()` が `_panel_tabs.isVisible()` と常に同期していること

- [x] T011 [US1] `tests/integration/test_bookmark_panel_ui.py` を新規作成し、以下のテストを記述する（この時点では FAIL する）:
  - フィクスチャの teardown に `player._size_poll_timer.stop()` を追加すること（既存テストと同パターン）
  - アプリ起動直後にパネルが非表示であること（`_panel_tabs.isVisible() == False`）
  - `B` キー押下でパネルが表示されること
  - 再度 `B` キー押下でパネルが非表示になること
  - メニュー「表示 → ブックマークパネル」操作でパネル表示が切り替わること
  - パネル表示中にメニュー項目のチェックマークが付いていること
  - パネル表示・非表示切り替え後もシークバー・再生ボタンが表示されていること（FR-009）
  - パネル表示中にブックマーク操作（保存・選択・削除）が正常動作すること（FR-008）
  - ウィンドウを幅 400px 相当に縮小してもパネルが 240px 未満にならないこと（EC-2）

### 実装

- [x] T012 [US1] `looplayer/player.py` の `_setup_ui()` 内で `controls_layout.addWidget(self._panel_tabs)` を削除する（quickstart.md §2 の「変更前のコード」参照）
- [x] T013 [US1] `looplayer/player.py` の `_setup_ui()` 内で `layout.addWidget(self.video_frame, stretch=1)` を QSplitter レイアウトに置き換える:
  - `self._splitter = QSplitter(Qt.Orientation.Horizontal)` を作成
  - `self._splitter.setChildrenCollapsible(False)` を設定
  - `self._splitter.addWidget(self.video_frame)`
  - `self._panel_tabs.setMinimumWidth(240)`
  - `self._splitter.addWidget(self._panel_tabs)`
  - `self.video_frame.setMinimumWidth(320)`
  - `layout.addWidget(self._splitter, stretch=1)`
  - `QTimer.singleShot(0, self._apply_initial_panel_width)` を追加
  - （quickstart.md §2 参照）
- [x] T014 [US1] `looplayer/player.py` に `_apply_initial_panel_width()` メソッドを追加する（quickstart.md §3 参照）:
  - `total = self._splitter.width()` でスプリッター幅を取得
  - `visible` フラグに応じて `_panel_tabs.hide()` または `setSizes()` を実行
  - `self._bookmark_panel_action.setChecked(visible)` でメニューと同期
- [x] T015 [US1] `looplayer/player.py` に `_toggle_bookmark_panel()` メソッドを追加する（quickstart.md §4 参照）:
  - 現在の `isVisible()` を反転
  - 表示時: `_panel_tabs.show()` + `setSizes([total - w, w])`
  - 非表示時: 幅を `_app_settings.bookmark_panel_width` に保存 + `_panel_tabs.hide()`
  - `_app_settings.bookmark_panel_visible` 更新 + `save()`
  - `_bookmark_panel_action.setChecked(visible)` で同期
- [x] T016 [US1] `looplayer/player.py` の `_setup_view_menu()` に `_bookmark_panel_action`（チェック可能 QAction、ショートカット `B`）を `mirror_action` の直後に追加する（quickstart.md §5 参照）
- [x] T017 [US1] `pytest tests/unit/test_bookmark_panel_toggle.py tests/integration/test_bookmark_panel_ui.py -v` を実行して全テストが通過することを確認する

**Checkpoint**: この時点で US1 が完全に動作し独立してデモ可能。`pytest tests/ -v` でリグレッションゼロを確認する。

---

## Phase 4: User Story 2 — サイドパネルの幅調整と永続化（Priority: P2）

**Goal**: 境界ドラッグで幅を自由に調整でき、アプリ再起動後も同じ幅が維持される

**Independent Test**: パネルを表示 → スプリッター境界をドラッグして幅を変更 → アプリ終了 → 再起動してパネルを表示 → 変更した幅で表示されること。初回起動時はデフォルト 280px（最小 240px 保証）で表示されること。

### テスト（先行作成）

> **Constitution I 準拠: T018 を先に書き、FAIL を確認してから T019〜T020 を実装する**

- [x] T018 [US2] `tests/integration/test_bookmark_panel_ui.py` に以下のテストを追加する（この時点では FAIL する）:
  - ※ T015（`_toggle_bookmark_panel` のパネル非表示時幅保存）が実装済みであることが前提
  - パネル非表示化時に `_app_settings.bookmark_panel_width` が splitter の現在幅で更新されること（T015 実装に依存）
  - `closeEvent` 時にパネルが表示中ならば `_app_settings.bookmark_panel_width` が更新されること
  - `closeEvent` 時にパネルが非表示ならば幅が変更されないこと
  - 起動時に `_app_settings.bookmark_panel_width=350` が設定されている場合、パネル表示後に splitter の右ペイン幅が 350px になること

### 実装

- [x] T019 [US2] `looplayer/player.py` の `closeEvent()` に幅保存ロジックを追加する（quickstart.md §7 参照）:
  - パネルが表示中かつ `splitter.sizes()` の長さ >= 2 かつ `sizes[1] > 0` の場合
  - `self._app_settings.bookmark_panel_width = sizes[1]` を実行
  - `self._app_settings.save()` を呼び出す
- [x] T020 [US2] `pytest tests/integration/test_bookmark_panel_ui.py -v -k "width or close"` を実行して T018 のテストが通過することを確認する

**Checkpoint**: この時点で US2 が完全に動作。幅の永続化を手動確認: パネルを表示 → 幅を変更 → アプリを終了 → 再起動 → 幅が復元されることを確認する。

---

## Phase 5: User Story 3 — フルスクリーン時のパネル自動制御（Priority: P3）

**Goal**: フルスクリーン移行時にパネルが自動非表示になり、解除後に元の表示状態が復元される

**Independent Test**: パネルを表示した状態で `F` キーでフルスクリーン → パネルが非表示になる → `F` で解除 → パネルが再び表示される。パネル非表示の状態でフルスクリーン切り替えしてもパネルは非表示のまま。

### テスト（先行作成）

> **Constitution I 準拠: T021 を先に書き、FAIL を確認してから T022〜T023 を実装する**

- [x] T021 [US3] `tests/integration/test_bookmark_panel_ui.py` に以下のテストを追加する（この時点では FAIL する）:
  - パネル表示中にフルスクリーン移行すると `_panel_tabs.isVisible() == False` になること
  - フルスクリーン解除後に `_panel_tabs.isVisible() == True` に復元されること（元々表示中だった場合）
  - パネル非表示中にフルスクリーン切り替えしても `_panel_tabs.isVisible() == False` のまま維持されること

### 実装

- [x] T022 [US3] `looplayer/player.py` の `_enter_fullscreen_overlay_mode()` に以下を追加する（quickstart.md §6 参照）:
  - `self._panel_tabs_was_visible = self._panel_tabs.isVisible()`
  - `self._panel_tabs.hide()`
- [x] T023 [US3] `looplayer/player.py` の `_exit_fullscreen_overlay_mode()` に以下を追加する（quickstart.md §6 参照）:
  - `if getattr(self, "_panel_tabs_was_visible", False):` の条件分岐
  - `self._panel_tabs.show()`
  - `splitter.setSizes([total - max(w, 240), max(w, 240)])`
- [x] T024 [US3] `pytest tests/integration/test_bookmark_panel_ui.py -v -k "fullscreen"` を実行して T021 のテストが通過することを確認する

**Checkpoint**: この時点で US1・US2・US3 が全て動作。全ユーザーストーリーを独立してデモ可能。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 複数ストーリーにまたがる動作の修正と全体的な品質確認

- [x] T025 `looplayer/player.py` の `_resize_to_video()` にパネル幅の加算ロジックを追加する（quickstart.md §8 参照）:
  - `panel_w = self._splitter.sizes()[1] if (hasattr(self, "_splitter") and self._panel_tabs.isVisible()) else 0`
  - `target_w = min(w + panel_w, avail.width())`
- [x] T026 `pytest tests/ -v` を実行して全テスト（ユニット + 統合）が通過することを確認する（SC-006: リグレッションゼロ）
- [x] T027 quickstart.md の「動作確認チェックリスト」を手動で実施する:
  - アプリ起動 → パネルは非表示
  - `B` キー → パネルが動画右に表示
  - 境界ドラッグ → 幅が変更できる
  - アプリ再起動 → 前回の表示状態・幅が復元される
  - フルスクリーン（`F`）→ パネル非表示。解除後に復元
  - メニュー「表示 → ブックマークパネル」のチェックマークが状態と同期

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即時開始可能
- **Foundational (Phase 2)**: Phase 1 完了後 — 全ユーザーストーリーをブロック
- **US1 (Phase 3)**: Phase 2 完了後 — US2・US3 に非依存
- **US2 (Phase 4)**: Phase 3 完了後（`_apply_initial_panel_width` を再利用するため）
- **US3 (Phase 5)**: Phase 3 完了後（`_enter/exit_fullscreen_overlay_mode` 修正のため）
- **Polish (Phase 6)**: Phase 3〜5 完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始可能。他ストーリーへの依存なし
- **US2 (P2)**: US1 完了後に開始（`_apply_initial_panel_width` が US1 で実装済みのため）
- **US3 (P3)**: US1 完了後に開始（`_enter/exit_fullscreen` が US1 のコードを前提とするため）

### Within Each User Story

1. テストを書く → 2. テストが FAIL することを確認 → 3. 実装 → 4. テストが PASS することを確認

---

## Parallel Opportunities

### Phase 2 での並列実行

```bash
# 並列実行可能:
T004  tests/unit/test_app_settings_panel.py の作成
T007  i18n.py への menu.view.bookmark_panel 追加

# T007 完了後に順次実行:
T008  i18n.py への shortcut.bookmark_panel 追加（同一ファイルのため T007 の後）
```

### Phase 1 での並列実行

```bash
# 並列実行可能:
T001  app_settings.py の挿入位置確認
T002  player.py の対象行番号確認
T003  i18n.py の挿入位置確認
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1 完了（確認・準備）
2. Phase 2 完了（AppSettings + i18n）— 必須基盤
3. Phase 3 完了（US1: トグル操作）
4. **STOP & VALIDATE**: `pytest tests/ -v` + 手動確認
5. デモ・レビュー可能

### 段階的デリバリー

1. Setup + Foundational → 基盤完成
2. US1 → パネルの表示・非表示切り替え ✅ デモ可能（MVP）
3. US2 → 幅の永続化 ✅ デモ可能
4. US3 → フルスクリーン連動 ✅ デモ可能
5. Polish → 全テスト通過・動作確認チェックリスト完了

---

## Notes

- **[P] タスク** = 別ファイルへの変更、依存なし、並列実行可能
- **[Story] ラベル** = タスクと対応するユーザーストーリーのトレーサビリティ
- Constitution I により各フェーズでテストを先に書いて FAIL を確認すること
- `tests/integration/` テストは実際の依存（QApplication, QWidget）を使用しモックしない
- 各チェックポイントで `pytest tests/ -v` を実行しリグレッションゼロを維持すること
- `_size_poll_timer.stop()` を `test_bookmark_panel_ui.py` の全 `player` フィクスチャに追加すること（既存テストと同様のパターン）
