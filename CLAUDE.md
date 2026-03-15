# video-player Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-15

## Active Technologies
- Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203（既存） (002-ab-loop-bookmarks)
- `~/.looplayer/bookmarks.json`（ローカルJSONファイル、追加ライブラリなし） (002-ab-loop-bookmarks)

- Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203 (001-video-player-core)

## Project Structure

```text
main.py
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
- 002-ab-loop-bookmarks: Added Python 3.12.13 + PyQt6 6.10.2、python-vlc 3.0.21203（既存）

- 001-video-player-core: Added Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
