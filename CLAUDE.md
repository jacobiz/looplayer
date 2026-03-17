# video-player Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-16

## Active Technologies
- Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203（既存） (002-ab-loop-bookmarks)
- `~/.looplayer/bookmarks.json`（ローカルJSONファイル、追加ライブラリなし） (002-ab-loop-bookmarks)
- N/A（状態はメモリのみ、音量・速度は永続化しない） (003-player-menus)
- Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203 + PyQt6（QDrag, QTimer, QCursor, QFileDialog, QAction）, python-vlc（MediaPlayerVideoChanged イベント） (004-player-ux)
- `~/.looplayer/recent_files.json`（新規）, `~/.looplayer/bookmarks.json`（既存・変更なし） (004-player-ux)
- `~/.looplayer/bookmarks.json`（既存・`enabled` フィールドを追加） (005-timeline-seq-info-help)
- Python 3.12.13 + PyInstaller（バンドラー）、Inno Setup（インストーラフレームワーク）、既存の PyQt6 6.10.2 + python-vlc 3.0.21203 (006-windows-installer)
- N/A（インストーラはビルド成果物） (006-windows-installer)
- `~/.looplayer/positions.json`（新規）、`~/.looplayer/settings.json`（新規）、既存の `bookmarks.json`・`recent_files.json` は変更なし (007-player-enhancements)
- N/A（永続データなし） (008-seekbar-click-seek)
- Python 3.12.13 + PyQt6 6.10.2（`QLocale.system()` でロケール検出） (009-english-ui)
- N/A（言語はメモリ内で決定。永続化なし） (009-english-ui)

- Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203 (001-video-player-core)

## Project Structure

```text
looplayer/              # アプリパッケージ
├── __init__.py
├── bookmark_store.py   # LoopBookmark + BookmarkStore（JSON永続化）
├── sequential.py       # SequentialPlayState（連続再生状態管理）
├── utils.py            # _ms_to_str ユーティリティ
├── widgets/
│   ├── bookmark_row.py    # BookmarkRow ウィジェット
│   └── bookmark_panel.py  # BookmarkPanel ウィジェット
└── player.py           # VideoPlayer + main()
main.py                 # エントリーポイント
tests/
├── unit/
└── integration/
```

## Commands

```bash
python main.py          # アプリ起動
pytest tests/ -v        # 全テスト実行
pytest tests/unit/ -v   # ユニットテストのみ
```

## Code Style

Python 3.12.13: Follow standard conventions

## Recent Changes
- 009-english-ui: Added Python 3.12.13 + PyQt6 6.10.2（`QLocale.system()` でロケール検出）
- 008-seekbar-click-seek: Added Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203
- 007-player-enhancements: Added Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203（既存）


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
