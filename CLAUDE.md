# video-player Development Guidelines

## Tech Stack

- Python 3.12.13
- PyQt6 6.10.2
- python-vlc 3.0.21203
- ffmpeg（外部依存・クリップ書き出し時のみ必須、PATH に通っていること）

## Project Structure

```text
looplayer/
├── player.py              # メインウィンドウ (VideoPlayer)
├── bookmark_store.py      # LoopBookmark + BookmarkStore（JSON永続化）
├── bookmark_io.py         # ブックマーク export/import
├── clip_export.py         # ClipExportJob + ExportWorker（ffmpeg 書き出し）
├── app_settings.py        # アプリ設定（再生終了動作など）
├── playback_position.py   # 再生位置の記憶
├── playlist.py            # プレイリスト（フォルダドロップ）
├── sequential.py          # SequentialPlayState（連続再生状態管理）
├── recent_files.py        # 最近のファイル管理
├── updater.py             # 自動アップデート確認
├── i18n.py                # UI 文字列（日本語/英語）
├── utils.py               # ユーティリティ
├── version.py             # バージョン定義
└── widgets/
    ├── bookmark_panel.py  # ブックマークリストパネル
    ├── bookmark_row.py    # ブックマーク行ウィジェット
    ├── bookmark_slider.py # タイムライン可視化
    ├── export_dialog.py   # クリップ書き出し進捗ダイアログ
    └── playlist_panel.py  # プレイリスト UI パネル（012）
main.py                    # エントリーポイント
tests/
├── unit/                  # ユニットテスト
└── integration/           # 統合テスト
specs/                     # 機能仕様書
```

## Data Files

| ファイル | 内容 |
|----------|------|
| `~/.looplayer/bookmarks.json` | ブックマーク（`enabled` フィールドあり） |
| `~/.looplayer/recent_files.json` | 最近開いたファイル履歴 |
| `~/.looplayer/positions.json` | 再生位置の記憶 |
| `~/.looplayer/settings.json` | アプリ設定（`check_update_on_startup` など） |

## Commands

```bash
python main.py          # アプリ起動
pytest tests/ -v        # 全テスト実行
pytest tests/unit/ -v   # ユニットテストのみ
```

## Code Style

- Python 標準スタイル (PEP 8)
- UI 文字列はすべて `looplayer/i18n.py` の `t()` 経由で取得する
- テストファースト（新機能はテストを先に書いてから実装）


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Active Technologies
- Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203、ffmpeg（US10 のトランスコード用、既存） (012-player-improvements)
- `~/.looplayer/bookmarks.json`（LoopBookmark 拡張）、`~/.looplayer/settings.json`（AppSettings 拡張） (012-player-improvements)
- `~/.looplayer/bookmarks.json`（既存、変更なし） (013-player-ui-fixes)
- Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203 (015-fix-window-resize)
- `~/.looplayer/settings.json`（JSON, `AppSettings` クラスで管理） (016-p1-features)
- `~/.looplayer/settings.json`（`AppSettings` クラスで管理） (017-p2-ux-features)
- `~/.looplayer/settings.json`（AppSettings、mirror_display フィールド追加） (018-speed-mirror)
- Python 3.12.13 + PyQt6 6.10.2（UI）、標準ライブラリ: `zipfile`, `json`, `re`, `shutil`, `datetime` (019-subtitle-bookmark-backup)
- `~/.looplayer/bookmarks.json`・`settings.json`・`positions.json`・`recent_files.json`（既存）; バックアップ用 ZIP ファイル (019-subtitle-bookmark-backup)
- `~/.looplayer/bookmarks.json`, `positions.json`, `recent_files.json`（既存、変更なし） (020-music-playback)
- `~/.looplayer/settings.json`（AppSettings — 既存ファイルに 2 フィールド追加） (021-bookmark-sidepanel)
- `~/.looplayer/bookmarks.json`（BookmarkStore 経由、変更なし） (022-enhance-context-menu)
- N/A（UI 変更のみ、データファイル変更なし） (023-button-icons)

## Recent Changes
- 012-player-improvements: Added Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203、ffmpeg（US10 のトランスコード用、既存）
