# Implementation Plan: Windows スタンドアロンアプリ インストーラ

**Branch**: `006-windows-installer` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-windows-installer/spec.md`

## Summary

PyInstaller で Python + PyQt6 + VLC をバンドルした単一 .exe を生成し、Inno Setup でインストーラを作成する。GitHub Actions のバージョンタグトリガーで自動ビルド・GitHub Releases への公開を実現する。ウィザード UI は日英 2 言語対応（Windows システム言語で自動切替）。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyInstaller（バンドラー）、Inno Setup（インストーラフレームワーク）、既存の PyQt6 6.10.2 + python-vlc 3.0.21203
**Storage**: N/A（インストーラはビルド成果物）
**Testing**: Windows 実機手動テスト（インストーラの性質上、Linux CI での自動テスト不可）
**Target Platform**: Windows 10/11 64bit
**Project Type**: Desktop app + ビルドツール（インストーラ生成パイプライン）
**Performance Goals**: インストール完了まで 5 分以内（SC-001）、インストーラサイズ 200MB 以下（SC-002）
**Constraints**: 管理者権限不要（ユーザースコープ）、Python 未インストール環境で動作

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 判定 | 備考 |
|------|------|------|
| I. テストファースト | ⚠️ 条件付きクリア | インストーラビルドは Windows 実機テストが必要。`looplayer/player.py` の VLC パス修正は既存テストでカバー可能。インストーラ自体の自動テストは本スコープ外だが、手動テストチェックリストを `quickstart.md` に定義する |
| II. シンプルさ重視 | ✅ クリア | PyInstaller + Inno Setup は業界標準の最小構成。追加の抽象化レイヤーなし |
| III. 過度な抽象化の禁止 | ✅ クリア | `.spec` ファイルと `.iss` スクリプトは直接的な設定ファイル |
| IV. 日本語コミュニケーション | ✅ クリア | インストーラスクリプトのコメント・コミットメッセージは日本語で記述 |

**⚠️ Constitution 例外事項（Complexity Tracking に記録）**: テストファーストの原則はインストーラビルド成果物には完全適用不可。Windows 環境依存のため。

## Project Structure

### Documentation (this feature)

```text
specs/006-windows-installer/
├── plan.md           # このファイル
├── research.md       # Phase 0 出力
├── data-model.md     # Phase 1 出力
├── quickstart.md     # Phase 1 出力
└── tasks.md          # Phase 2 出力（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
looplayer/
└── version.py              # バージョン定数（新規）

installer/
├── looplayer.spec          # PyInstaller 設定（新規）
├── looplayer.iss           # Inno Setup スクリプト（新規）
└── build.ps1               # ローカルビルドスクリプト（新規）

.github/workflows/
├── build-windows.yml       # 既存（修正: main ブランチトリガーを更新）
└── release.yml             # バージョンタグトリガーのリリースワークフロー（新規）
```

**Structure Decision**: 既存のプロジェクト構造に `installer/` ディレクトリを追加するだけ。`looplayer/` パッケージへの変更は `version.py` と `player.py` の最小限の修正のみ。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| テストファーストの部分適用除外 | インストーラ .exe は Windows 実機がないと動作確認不可。Linux CI 環境では PyInstaller ビルドまでしか検証できない | Wine でのクロスコンパイルは信頼性が低く、CI コストに見合わない |

## Phase 0: Research 完了

→ 詳細は [research.md](research.md) を参照

**主要決定**:
- バンドラー: **PyInstaller**（既存ワークフローを継続）
- インストーラ: **Inno Setup**（日英自動切替、自動ロールバック、無料）
- 配布: **GitHub Releases**（`gh release create` でタグトリガー自動公開）
- VLC バンドル: `installer/looplayer.spec` で DLL + plugins を明示指定

## Phase 1: Design 完了

→ 詳細は [data-model.md](data-model.md)、[quickstart.md](quickstart.md) を参照

### 実装コンポーネント

| コンポーネント | 説明 | 依存 |
|--------------|------|------|
| `looplayer/version.py` | VERSION・APP_NAME・PUBLISHER 定数 | なし |
| `looplayer/player.py` 修正 | VLC_PLUGIN_PATH 設定（frozen 時のみ）、タイトルにバージョン表示 | version.py |
| `installer/looplayer.spec` | PyInstaller 設定（VLC DLL + plugins バンドル） | version.py |
| `installer/looplayer.iss` | Inno Setup スクリプト（日英 2 言語、アンインストール登録） | looplayer.spec の出力 |
| `installer/build.ps1` | ローカルビルド用 PowerShell スクリプト | PyInstaller, Inno Setup |
| `.github/workflows/release.yml` | タグトリガーの自動ビルド・リリースワークフロー | 全上記 |

### 実装順序

1. `looplayer/version.py` 作成（他のすべての依存元）
2. `looplayer/player.py` に VLC パス修正を追加
3. `installer/looplayer.spec` 作成・動作確認
4. `installer/looplayer.iss` 作成・動作確認
5. `installer/build.ps1` 作成
6. `.github/workflows/release.yml` 作成
7. 既存 `build-windows.yml` をクリーンアップ（spec ファイルを使うよう更新）

### 受け入れテスト手順

`quickstart.md` の「テスト方針」セクションに定義済み。Windows 実機での手動テストが必須。

---

**次のステップ**: `/speckit.tasks` でタスクリストを生成する
