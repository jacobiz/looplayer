# Implementation Plan: シークバークリックシーク

**Branch**: `008-seekbar-click-seek` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-seekbar-click-seek/spec.md`

## Summary

`BookmarkSlider`（`looplayer/widgets/bookmark_slider.py`）に `mousePressEvent` の拡張と `mouseMoveEvent` の追加を行い、シークバートラックのクリック・ドラッグで `seek_requested = pyqtSignal(int)` を emit する。`VideoPlayer` 側でこのシグナルを受け取り `set_time(ms)` を呼び出す。既存の `bookmark_bar_clicked` シグナル（ブックマーク区間バークリック）の優先度は変更しない。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A（永続データなし）
**Testing**: pytest
**Target Platform**: Windows / macOS デスクトップ
**Project Type**: desktop-app
**Performance Goals**: クリックからシーク更新まで視覚的に感知できない遅延（< 1フレーム相当）
**Constraints**: 既存の `BookmarkSlider` 継承構造を維持、新規クラスを作らない
**Scale/Scope**: 単一ウィジェットへの変更（約 30 行追加）+ VideoPlayer への接続（約 5 行）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | Status | 根拠 |
|------|--------|------|
| I. テストファースト | ✅ PASS | ユニットテスト → 実装の順序を tasks.md に明記する |
| II. シンプルさ重視 | ✅ PASS | 既存クラスへの最小追加（mouseMoveEvent + シグナル1本）のみ |
| III. 過度な抽象化の禁止 | ✅ PASS | ヘルパークラス・マネージャー不要。直接メソッド追加 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットメッセージ・仕様書すべて日本語 |

違反なし。Complexity Tracking 記入不要。

## Project Structure

### Documentation (this feature)

```text
specs/008-seekbar-click-seek/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── contracts/
│   └── ui-signals.md    # Phase 1 output（シグナルインターフェース契約）
├── quickstart.md        # Phase 1 output（手動テストシナリオ）
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
looplayer/
├── widgets/
│   └── bookmark_slider.py   # 変更: seek_requested シグナル追加、mousePressEvent 拡張、mouseMoveEvent/mouseReleaseEvent 追加
└── player.py                # 変更: seek_requested シグナル接続、_on_seek_ms() 追加

tests/
├── unit/
│   └── test_bookmark_slider.py  # 変更: クリックシーク・ドラッグシークのテスト追加
└── integration/
    └── (既存テストのリグレッション確認)
```

**Structure Decision**: 単一プロジェクト構成。変更は `bookmark_slider.py`（ウィジェット層）と `player.py`（アプリ層）の 2 ファイルのみ。新規ファイルは不要。
