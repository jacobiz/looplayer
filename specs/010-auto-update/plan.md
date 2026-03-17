# Implementation Plan: 自動更新機能

**Branch**: `010-auto-update` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-auto-update/spec.md`

## Summary

GitHub Releases API を使用してアプリ起動時にバックグラウンドで新バージョンを確認し、利用可能な場合は通知ダイアログを表示する。ユーザーは「今すぐダウンロード」でインストーラーを OS 一時フォルダにダウンロード（進捗ダイアログ付き）して自動起動するか、「あとで」で通知を閉じることができる。ヘルプメニューから手動確認も可能。設定は既存の `~/.looplayer/settings.json` に保存する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2（既存）、`urllib.request`（標準ライブラリ）、`tempfile`（標準ライブラリ）
**Storage**: `~/.looplayer/settings.json`（既存・`check_update_on_startup` フィールドを追加）
**Testing**: pytest + pytest-qt（既存）
**Target Platform**: Windows（主）、macOS（副）
**Project Type**: デスクトップアプリ
**Performance Goals**: 更新確認はメインウィンドウ表示をブロックしない（バックグラウンド）。起動から 5 秒以内に通知表示（通常回線）。
**Constraints**: タイムアウト上限 5 秒。追加の外部ライブラリ禁止（`requests`、`semver`、`packaging` 等）。
**Scale/Scope**: 単一ユーザー向けデスクトップアプリ。同時接続なし。

## Constitution Check

### I. テストファースト ✅

- `tests/unit/test_updater.py`（UpdateChecker・バージョン比較・AppSettings 拡張）を実装前に作成する
- `tests/integration/test_auto_update.py`（ヘルプメニュー項目・設定トグル）を統合テストとして追加する
- モックは最小限（GitHub API HTTP 呼び出しのみ）、AppSettings は実ファイル（tmp_path）を使用する

### II. シンプルさ重視 ✅

- セマンティックバージョン比較は外部ライブラリなしで `tuple(int(x) for x in ver.split("."))` で実装
- ダウンロードは `urllib.request.urlretrieve` を使用（`requests` 不要）
- `UpdateInfo` データクラスは導入しない（`pyqtSignal(str, str)` で十分）

### III. 過度な抽象化の禁止 ✅

- `UpdateChecker` と `DownloadThread` は `QThread` を直接サブクラス化（ファクトリ・リポジトリパターン不要）
- `DownloadDialog` は `updater.py` 内にインライン定義（別ファイル分割不要）
- `UpdateInfo` 値オブジェクトは作成しない（シグナルの引数で十分）

### IV. 日本語コミュニケーション ✅

- UI テキストは i18n キー経由（ja/en 両対応）
- コメント・ドキュメントは日本語

## Project Structure

### Documentation (this feature)

```text
specs/010-auto-update/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── github-api.md    # GitHub Releases API contract
│   └── qt-signals.md    # UpdateChecker / DownloadThread signal contract
└── tasks.md             # Phase 2 output (/speckit.tasks で生成)
```

### Source Code (repository root)

```text
looplayer/
├── updater.py           # 新規: UpdateChecker, DownloadThread, DownloadDialog
├── app_settings.py      # 変更: check_update_on_startup プロパティ追加
├── i18n.py              # 変更: 13 キー追加
└── player.py            # 変更: ヘルプメニュー 2 項目追加、起動時チェック呼び出し

tests/
├── unit/
│   └── test_updater.py           # 新規: UpdateChecker ユニットテスト
└── integration/
    └── test_auto_update.py       # 新規: メニュー・設定統合テスト
```

**Structure Decision**: 既存の単一プロジェクト構造に準拠。新規ファイルは `looplayer/updater.py` と 2 つのテストファイルのみ。

## Complexity Tracking

| 違反 | 必要な理由 | より単純な代替を棄却した理由 |
|------|-----------|--------------------------|
| `QThread` サブクラス 2 つ | バックグラウンド HTTP + 進捗更新は UI スレッドをブロックできないため並行処理が必須 | `threading.Thread` は Qt オブジェクトとのスレッド安全性が複雑になる |
