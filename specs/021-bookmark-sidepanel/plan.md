# Implementation Plan: Bookmark Side Panel Toggle

**Branch**: `021-bookmark-sidepanel` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/021-bookmark-sidepanel/spec.md`

## Summary

ブックマーク一覧（＋プレイリスト）パネルを動画右側のサイドパネルとして表示・非表示切り替えできるようにする。`QSplitter(Horizontal)` を導入し、現在 `controls_layout` 下部に配置されている `_panel_tabs` を右ペインへ移動する最小変更レイアウト改修。表示状態・幅は `AppSettings` に永続化し、フルスクリーン時は自動非表示・復元する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/settings.json`（AppSettings — 既存ファイルに 2 フィールド追加）
**Testing**: pytest（ユニットテスト + 統合テスト）
**Target Platform**: Linux / macOS / Windows デスクトップ
**Project Type**: デスクトップアプリ（PyQt6 GUI）
**Performance Goals**: パネル表示・非表示の切り替えが視覚的に即座（フレーム遅延なし）
**Constraints**: パネル最小幅 240px、動画エリア最小幅 320px、既存テスト全通過（リグレッションゼロ）
**Scale/Scope**: 単一ウィンドウアプリ。変更ファイル 3 件（player.py, app_settings.py, i18n.py）+ テスト追加

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 事前チェック | 事後チェック（Phase 1 後） |
|------|-------------|--------------------------|
| **I. テストファースト** | ✅ テストを先に書く。ユニット（AppSettings 新フィールド・トグルロジック）と統合テスト（UI 操作）を計画済み | ✅ quickstart.md にテスト実行コマンド記載。tasks.md でテスト先行タスクを定義予定 |
| **II. シンプルさ重視** | ✅ QSplitter は PyQt6 標準ウィジェット。新規クラス不要。既存 AppSettings パターンを踏襲 | ✅ 追加コードは最小限。QDockWidget 等の過剰な機能は不採用（research.md Decision 1）|
| **III. 過度な抽象化の禁止** | ✅ ヘルパークラス・ラッパーなし。`_toggle_bookmark_panel()` と `_apply_initial_panel_width()` の 2 メソッドのみ追加 | ✅ 1 箇所のみの処理を直接実装。Complexity Tracking 不要 |
| **IV. 日本語コミュニケーション** | ✅ i18n キー・コミットメッセージ・仕様書を日本語で記述 | ✅ 新 i18n キー（`menu.view.bookmark_panel`, `shortcut.bookmark_panel`）日本語・英語対応 |

**判定**: 全原則 PASS。Complexity Tracking 記録不要。

## Project Structure

### Documentation (this feature)

```text
specs/021-bookmark-sidepanel/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: 7 design decisions
├── data-model.md        # Phase 1: layout diff, new fields, new methods
├── quickstart.md        # Phase 1: implementation guide with code snippets
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
looplayer/
├── player.py              # QSplitter 導入・メニュー追加・フルスクリーン連動・リサイズ修正
├── app_settings.py        # bookmark_panel_visible, bookmark_panel_width フィールド追加
└── i18n.py                # menu.view.bookmark_panel, shortcut.bookmark_panel キー追加

tests/
├── unit/
│   ├── test_app_settings_panel.py     # 新規: AppSettings 新フィールドのユニットテスト
│   └── test_bookmark_panel_toggle.py  # 新規: トグルロジックのユニットテスト
└── integration/
    └── test_bookmark_panel_ui.py      # 新規: UI 操作の統合テスト
```

**Structure Decision**: 単一プロジェクト構成。変更対象は `looplayer/` 配下の 3 ファイルのみ。新規テストファイルを `tests/unit/` と `tests/integration/` にそれぞれ追加する。既存ファイルへの変更は最小限（新メソッド 2 件追加、既存メソッド 5 件修正、既存テストへの影響なし）。

## Implementation Design

### Phase 1 成果物

| 成果物 | ステータス | 概要 |
|--------|-----------|------|
| `research.md` | ✅ 完了 | QSplitter 採用理由・代替案・7 決定事項 |
| `data-model.md` | ✅ 完了 | レイアウト差分・新フィールド・新メソッド一覧 |
| `quickstart.md` | ✅ 完了 | 実装コードスニペット・動作確認チェックリスト |

### 変更概要

#### `looplayer/app_settings.py`

`mirror_display` プロパティ直後に 2 フィールド追加（詳細: `data-model.md` §1）:
- `bookmark_panel_visible: bool` — デフォルト `False`
- `bookmark_panel_width: int` — デフォルト `280`（最小クランプ 240px）

#### `looplayer/i18n.py`

`menu.view` セクションおよび `shortcut.*` セクションに 2 キー追加（詳細: `data-model.md` §2）:
- `menu.view.bookmark_panel`: `"ブックマークパネル (&B)"` / `"Bookmark Panel (&B)"`
- `shortcut.bookmark_panel`: `"ブックマークパネル 表示切り替え (B)"` / `"Toggle bookmark panel (B)"`

#### `looplayer/player.py`

以下 7 か所を変更（詳細: `quickstart.md` §2〜§8）:

1. **`_setup_ui()`**: `controls_layout.addWidget(self._panel_tabs)` を削除し、`QSplitter` 経由のレイアウトに置き換え
2. **`_apply_initial_panel_width()` 追加**: 起動時に AppSettings からパネル幅を遅延復元
3. **`_toggle_bookmark_panel()` 追加**: 表示切り替え・幅保存・AppSettings 更新・メニュー同期
4. **`_setup_view_menu()`**: `mirror_action` 直後に `_bookmark_panel_action` 追加
5. **`_enter_fullscreen_overlay_mode()`**: `_panel_tabs_was_visible` 保存 + `_panel_tabs.hide()`
6. **`_exit_fullscreen_overlay_mode()`**: `_panel_tabs_was_visible` に応じて `_panel_tabs.show()`
7. **`_resize_to_video()`**: パネル表示中はターゲット幅にパネル幅を加算
8. **`closeEvent()`**: パネル表示中なら幅を AppSettings に保存

### テスト戦略

| テストファイル | 種別 | カバーする要件 |
|---------------|------|--------------|
| `tests/unit/test_app_settings_panel.py` | ユニット | `bookmark_panel_visible` 読み書き・デフォルト値、`bookmark_panel_width` 最小クランプ（240px）|
| `tests/unit/test_bookmark_panel_toggle.py` | ユニット | `_toggle_bookmark_panel()` の表示・非表示ロジック、幅保存タイミング |
| `tests/integration/test_bookmark_panel_ui.py` | 統合 | B キー操作・メニュー選択・フルスクリーン連動・起動時状態復元 |

**全テスト通過**: `pytest tests/ -v` でリグレッションゼロを確認（SC-006）

## Complexity Tracking

> 憲法違反なし。追加コードはすべて PyQt6 標準ウィジェットと既存パターンの範囲内。記録不要。
