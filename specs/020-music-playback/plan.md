# Implementation Plan: 音楽ファイル再生対応

**Branch**: `020-music-playback` | **Date**: 2026-03-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-music-playback/spec.md`

## Summary

既存の動画プレーヤーに音楽ファイル（MP3, FLAC, AAC, WAV, OGG, M4A, OPUS）の再生機能を追加する。VLC はネイティブに音楽ファイルをデコードできるため、主な変更は（1）対応拡張子セットの拡張、（2）ファイルダイアログフィルタの追加、（3）音楽ファイル再生中のプレースホルダー表示の 3 点に絞られる。新規クラス・抽象化レイヤーは導入しない。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/bookmarks.json`, `positions.json`, `recent_files.json`（既存、変更なし）
**Testing**: pytest（ユニット: `tests/unit/`, 統合: `tests/integration/`）
**Target Platform**: Windows / macOS / Linux デスクトップ
**Project Type**: desktop-app
**Performance Goals**: 音楽ファイルを開いてから再生開始まで 3 秒以内（SC-001）
**Constraints**: 新規外部依存なし。既存の動画機能にリグレッションを起こさない（SC-005）
**Scale/Scope**: 単一ユーザー、ローカルファイル操作

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | チェック | 備考 |
|------|----------|------|
| I. テストファースト | ✅ PASS | 各ユーザーストーリーごとにテストを先に書く。`test_media_extensions.py`・`test_audio_placeholder.py`・`test_audio_playback.py` を先行作成 |
| II. シンプルさ重視 | ✅ PASS | 拡張子セット追加・フィルタ文字列追加・`QLabel` オーバーレイのみ。YAGNI 遵守 |
| III. 過度な抽象化の禁止 | ✅ PASS | `AudioFile` クラスは作成しない。`_SUPPORTED_AUDIO_EXTENSIONS` 定数と `_is_audio` ブールフラグで十分 |
| IV. 日本語コミュニケーション | ✅ PASS | i18n キーの日本語文字列・コメント・コミットメッセージを日本語で記述 |

**Complexity Tracking**: 違反なし。追記不要。

## Project Structure

### Documentation (this feature)

```text
specs/020-music-playback/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output ✅
├── data-model.md        # Phase 1 output ✅
├── quickstart.md        # Phase 1 output ✅
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks で生成)
```

### Source Code (変更対象)

```text
looplayer/
├── player.py            # 拡張子セット分割・_is_audio フラグ・プレースホルダー・open_file フィルタ
└── i18n.py              # filter.media_file / filter.audio_file / msg.no_media_file.* 追加

tests/
├── unit/
│   ├── test_media_extensions.py    # 新規: 拡張子判定ロジック
│   └── test_audio_placeholder.py  # 新規: プレースホルダー表示ロジック
└── integration/
    └── test_audio_playback.py      # 新規: D&D・フォルダ読み込み・混在プレイリスト
```

**Structure Decision**: 既存のシングルプロジェクト構造を踏襲。新規ファイルはテストのみ。

## Implementation Design

### 変更 1: `looplayer/player.py` — 拡張子セット

```python
# 変更前
_SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}

# 変更後
_SUPPORTED_VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"
})
_SUPPORTED_AUDIO_EXTENSIONS = frozenset({
    ".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"
})
_SUPPORTED_EXTENSIONS = _SUPPORTED_VIDEO_EXTENSIONS | _SUPPORTED_AUDIO_EXTENSIONS
```

既存の `_SUPPORTED_EXTENSIONS` 参照箇所はすべて後方互換（変更不要）。

### 変更 2: `looplayer/player.py` — `open_file()` フィルタ

```python
def open_file(self):
    path, _ = QFileDialog.getOpenFileName(
        self,
        t("dialog.open_video.title"),
        "",
        t("filter.media_file"),   # filter.video_file → filter.media_file
    )
```

### 変更 3: `looplayer/player.py` — `_open_path()` に `_is_audio` 設定

```python
def _open_path(self, path: str) -> None:
    ...
    self._is_audio = Path(path).suffix.lower() in self._SUPPORTED_AUDIO_EXTENSIONS
    self._update_audio_placeholder()
    ...
```

### 変更 4: `looplayer/player.py` — プレースホルダー `QLabel`

`_setup_ui()` 内で `video_frame` の子として `_audio_placeholder: QLabel` を追加。
`_update_audio_placeholder()` メソッドで表示/非表示を切り替える。
`resizeEvent()` でジオメトリを `video_frame` に合わせてリサイズする。

### 変更 5: `looplayer/player.py` — `_open_folder()` エラーメッセージ

`msg.no_video_file.*` → `msg.no_media_file.*` に変更（音楽ファイルもスキャン対象になるため）

### 変更 6: `looplayer/i18n.py` — キー追加

`filter.media_file`・`filter.audio_file`・`msg.no_media_file.title`・`msg.no_media_file.body` を追加。

## Phase 0 完了

→ [research.md](research.md) ✅ — すべての NEEDS CLARIFICATION 解決済み

## Phase 1 完了

→ [data-model.md](data-model.md) ✅
→ [quickstart.md](quickstart.md) ✅
→ contracts/ — デスクトップアプリのため外部 API 契約なし。スキップ。
