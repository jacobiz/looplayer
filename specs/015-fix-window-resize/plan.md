# Implementation Plan: ウィンドウサイズを動画サイズに合わせる機能のバグ修正

**Branch**: `015-fix-window-resize` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-fix-window-resize/spec.md`

## Summary

「ウィンドウサイズを動画サイズに合わせる」メニュー機能に存在する 4 つのバグを修正する。
主要な修正は `_resize_to_video` の高さ計算（UIコントロール分のオフセット未考慮）であり、
加えてポーリングタイムアウト追加とデッドコード削除を行う。
変更は `looplayer/player.py` のみに限定され、新規テストを `tests/unit/test_window_resize.py` に追加する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A
**Testing**: pytest + pytest-qt
**Target Platform**: Windows / macOS / Linux デスクトップ
**Project Type**: desktop-app
**Performance Goals**: リサイズ処理は即時（知覚遅延なし）、ポーリングタイムアウト ≤ 5秒
**Constraints**: 既存の最小ウィンドウサイズクランプ（幅 800px・高さ 600px）を維持
**Scale/Scope**: player.py 単一ファイルへの局所的変更

## Constitution Check

| 原則 | 状態 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | test_window_resize.py を実装前に作成し FAIL を確認してから実装 |
| II. シンプルさ重視 | ✅ PASS | player.py のみ変更、カウンタ変数1つ追加のみ |
| III. 過度な抽象化の禁止 | ✅ PASS | 新規クラス・ヘルパーなし |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットメッセージは日本語 |

## Project Structure

### Documentation (this feature)

```text
specs/015-fix-window-resize/
├── plan.md         ← このファイル
├── research.md     ← Phase 0 output
├── quickstart.md   ← Phase 1 output
└── tasks.md        ← /speckit.tasks output
```

### Source Code (repository root)

```text
looplayer/
└── player.py                      # 修正対象（_resize_to_video, _poll_video_size, _start_size_poll）

tests/
└── unit/
    └── test_window_resize.py      # 新規テスト
```

**Structure Decision**: 既存プロジェクト構造に完全準拠。新規ファイルはテストのみ。

## Implementation Design

### Bug 1: UIオフセット未考慮（FR-001 / SC-001）

**修正前**:
```python
def _resize_to_video(self, w: int, h: int) -> None:
    target_w = max(800, min(w, max_w))
    target_h = max(600, min(h, max_h))   # ← UIコントロール分が未加算
    self.resize(target_w, target_h)
```

**修正後**:
```python
def _resize_to_video(self, w: int, h: int) -> None:
    ui_h_offset = self.height() - self.video_frame.height()  # タイトルバー+コントロール分
    target_w = max(800, min(w, max_w))
    target_h = max(600, min(h + ui_h_offset, max_h))  # ← オフセット加算
    self.resize(target_w, target_h)
```

### Bug 2: ポーリングタイムアウトなし（FR-002 / SC-002）

**修正**: `_size_poll_count` カウンタを追加し 100回（5秒）で強制停止

```python
def _start_size_poll(self) -> None:
    self._size_poll_count = 0          # カウンタリセット
    self._size_poll_timer.start()

def _poll_video_size(self) -> None:
    self._size_poll_count += 1
    if self._size_poll_count >= 100:   # 5秒タイムアウト
        self._size_poll_timer.stop()
        return
    w, h = self.media_player.video_get_size()
    if w and h:
        self._size_poll_timer.stop()
        self._resize_to_video(w, h)
```

### Bug 3 & 4: デッドコード削除（FR-004, FR-005）

- `_start_size_poll` から `self._user_resized = False` を削除
- `_on_vlc_video_changed` メソッド全体を削除

## テスト設計

| テストクラス | テスト内容 | 対応 FR |
|-------------|-----------|---------|
| `TestResizeToVideo` | UIオフセットが加算されていること | FR-001 |
| `TestResizeToVideo` | フルスクリーン時はスキップ | FR-006 |
| `TestResizeToVideo` | 画面クランプ動作 | FR-007 |
| `TestPollTimeout` | 100回でタイマー停止 | FR-002 |
| `TestPollTimeout` | サイズ取得時は即停止 | FR-003 |
| `TestDeadCode` | `_user_resized` が存在しない | FR-004 |
| `TestDeadCode` | `_on_vlc_video_changed` が存在しない | FR-005 |

## 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `looplayer/player.py` | 修正 | `_resize_to_video`, `_poll_video_size`, `_start_size_poll` の改修、`_on_vlc_video_changed` 削除 |
| `tests/unit/test_window_resize.py` | 新規 | US1〜US3 のユニットテスト |
