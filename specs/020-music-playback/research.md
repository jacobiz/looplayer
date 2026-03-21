# Research: 音楽ファイル再生対応

## VLC による音楽ファイル再生

**Decision**: python-vlc の既存 `media_player_new()` + `media_new()` API をそのまま利用する
**Rationale**: VLC は MP3/FLAC/AAC/WAV/OGG/M4A/OPUS をネイティブにデコードできる。音楽ファイルを開くと映像トラックがないだけで再生は正常に動作する。追加ライブラリ不要。
**Alternatives considered**: GStreamer, mutagen（メタデータ用）— 不要なため却下

## 音楽/動画の判定方式

**Decision**: 拡張子ベース判定（既存の `_SUPPORTED_EXTENSIONS` と同じアプローチ）
**Rationale**: シンプルで高速。VLC のデコード可否は実際の再生時に自動判定される。拡張子判定で十分な精度が得られる。
**Alternatives considered**: ファイルヘッダ（マジックバイト）判定 — 過剰。VLC の `media.get_tracks()` で映像トラック有無を検出 — 再生開始後でないと取得不可なため、UI 表示切り替えのタイミングが遅れる

## プレースホルダー表示の実装方式

**Decision**: `video_frame` の上に `QLabel` をオーバーレイとして配置し、音楽ファイル再生中のみ表示する
**Rationale**: `video_frame` は VLC の映像出力先として使用中のため、置き換えではなくオーバーレイが安全。`QLabel` に Unicode 音符文字（♫）とファイル名を表示するシンプルな実装で十分。
**Alternatives considered**: 別の `QStackedWidget` に切り替える — video_frame の win_id が変わるため VLC との接続が切れるリスクあり。SVG アイコン描画 — 過剰

## ファイルダイアログフィルタ

**Decision**: 3 種類のフィルタを提供
1. `すべてのメディア (*.mp4 *.avi ... *.mp3 *.flac ...)` — デフォルト選択
2. `動画ファイル (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)`
3. `音楽ファイル (*.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus)`

**Rationale**: ユーザーが音楽・動画を 1 操作で開ける「すべてのメディア」がデフォルトの第 1 フィルタになるとよい。QFileDialog の filter 文字列は `;;` で区切ることで複数提供できる。
**Alternatives considered**: 統合フィルタのみ — 絞り込みができない。別々のみ — ユーザーが毎回切り替え必要

## i18n 変更方針

**Decision**: 以下のキーを追加・変更する

追加:
- `filter.audio_file`: 音楽ファイルフィルタ文字列
- `filter.media_file`: すべてのメディアフィルタ文字列
- `dialog.open_media.title`: 「メディアファイルを開く」（新規追加）

変更なし（後方互換性のため）:
- `filter.video_file`: そのまま保持
- `msg.no_video_file.body`: 音楽ファイルにも言及する文言に更新

**Rationale**: `dialog.open_video.title` は変更せず、`dialog.open_media.title` を新規追加することで、将来的に使い分けが可能。
**Alternatives considered**: 既存キーの値を変更 — 動画専用のコンテキストで使われている可能性があるため、新規キー追加が安全

## プレイリスト並び順

**Decision**: 既存の `sorted()` + ファイル名昇順をそのまま利用。変更不要
**Rationale**: `_open_folder()` はすでに `sorted(p for p in ...)` でファイル名順に並べている。音楽ファイルを対象拡張子セットに追加するだけで同じ並び順が自動的に適用される。

## テスト戦略（Constitution I 準拠）

**Decision**: 以下の順でテストを先に書く
1. `tests/unit/test_media_extensions.py` — 拡張子判定ロジック
2. `tests/unit/test_file_dialog_filters.py` — フィルタ文字列生成
3. `tests/unit/test_audio_placeholder.py` — プレースホルダー表示ロジック
4. `tests/integration/test_audio_playback.py` — 音楽ファイルドラッグ&ドロップ、フォルダ読み込み

**Rationale**: 拡張子判定とフィルタ生成はユニットテストで完結。プレースホルダー表示は UI ロジック（`_is_audio` フラグ）をユニットテスト可能な形で設計する。
