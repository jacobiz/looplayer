# Data Model: 音楽ファイル再生対応

## 概要

このフィーチャーは新しい永続化データモデルを導入しない。既存の `bookmarks.json`・`positions.json`・`recent_files.json` をそのまま拡張して使用する（音楽ファイルパスも同じ形式で保存される）。

唯一の「モデル変化」は `player.py` 内の定数セットと UI 状態フラグの追加。

---

## 定数変更: 対応拡張子セット

### 変更前（`player.py` 内）

```python
_SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
```

### 変更後

```python
_SUPPORTED_VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"
})

_SUPPORTED_AUDIO_EXTENSIONS = frozenset({
    ".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"
})

_SUPPORTED_EXTENSIONS = _SUPPORTED_VIDEO_EXTENSIONS | _SUPPORTED_AUDIO_EXTENSIONS
```

**制約**:
- `_SUPPORTED_EXTENSIONS` の参照はすべて既存コードのまま動作する（後方互換）
- 拡張子はすべて小文字で定義。判定時は `.suffix.lower()` で比較（既存実装と同じ）

---

## UI 状態: 音楽ファイル判定フラグ

`_open_path()` 内でファイルを開く際に判定し、プレースホルダー表示の制御に使用する。

```python
# player.py の _open_path() 内で設定
self._is_audio: bool = Path(path).suffix.lower() in self._SUPPORTED_AUDIO_EXTENSIONS
```

**状態遷移**:
```
ファイル未選択 → _is_audio = False（初期値）
音楽ファイルを開く → _is_audio = True → プレースホルダー表示
動画ファイルを開く → _is_audio = False → プレースホルダー非表示
```

---

## i18n キー追加

`looplayer/i18n.py` に以下のキーを追加する。

| キー | 日本語 | 英語 |
|------|--------|------|
| `filter.audio_file` | `音楽ファイル (*.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;すべてのファイル (*)` | `Audio Files (*.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;All Files (*)` |
| `filter.media_file` | `すべてのメディア (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;動画ファイル (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;音楽ファイル (*.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;すべてのファイル (*)` | `All Media (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;Audio Files (*.mp3 *.flac *.aac *.wav *.ogg *.m4a *.opus);;All Files (*)` |
| `msg.no_media_file.title` | `エラー` | `Error` |
| `msg.no_media_file.body` | `対応するメディアファイルが見つかりませんでした。` | `No supported media files found.` |

**既存キー変更**（1 件のみ）:
- `dialog.open_video.title` の呼び出しを `open_file()` 内で `filter.media_file` フィルタに切り替える（キー自体は削除しない）

---

## プレースホルダーウィジェット

新規クラスを作成しない（Constitution III 遵守）。`VideoPlayer._setup_ui()` 内に `QLabel` を追加してオーバーレイとして実装する。

```
video_frame (QWidget, 黒背景)
└── _audio_placeholder (QLabel, 中央揃え, 音符 + ファイル名)
    ├── 表示条件: self._is_audio == True
    └── 非表示条件: self._is_audio == False
```

**注意**: `video_frame` は VLC の `set_hwnd()` / `set_xwindow()` に渡す win_id の親として機能するため、`video_frame` 自体は変更しない。`QLabel` を `video_frame` の子ウィジェットとして配置し、geometry を `video_frame` に合わせる。
