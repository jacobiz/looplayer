# Implementation Plan: コンテキストメニューの充実

**Branch**: `022-enhance-context-menu` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/022-enhance-context-menu/spec.md`

## Summary

動画エリア・ブックマーク行・ブックマークパネル空白エリアの 3 箇所にコンテキストメニューを実装する。
動画エリアは VLC のネイティブウィンドウ占有を回避するために透明オーバーレイウィジェットを使用する。
ブックマーク行には「A点へジャンプ」「名前を変更」「複製」「削除」を追加し、複製機能のために `BookmarkStore.insert_after` を新規追加する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/bookmarks.json`（BookmarkStore 経由、変更なし）
**Testing**: pytest
**Target Platform**: デスクトップ（Linux / Windows / macOS）
**Project Type**: デスクトップアプリ
**Performance Goals**: コンテキストメニュー表示まで 100ms 以内（標準 UI 期待値）
**Constraints**: VLC が video_frame のネイティブウィンドウを占有するため、透明オーバーレイで右クリックを受信する
**Scale/Scope**: シングルユーザー、ブックマーク件数は最大数百件

## Constitution Check

| 原則 | ステータス | 備考 |
|------|-----------|------|
| I. テストファースト | ✅ | 各ストーリー実装前にユニット/統合テストを作成する |
| II. シンプルさ重視 | ✅ | 既存 QAction オブジェクトを再利用（FR-008）、新規抽象化なし |
| III. 過度な抽象化禁止 | ✅ | QListWidget のサブクラス化は行わない、1箇所だけのヘルパーは作らない |
| IV. 日本語コミュニケーション | ✅ | すべての i18n キーを `t()` 経由で取得する（FR-009） |

**Complexity Tracking**: なし（違反なし）

## Project Structure

### Documentation (this feature)

```text
specs/022-enhance-context-menu/
├── plan.md              # このファイル
├── spec.md              # 機能仕様書
├── research.md          # Phase 0 調査結果
├── data-model.md        # Phase 1 データモデル
├── quickstart.md        # Phase 1 クイックスタート
├── checklists/
│   └── requirements.md  # 品質チェックリスト
└── tasks.md             # Phase 2 タスク（/speckit.tasks コマンドで生成）
```

### Source Code (変更ファイル)

```text
looplayer/
├── bookmark_store.py          # insert_after() メソッドを追加
├── i18n.py                    # ctx.* / bookmark.copy_suffix キーを追加
├── player.py                  # 動画エリアオーバーレイ・コンテキストメニュー実装
└── widgets/
    ├── bookmark_panel.py      # seek_to_ms_requested シグナル・空白エリアメニュー
    └── bookmark_row.py        # jump_to_a_requested / duplicate_requested シグナル追加
                               # _start_rename() 抽出・コンテキストメニュー拡充

tests/
├── unit/
│   ├── test_bookmark_store_insert_after.py   # 新規（US-2 複製）
│   ├── test_bookmark_row_ctx_menu.py         # 新規（US-2 ブックマーク行）
│   └── test_bookmark_panel_ctx_menu.py       # 新規（US-3 パネル空白）
└── integration/
    └── test_video_ctx_menu.py                # 新規（US-1 動画エリア）
```

**Structure Decision**: シングルプロジェクト構成（既存構造に変更なし）

---

## Phase 0: Outline & Research

詳細は [research.md](research.md) 参照。

### 解決済み NEEDS CLARIFICATION

1. **VLC マウスイベント横取り問題** → 透明オーバーレイ QWidget（`_video_ctx_overlay`）を video_frame の子として配置する
2. **BookmarkStore.insert_after の欠如** → 新規メソッドとして追加する（末尾追加 API を破壊しない）
3. **rename ロジックの再利用** → `_start_rename()` メソッドに抽出する
4. **「A点へジャンプ」シグナルチェーン** → `BookmarkRow.jump_to_a_requested` → `BookmarkPanel.seek_to_ms_requested` → `VideoPlayer._on_seek_to_ms`
5. **パネル空白エリアの検出** → `list_widget.itemAt(pos) is None` で判定する

---

## Phase 1: Design & Contracts

詳細は [data-model.md](data-model.md) 参照。

### User Story 1: 動画エリアの右クリックメニュー（P1）

**実装設計**

```
player.py
├── _build_video_context_overlay()        # 透明 QWidget 生成・接続
│   ├── QWidget(video_frame)
│   ├── WA_TranslucentBackground 設定
│   ├── setContextMenuPolicy(CustomContextMenu)
│   └── customContextMenuRequested → _show_video_context_menu
├── _show_video_context_menu(pos)         # メニュー表示
│   ├── 「再生 / 一時停止」← toggle_play アクション再利用
│   ├── 「停止」← stop アクション再利用
│   ├── セパレータ
│   ├── 「A点を設定」← set_point_a アクション再利用（ファイル未開時 disabled）
│   ├── 「B点を設定」← set_point_b アクション再利用（ファイル未開時 disabled）
│   ├── 「ここにブックマークを追加」← A/B 両方設定時のみ有効
│   ├── セパレータ
│   ├── 「スクリーンショット」← _screenshot_action 再利用（動画未開時 disabled）
│   └── 「フルスクリーン切り替え」← fullscreen_action 再利用
└── resizeEvent 更新
    └── _video_ctx_overlay.resize(video_frame.size())（既存 resizeEvent に追記）
```

**コンテキストメニューのアクション有効/無効条件**

| 項目 | 有効条件 |
|------|---------|
| 再生 / 一時停止 | ファイル開放時 |
| 停止 | ファイル開放時 |
| A点を設定 | ファイル開放時 |
| B点を設定 | ファイル開放時 |
| ここにブックマークを追加 | `ab_point_a is not None and ab_point_b is not None` |
| スクリーンショット | `_screenshot_action.isEnabled()` に依存（既存ロジック） |
| フルスクリーン切り替え | 常時有効 |

---

### User Story 2: ブックマーク行の右クリックメニュー拡充（P2）

**bookmark_store.py 変更**

```python
def insert_after(self, video_path: str, bookmark: LoopBookmark, after_id: str) -> None:
    bms = self._data.get(video_path, [])
    sorted_bms = sorted(bms, key=lambda b: b.order)
    # after_id が見つからない場合は末尾に追加（フォールバック）
    after_idx = next(
        (i for i, b in enumerate(sorted_bms) if b.id == after_id),
        len(sorted_bms) - 1
    )
    if not bookmark.name:
        bookmark.name = f"ブックマーク {len(sorted_bms) + 1}"
    sorted_bms.insert(after_idx + 1, bookmark)
    for i, b in enumerate(sorted_bms):
        b.order = i
    self._data[video_path] = sorted_bms
    self._save_all()
```

**bookmark_row.py 変更**

```python
# 追加シグナル
jump_to_a_requested = pyqtSignal(str)   # bookmark_id
duplicate_requested = pyqtSignal(str)   # bookmark_id

# _start_rename() 抽出（eventFilter から移動）
def _start_rename(self) -> None:
    new_name, ok = QInputDialog.getText(
        self, t("bookmark.name.edit_title"), t("bookmark.name.edit_prompt"),
        text=self.name_label.text()
    )
    if ok and new_name.strip():
        self.name_label.setText(new_name.strip())
        self.name_changed.emit(self.bookmark_id, new_name.strip())

# _show_context_menu 拡充
def _show_context_menu(self, pos) -> None:
    menu = QMenu(self)
    jump_action = QAction(t("ctx.jump_to_a"), self)
    jump_action.triggered.connect(lambda: self.jump_to_a_requested.emit(self.bookmark_id))
    menu.addAction(jump_action)
    menu.addSeparator()
    rename_action = QAction(t("ctx.rename"), self)
    rename_action.triggered.connect(self._start_rename)
    menu.addAction(rename_action)
    dup_action = QAction(t("ctx.duplicate"), self)
    dup_action.triggered.connect(lambda: self.duplicate_requested.emit(self.bookmark_id))
    menu.addAction(dup_action)
    del_action = QAction(t("ctx.delete"), self)
    del_action.triggered.connect(lambda: self.deleted.emit(self.bookmark_id))
    menu.addAction(del_action)
    menu.addSeparator()
    menu.addAction(self._export_clip_action)   # 既存（A/B未設定時 disabled）
    menu.addAction(self._reset_play_count_action)  # 既存
    menu.exec(self.mapToGlobal(pos))
```

**bookmark_panel.py 変更**

```python
# 追加シグナル
seek_to_ms_requested = pyqtSignal(int)  # ms

# _refresh_list() 内に追加接続
row.jump_to_a_requested.connect(self._on_jump_to_a)
row.duplicate_requested.connect(self._on_duplicate)

# ハンドラ追加
def _on_jump_to_a(self, bookmark_id: str) -> None:
    if self._video_path is None:
        return
    bms = self._store.get_bookmarks(self._video_path)
    bm = next((b for b in bms if b.id == bookmark_id), None)
    if bm is not None:
        self.seek_to_ms_requested.emit(bm.point_a_ms)

def _on_duplicate(self, bookmark_id: str) -> None:
    if self._video_path is None:
        return
    bms = self._store.get_bookmarks(self._video_path)
    bm = next((b for b in bms if b.id == bookmark_id), None)
    if bm is None:
        return
    from dataclasses import replace as _dc_replace
    new_bm = _dc_replace(
        bm,
        id=str(__import__("uuid").uuid4()),
        name=bm.name + t("bookmark.copy_suffix"),
        play_count=0,
    )
    self._store.insert_after(self._video_path, new_bm, after_id=bookmark_id)
    self._refresh_list()
```

---

### User Story 3: ブックマークパネル空白エリアの右クリックメニュー（P3）

**bookmark_panel.py 変更（追記）**

```python
# _build_ui() 内の list_widget 設定に追加
self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self.list_widget.customContextMenuRequested.connect(self._show_panel_context_menu)

# メニュー表示ハンドラ（空白エリアのみ）
def _show_panel_context_menu(self, pos) -> None:
    if self.list_widget.itemAt(pos) is not None:
        return  # 行クリックは BookmarkRow が処理するため無視
    menu = QMenu(self)
    import_action = QAction(t("ctx.import_bookmarks"), self)
    import_action.triggered.connect(self._request_import)
    menu.addAction(import_action)
    export_action = QAction(t("ctx.export_bookmarks"), self)
    export_action.setEnabled(
        self._video_path is not None
        and bool(self._store.get_bookmarks(self._video_path))
    )
    export_action.triggered.connect(self._request_export)
    menu.addAction(export_action)
    menu.exec(self.list_widget.mapToGlobal(pos))
```

パネルのインポート/エクスポートは player.py の既存メソッド（`_import_bookmarks`, `_export_bookmarks`）を呼ぶ。
BookmarkPanel に新シグナル `import_requested = pyqtSignal()` と `export_requested_panel = pyqtSignal()` を追加し、player.py で接続する（既存の `export_requested` は BookmarkRow からの clip export シグナルと名前が衝突するため別名を使用）。

```python
# BookmarkPanel 追加シグナル
import_requested = pyqtSignal()
export_from_panel_requested = pyqtSignal()

# 接続（player.py _build_ui 内）
self.bookmark_panel.import_requested.connect(self._import_bookmarks)
self.bookmark_panel.export_from_panel_requested.connect(self._export_bookmarks)
```

---

## Agent Context Update

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

追加技術: なし（既存スタック内での実装）

---

## 実装チェックポイント

各ストーリーを実装する際は以下の順序を守る（Constitution I: テストファースト）:

1. テストを書く
2. テストが **失敗する** ことを確認する
3. 最小限のコードで **通過させる**
4. リファクタリング

コミットタイミング:
- テスト作成後（赤フェーズ）
- 実装完了後（緑フェーズ）
- 各ユーザーストーリー完了後
