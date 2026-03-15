# Implementation Plan: プレイヤーメニュー基本機能

**Branch**: `003-player-menus` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-player-menus/spec.md`

## Summary

メニューバー（ファイル・再生・表示）と音量スライダーを追加し、キーボードショートカット・フルスクリーン・再生速度・常に最前面の機能を実装する。既存の `looplayer/player.py` に全変更を集約し、コントロール群を `controls_panel` コンテナでラップしてフルスクリーン時の一括 hide/show を実現する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203（既存）
**Storage**: N/A（状態はメモリのみ、音量・速度は永続化しない）
**Testing**: pytest + pytest-qt
**Target Platform**: Linux / Windows / macOS デスクトップ
**Project Type**: desktop-app
**Performance Goals**: メニュー操作・キー応答は即時（<50ms）
**Constraints**: 既存ボタン群を削除しない（メニューと併存）
**Scale/Scope**: 単一ウィンドウ、単一ユーザー

## Constitution Check

| 原則 | 評価 | 備考 |
|------|------|------|
| I. テストファースト | ✓ PASS | 各タスク前にテストを作成 |
| II. シンプルさ重視 | ✓ PASS | 新モジュール不要、player.py 内に完結 |
| III. 過度な抽象化の禁止 | ✓ PASS | controls_panel コンテナのみ（Complexity Tracking に記録） |
| IV. 日本語コミュニケーション | ✓ PASS | UIラベル・コメント日本語 |

**Gate status: PASS → Phase 0 開始**

## Project Structure

### Documentation (this feature)

```text
specs/003-player-menus/
├── plan.md          ← This file
├── research.md      ← Phase 0 output
├── data-model.md    ← Phase 1 output
├── quickstart.md    ← Phase 1 output
└── tasks.md         ← /speckit.tasks output
```

### Source Code Changes

```text
looplayer/
└── player.py          ← 全変更をここに集約（新モジュール不要）

tests/
├── unit/
│   ├── test_volume_controls.py    ← 音量・ミュート状態の単体テスト（新規）
│   └── test_playback_speed.py     ← 再生速度状態の単体テスト（新規）
└── integration/
    ├── test_menus.py              ← メニュー・ショートカット統合テスト（新規）
    └── test_fullscreen.py         ← フルスクリーン統合テスト（新規）
```

**Structure Decision**: 新機能はすべて既存の `VideoPlayer` クラスに追加する。新たなモジュール分割は行わない（憲法 III 遵守）。

## Architecture Design

### controls_panel パターン（フルスクリーン対応）

フルスクリーン時にコントロール群を一括 hide するため、`_build_ui()` 内のコントロール類を `controls_panel`（`QWidget`）でラップする。

```
QMainWindow
└── central_widget (QVBoxLayout)
    ├── video_frame          ← 映像（常時表示）
    └── controls_panel       ← コントロール群コンテナ
        └── controls_layout (QVBoxLayout)
            ├── volume_bar   ← 音量スライダー + ラベル（新規）
            ├── seek_layout  ← シークバー（既存）
            ├── ctrl_layout  ← 再生ボタン群（既存）
            ├── ab_layout    ← ABループコントロール（既存）
            ├── bookmark_save_layout （既存）
            └── bookmark_panel       （既存）
```

フルスクリーン時: `self.controls_panel.hide(); self.menuBar().hide()`
復帰時: `self.controls_panel.show(); self.menuBar().show()`

### メニュー構成

```
ファイル(F)
  └── 開く...  (Ctrl+O)
  └── ──────
  └── 終了     (Ctrl+Q)

再生(P)
  └── 再生/一時停止  (Space)
  └── 停止
  └── ──────
  └── 音量を上げる   (↑)
  └── 音量を下げる   (↓)
  └── ミュート       (M)
  └── ──────
  └── 再生速度 ▶
        └── 0.5倍
        └── 0.75倍
        └── 標準 (1.0倍) [checked by default]
        └── 1.25倍
        └── 1.5倍
        └── 2.0倍

表示(V)
  └── フルスクリーン     (F)
  └── ──────
  └── 常に最前面に表示  [toggle, checkable]
```

### 音量管理

- VLC `audio_set_volume(0-100)` / `audio_get_volume()` を使用
- `self._volume: int = 80`（初期値 80%）
- `self._pre_mute_volume: int`（ミュート前の音量を保存）
- `self._is_muted: bool = False`
- ファイルオープン時に音量はリセットしない（設定を維持）

### 再生速度管理

- VLC `set_rate(float)` を使用
- `self._playback_rate: float = 1.0`
- ファイルオープン時に `set_rate(1.0)` でリセット（FR-012）
- `QActionGroup` で排他選択

### フルスクリーン管理

- `self._is_fullscreen: bool = False`
- `showFullScreen()` / `showNormal()`
- FR-016: フルスクリーン中のメニューバー自動表示
  - `video_frame.setMouseTracking(True)`
  - `mouseMoveEvent`: マウスが画面上部15px以内 → `menuBar().show()`
  - `QTimer`（2秒）: タイムアウト → `menuBar().hide()`

### キーボードショートカット

`QAction.setShortcut()` を使用（メニューと一体化）。メニューに対応しない単独ショートカットはなし（全操作がメニュー経由で利用可能）。

## Complexity Tracking

| 複雑さ | 理由 | 却下した代替案 |
|--------|------|---------------|
| controls_panel コンテナ追加 | フルスクリーン時に非表示にする UI 要素が6つ以上あり、個別 hide/show は保守困難 | 個別 hide/show → 追加/削除のたびに漏れが発生するリスク |
| FR-016 マウス追跡 + QTimer | スペックで要求されているため回避不可 | フルスクリーン中にメニューバーを常時非表示のみにする → FR-016 違反 |
