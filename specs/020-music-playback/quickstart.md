# Quickstart: 音楽ファイル再生対応 開発ガイド

## 開発の準備

```bash
cd /workspaces/video-player
git checkout 020-music-playback
python -m pytest tests/ -v   # 現時点で全テストがパスすることを確認
```

## 実装の進め方（Constitution I: テストファースト）

各ユーザーストーリーを **テスト → 実装 → リファクタリング** の順で進める。

### P1: 音楽ファイルを開いて再生する

```bash
# 1. テストを先に書く
# tests/unit/test_media_extensions.py を新規作成

# 2. テストが失敗することを確認
python -m pytest tests/unit/test_media_extensions.py -v  # FAIL expected

# 3. 実装: looplayer/player.py の拡張子セット追加
# 4. looplayer/i18n.py にフィルタキー追加
# 5. テストが通ることを確認
python -m pytest tests/unit/test_media_extensions.py -v  # PASS

# 6. 統合テスト
python -m pytest tests/integration/test_audio_playback.py -v
```

### P2: 音楽再生中のプレースホルダー表示

```bash
# 1. テストを先に書く
# tests/unit/test_audio_placeholder.py を新規作成

# 2. テストが失敗することを確認
python -m pytest tests/unit/test_audio_placeholder.py -v  # FAIL expected

# 3. 実装: _is_audio フラグ + QLabel オーバーレイ
# 4. テストが通ることを確認
```

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `looplayer/player.py` | 拡張子セット分割、`_is_audio` フラグ、プレースホルダー QLabel、`open_file()` フィルタ変更 |
| `looplayer/i18n.py` | `filter.audio_file`・`filter.media_file`・`msg.no_media_file.*` キー追加 |

## 新規テストファイル

| ファイル | テスト内容 |
|----------|-----------|
| `tests/unit/test_media_extensions.py` | 拡張子判定（音楽/動画/不明の分類）|
| `tests/unit/test_audio_placeholder.py` | `_is_audio` フラグ、プレースホルダー表示/非表示ロジック |
| `tests/integration/test_audio_playback.py` | ドラッグ&ドロップ、フォルダ読み込み、プレイリスト混在 |

## 動作確認

```bash
python main.py
# 確認項目:
# 1. ファイルを開く → 「すべてのメディア」が最初のフィルタとして表示
# 2. .mp3 ファイルを選択 → 再生開始 + 映像エリアに音符プレースホルダー表示
# 3. .mp4 ファイルを選択 → プレースホルダーが消えて動画が表示
# 4. 音楽ファイルをドラッグ&ドロップ → 再生開始
# 5. 音楽ファイルのみのフォルダをドロップ → プレイリストに追加されて連続再生
```
