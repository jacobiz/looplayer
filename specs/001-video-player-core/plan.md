# Implementation Plan: ビデオプレイヤーコア機能

**Branch**: `001-video-player-core` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-video-player-core/spec.md`

## Summary

Python/PyQt6 + VLC を使ったデスクトップ動画プレイヤーのコア機能実装。
既存の `main.py` に対してテストスイートを整備し、未実装仕様（エラーハンドリング・
アスペクト比保持）を追加する。既存コードはほぼ仕様を満たしているため、
差分実装と pytest/pytest-qt によるテスト追加が主作業となる。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A（セッション状態はメモリのみ、永続化なし）
**Testing**: pytest + pytest-qt
**Target Platform**: Linux デスクトップ（WSL2/WSLg）、クロスプラットフォーム対応
**Project Type**: desktop-app
**Performance Goals**: ファイル開始 < 3秒、シーク反映 < 1秒、UI更新間隔 ~200ms
**Constraints**: ローカルファイルのみ、シングルウィンドウ、シングルファイル同時再生
**Scale/Scope**: シングルユーザー、セッションあたり1ファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 判定 | 詳細 |
|------|------|------|
| I. テストファースト | ✅ PASS | タスクではテストを実装より先に書く。pytest-qt を使用 |
| II. シンプルさ重視 | ✅ PASS | 単一ファイル構成を維持。不要な抽象化なし |
| III. 過度な抽象化の禁止 | ✅ PASS | Repository/Service/Factory パターン不使用 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・仕様書・コミットメッセージは日本語 |

**Constitution Check: PASSED — Phase 0 へ進む**

## Project Structure

### Documentation (this feature)

```text
specs/001-video-player-core/
├── plan.md              # このファイル
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks で生成)
```

### Source Code (repository root)

```text
main.py                  # メインアプリ（既存・差分追加あり）
requirements.txt         # 依存定義（pytest-qt 追加）
tests/
├── unit/
│   ├── test_ms_to_str.py        # _ms_to_str ヘルパー関数
│   └── test_ab_loop_logic.py    # ABループ判定ロジック
└── integration/
    ├── test_playback.py          # 再生制御（pytest-qt / qtbot）
    └── test_ab_loop.py           # ABループ操作フロー（pytest-qt / qtbot）
```

**Structure Decision**: 既存の単一ファイル構成（`main.py`）を維持する。
テストは `tests/unit/` と `tests/integration/` に分離して配置する。
新規クラス・モジュールは追加しない（シンプルさ重視の原則に従う）。

## Complexity Tracking

> 憲法違反なし。追記不要。
