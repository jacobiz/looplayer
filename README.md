# LoopPlayer

AB ループとブックマーク機能を備えた語学学習・練習用動画プレイヤー。

## 概要

LoopPlayer は PyQt6 + VLC ベースの動画プレイヤーです。動画の任意の区間を A・B 点で指定してループ再生し、複数のループをブックマークとして保存・連続再生できます。語学学習、楽器練習、動画分析に特化した機能を備えています。

## 機能

- **AB ループ**: 任意の区間を繰り返し再生
- **ブックマーク管理**: 複数のループ区間を名前付きで保存・編集・メモ付き管理
- **連続再生**: ブックマークを順番に再生（各区間の繰り返し回数指定可）
- **タイムライン表示**: シークバー上にブックマーク区間をカラーバーで可視化
- **精細な再生操作**: フレームコマ送り・±1秒/±10秒シーク・速度段階変更（キーボードのみ）
- **マルチトラック対応**: 複数の音声トラック・字幕トラックをメニューで切り替え
- **スクリーンショット保存**: 現在フレームをデスクトップに PNG 保存（`Ctrl+Shift+S`）
- **再生終了時の動作設定**: 停止・先頭に戻る・ループ再生から選択（設定は永続化）
- **再生位置の記憶**: 同じファイルを再度開くと前回位置から再開
- **フォルダドロップでプレイリスト**: フォルダをドロップすると動画をファイル名順に自動順再生
- **ドラッグ＆ドロップ**: ウィンドウに動画ファイル・フォルダをドロップして開く
- **最近開いたファイル**: 直近 10 件のファイルを履歴から開く
- **クリップ書き出し**: AB ループ区間・ブックマーク区間を独立した動画ファイルとして書き出し（ffmpeg 必須、`Ctrl+E`）
- **ブックマーク export/import**: JSON ファイルで共有可能
- **動画情報表示**: 解像度・フレームレート・コーデック・ファイルサイズを表示

## インストール

Python 不要のスタンドアロンパッケージを GitHub Releases からダウンロードできます。

### Windows

1. [Releases](../../releases) から最新の `LoopPlayer-Setup-x.x.x.exe` をダウンロード
2. ダブルクリックしてインストーラを実行
3. ウィザードに従ってインストール（デスクトップにショートカットが作成されます）

> **注意**: 未署名の実行ファイルのため、Windows Defender SmartScreen の警告が表示される場合があります。「詳細情報」→「実行」で続行してください。

### macOS

1. [Releases](../../releases) から最新の `LoopPlayer-x.x.x.dmg` をダウンロード
2. DMG を開いて `LoopPlayer.app` を `/Applications` にドラッグ
3. 初回起動時は右クリック →「開く」を選択してください

> **注意**: 未署名のアプリのため、Gatekeeper の警告が表示される場合があります。「システム設定」→「プライバシーとセキュリティ」→「このまま開く」で実行できます。

## 動作環境

- Python 3.12+
- PyQt6 6.4+
- VLC ライブラリ（python-vlc が自動インストール）
- ffmpeg（クリップ書き出し機能を使う場合のみ、PATH に通っていること）
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

### 再生操作

| キー | 動作 |
|------|------|
| `Space` | 再生 / 一時停止 |
| `←` / `→` | ±5 秒シーク |
| `Shift+←` / `Shift+→` | ±1 秒シーク |
| `Ctrl+←` / `Ctrl+→` | ±10 秒シーク |
| `,` / `.` | 1フレーム戻る / 進む（自動一時停止） |
| `[` / `]` | 再生速度を下げる / 上げる |
| `↑` / `↓` | 音量 ±10% |
| `M` | ミュート切替 |

### ファイル操作

| キー | 動作 |
|------|------|
| `Ctrl+O` | ファイルを開く |
| `Ctrl+E` | クリップを書き出す（AB ループ設定時のみ有効） |
| `Ctrl+Shift+S` | スクリーンショット保存 |
| `Ctrl+Q` | 終了 |

### 表示・その他

| キー | 動作 |
|------|------|
| `F` | フルスクリーン切替 |
| `Ctrl+Z` | ブックマーク削除を元に戻す（5 秒以内） |
| `?` | ショートカット一覧を表示 |

> アプリ内の「ヘルプ → ショートカット一覧」でも確認できます。

## データ保存場所

| ファイル | 内容 |
|----------|------|
| `~/.looplayer/bookmarks.json` | ブックマーク（動画ファイルパスをキーに保存） |
| `~/.looplayer/recent_files.json` | 最近開いたファイルの履歴 |
| `~/.looplayer/positions.json` | 再生位置の記憶（直近 10 件） |
| `~/.looplayer/settings.json` | アプリ設定（再生終了時の動作など） |

## 対応フォーマット

MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V

## プロジェクト構成

```
looplayer/
├── player.py               # メインウィンドウ
├── bookmark_store.py       # ブックマーク管理・永続化
├── bookmark_io.py          # ブックマーク export/import
├── clip_export.py          # クリップ書き出し（ClipExportJob + ExportWorker）
├── app_settings.py         # アプリ設定（再生終了動作など）
├── playback_position.py    # 再生位置の記憶
├── playlist.py             # プレイリスト（フォルダドロップ）
├── sequential.py           # 連続再生状態管理
├── recent_files.py         # 最近のファイル管理
├── utils.py                # ユーティリティ
└── widgets/
    ├── bookmark_panel.py   # ブックマークリストパネル
    ├── bookmark_row.py     # ブックマーク行ウィジェット
    ├── bookmark_slider.py  # タイムライン可視化
    └── export_dialog.py    # クリップ書き出し進捗ダイアログ
main.py                     # エントリーポイント
tests/
├── unit/                   # ユニットテスト
└── integration/            # 統合テスト
specs/                      # 機能仕様書
```

## Dev Container（Docker）

VS Code の Dev Containers 拡張機能を使用してコンテナ内で開発できます。

```
コマンドパレット → "Dev Containers: Reopen in Container"
```
