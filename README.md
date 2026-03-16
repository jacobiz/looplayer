# LoopPlayer

AB ループとブックマーク機能を備えた語学学習・練習用動画プレイヤー。

## 概要

LoopPlayer は PyQt6 + VLC ベースの動画プレイヤーです。動画の任意の区間を A・B 点で指定してループ再生し、複数のループをブックマークとして保存・連続再生できます。語学学習、楽器練習、動画分析に特化した機能を備えています。

## 機能

- **AB ループ**: 任意の区間を繰り返し再生
- **ブックマーク管理**: 複数のループ区間を名前付きで保存・編集
- **連続再生**: ブックマークを順番に再生（各区間の繰り返し回数指定可）
- **タイムライン表示**: シークバー上にブックマーク区間をカラーバーで可視化
- **ショートカット充実**: キーボードのみで操作可能
- **ドラッグ＆ドロップ**: ウィンドウに動画ファイルをドロップして開く
- **最近開いたファイル**: 直近 10 件のファイルを履歴から開く
- **ブックマーク export/import**: JSON ファイルで共有可能
- **動画情報表示**: 解像度・フレームレート・コーデック・ファイルサイズを表示

## インストール（Windows）

Python 不要のスタンドアロンインストーラを GitHub Releases からダウンロードできます。

1. [Releases](../../releases) から最新の `LoopPlayer-Setup-x.x.x.exe` をダウンロード
2. ダブルクリックしてインストーラを実行
3. ウィザードに従ってインストール（デスクトップにショートカットが作成されます）

> **注意**: 未署名の実行ファイルのため、Windows Defender SmartScreen の警告が表示される場合があります。「詳細情報」→「実行」で続行してください。

## 動作環境

- Python 3.12+
- PyQt6 6.4+
- VLC ライブラリ（python-vlc が自動インストール）
- Linux / Windows / macOS

## 開発者向けセットアップ

```bash
git clone <repo-url>
cd video-player
pip install -r requirements.txt
```

## 起動

```bash
python main.py
```

## テスト

```bash
pytest tests/ -v          # 全テスト
pytest tests/unit/ -v     # ユニットテストのみ
pytest tests/integration/ # 統合テストのみ
```

## キーボードショートカット

| キー | 動作 |
|------|------|
| `Space` | 再生 / 一時停止 |
| `←` / `→` | ±5 秒シーク |
| `↑` / `↓` | 音量 ±10% |
| `M` | ミュート切替 |
| `F` | フルスクリーン切替 |
| `Ctrl+O` | ファイルを開く |
| `Ctrl+E` | ブックマーク書き出し |
| `Ctrl+I` | ブックマーク読み込み |
| `?` | ショートカット一覧を表示 |
| `Ctrl+Q` | 終了 |

## データ保存場所

| ファイル | 内容 |
|----------|------|
| `~/.looplayer/bookmarks.json` | ブックマーク（動画ファイルパスをキーに保存） |
| `~/.looplayer/recent_files.json` | 最近開いたファイルの履歴 |

## 対応フォーマット

MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V

## プロジェクト構成

```
looplayer/
├── player.py           # メインウィンドウ
├── bookmark_store.py   # ブックマーク管理・永続化
├── bookmark_io.py      # ブックマーク export/import
├── sequential.py       # 連続再生状態管理
├── recent_files.py     # 最近のファイル管理
├── utils.py            # ユーティリティ
└── widgets/
    ├── bookmark_panel.py   # ブックマークリストパネル
    ├── bookmark_row.py     # ブックマーク行ウィジェット
    └── bookmark_slider.py  # タイムライン可視化
main.py                 # エントリーポイント
tests/
├── unit/               # ユニットテスト
└── integration/        # 統合テスト
specs/                  # 機能仕様書
```

## Dev Container（Docker）

VS Code の Dev Containers 拡張機能を使用してコンテナ内で開発できます。

```
コマンドパレット → "Dev Containers: Reopen in Container"
```
