# Implementation Plan: AB ループ区間クリップ書き出し

**Branch**: `011-clip-export` | **Date**: 2026-03-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-clip-export/spec.md`

## Summary

AB ループの A点〜B点区間を ffmpeg ストリームコピーで書き出す機能。「ファイル」メニューに「クリップを書き出す...」項目を追加し、バックグラウンド QThread で ffmpeg subprocess を実行する。既存の `DownloadThread` / `DownloadDialog` パターン（`updater.py`）を踏襲してシンプルに実装する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203（既存）、ffmpeg（外部依存・PATH 検索）
**Storage**: N/A（出力はユーザー指定パス、アプリ設定への変更なし）
**Testing**: pytest + pytest-qt（既存）
**Target Platform**: Windows 10+、macOS 12+（デスクトップアプリ）
**Project Type**: desktop-app
**Performance Goals**: 30秒の区間を5秒以内に書き出し（ストリームコピー前提）
**Constraints**: ffmpeg 外部依存・同梱なし、再エンコードなし、同時書き出し1件のみ
**Scale/Scope**: シングルユーザー・デスクトップアプリ

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 判定 | 根拠 |
|------|------|------|
| I. テストファースト | PASS | ExportWorker・ExportProgressDialog のユニットテストを実装前に作成する |
| II. シンプルさ重視 | PASS | QThread + subprocess の直接呼び出し。updater.py の DownloadThread パターンを再利用 |
| III. 過度な抽象化の禁止 | PASS | 「ExportEngine」インターフェースは設けない。ExportWorker に直接実装する |
| IV. 日本語コミュニケーション | PASS | UIラベル・コメント・コミットメッセージを日本語で記述 |

**Complexity Tracking**: 違反なし、記録不要

## Project Structure

### Documentation (this feature)

```text
specs/011-clip-export/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
looplayer/
├── clip_export.py           # ClipExportJob (dataclass) + ExportWorker (QThread) [新規]
├── widgets/
│   └── export_dialog.py     # ExportProgressDialog (QDialog) [新規]
└── player.py                # 「クリップを書き出す...」メニュー項目の追加 [修正]

tests/
├── unit/
│   └── test_clip_export.py           # ExportWorker シグナルテスト（subprocess モック）[新規]
└── integration/
    └── test_clip_export_integration.py  # player メニュー統合テスト [新規]
```

**Structure Decision**: 既存の looplayer/ パッケージに2ファイルを追加する最小構成。updater.py と同様のパターンで実装する。

## Phase 0: Research Summary

→ 詳細は [research.md](./research.md) 参照

- **ffmpeg コマンド**: `ffmpeg -ss START -to END -i INPUT -c copy OUTPUT -y`（`-ss` を `-i` の前に置くことで高速キーフレームシーク）
- **ffmpeg 検出**: `shutil.which("ffmpeg")` を書き出し実行時に呼ぶ（遅延検出）
- **キャンセル**: `proc.terminate()` + `proc.wait(timeout=5)` で SIGTERM 送信後待機
- **QThread パターン**: updater.py の DownloadThread と同一パターン
- **不確定プログレスバー**: `QProgressBar.setRange(0, 0)` で往復アニメーション表示

## Phase 1: Design

→ 詳細は [data-model.md](./data-model.md) 参照

### ファイル別の責務

| ファイル | クラス | 責務 |
|---------|--------|------|
| `looplayer/clip_export.py` | `ClipExportJob` | 書き出しジョブのデータ（dataclass） |
| `looplayer/clip_export.py` | `ExportWorker` | ffmpeg subprocess を QThread で実行。シグナル: `finished(str)`, `failed(str)` |
| `looplayer/widgets/export_dialog.py` | `ExportProgressDialog` | 不確定プログレスバー + キャンセルボタン。ExportWorker を内包 |
| `looplayer/player.py` | `VideoPlayer` | 「クリップを書き出す...」メニュー項目、AB ループ状態に応じた有効/無効切り替え |

### メニュー統合

- 「ファイル」メニュー末尾（セパレーター後）に「クリップを書き出す... (Ctrl+E)」を追加
- A点とB点がともに設定されている場合のみ有効
- AB ループ状態変更時（set_a / set_b / clear）に action の enabled を更新

### デフォルトファイル名生成

```
{元ファイルのstem}_{A点 mm'm'ss's'}-{B点 mm'm'ss's'}{元ファイルの拡張子}
例: lecture_00m15s-01m30s.mp4
```

### ffmpeg コマンド（確定版）

```bash
ffmpeg -ss {start_hms} -to {end_hms} -i {input} -c copy {output} -y
```

- `-ss` を `-i` 前に置く: キーフレーム精度の高速シーク
- `-y`: 出力ファイルの上書き確認を抑止（OS ダイアログで事前確認済み）
- `-c copy`: ストリームコピー（映像・音声）
