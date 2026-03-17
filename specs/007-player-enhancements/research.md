# Research: プレイヤー機能強化

**Branch**: `007-player-enhancements` | **Date**: 2026-03-16

---

## R-001: フレームコマ送り（前進・後退）

**Decision**: 前進は `media_player.next_frame()`、後退は `media_player.set_time(t - frame_ms)` で実装する。

**Rationale**:
- `next_frame()` は python-vlc が提供する公式 API。一時停止状態でのみ有効（再生中は自動で一時停止してから呼ぶ）。
- 後退用の `prev_frame()` は VLC に存在しないため、現在位置からフレーム時間を差し引いて `set_time()` する。
- フレーム時間は `media_player.get_fps()` から算出（`frame_ms = 1000.0 / fps`）。`get_fps()` が 0 以下を返す場合は 25fps（40ms）にフォールバック。

**Alternatives considered**:
- `set_time(t - 1)` ごとに呼ぶ: ms 精度でのフレーム境界が不定のため不採用。
- 固定 40ms（25fps）: FPS 情報が取得可能な場合は正確な値を使うべきため不採用（フォールバックとしてのみ利用）。

---

## R-002: 音声・字幕トラック切り替え

**Decision**: `audio_get_track_description()` / `audio_set_track()` で音声、`video_get_spu_description()` / `video_set_spu()` で字幕を操作する。

**Rationale**:
- VLC の公式 API で、python-vlc にバインディングあり。
- トラック一覧はメニューを開いたタイミングで `aboutToShow` シグナルで最新取得することで、動画読み込み完了前の空リスト問題を回避する。
- 字幕オフは `video_set_spu(-1)` で実現（VLC の仕様）。

**Implementation note**:
```python
# 音声トラック一覧取得
descs = media_player.audio_get_track_description()  # [(id, name), ...]
# 音声トラック切り替え
media_player.audio_set_track(track_id)

# 字幕トラック一覧取得
descs = media_player.video_get_spu_description()  # [(id, name), ...]
# 字幕オフ
media_player.video_set_spu(-1)
# 字幕オン
media_player.video_set_spu(track_id)
```

---

## R-003: スクリーンショット保存

**Decision**: `media_player.video_take_snapshot(0, str(path), 0, 0)` で PNG 保存。保存先はデスクトップ（クロスプラットフォーム対応）。

**Rationale**:
- 第1引数 `0` は num (画面番号)、第3・第4引数 `0, 0` は width/height（0 = オリジナルサイズ）。
- 保存先パスはクロスプラットフォームで以下のロジックで決定:
  1. `Path.home() / "Desktop"` が存在すれば使用
  2. 存在しない場合（一部の Linux 環境）は `Path.home()` を使用

```python
desktop = Path.home() / "Desktop"
save_dir = desktop if desktop.exists() else Path.home()
filename = f"LoopPlayer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
path = save_dir / filename
media_player.video_take_snapshot(0, str(path), 0, 0)
```

**Alternatives considered**:
- `QScreen.grabWindow()` によるウィンドウキャプチャ: VLC レンダリング領域は OS ネイティブウィンドウのため PyQt 側からのキャプチャに制限あり。VLC 内蔵の snapshot API が信頼性で上回る。

---

## R-004: 再生終了イベントの処理

**Decision**: `MediaPlayerEndReached` イベントを既存の `MediaPlayerEncounteredError` と同じ pyqtSignal パターンで処理する。

**Rationale**:
- VLC のイベントコールバックは VLC 内部スレッドから呼ばれるため、Qt ウィジェットへの直接アクセスは禁止。
- 既存コードが `_error_occurred = pyqtSignal()` → `_on_media_error()` → `emit()` → `_show_error_dialog()` のパターンを確立済み。同じパターンで `_playback_ended = pyqtSignal()` を追加する。

```python
# シグナル定義
_playback_ended = pyqtSignal()

# イベント購読（__init__ 内）
em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_playback_ended)
self._playback_ended.connect(self._handle_playback_ended)

# VLC スレッドのコールバック
def _on_playback_ended(self, _event):
    self._playback_ended.emit()

# UI スレッドのハンドラ
def _handle_playback_ended(self):
    # プレイリスト有効 → 次のファイルへ
    # ABループ有効 → 何もしない（既存の _on_timer が制御）
    # それ以外 → app_settings の設定に従って動作
    ...
```

**Alternatives considered**:
- `QTimer.singleShot(0, handler)` による遅延実行: pyqtSignal の方がスレッドセーフ性が明示的で既存パターンとの一貫性が高い。

---

## R-005: 設定の永続化（AppSettings）

**Decision**: `~/.looplayer/settings.json` に JSON 形式で保存。既存の `RecentFiles`・`BookmarkStore` と同じアトミック書き込みパターンを使用する。

**Rationale**:
- プロジェクト全体で `~/.looplayer/*.json` という永続化パターンが確立されている。新たな依存（`QSettings`、`configparser` 等）を導入するより既存パターンを踏襲することが Constitution II（シンプルさ）に沿う。
- `settings.json` の初期構造:

```json
{
  "end_of_playback_action": "stop"
}
```

- 将来の設定追加時は `dict.get(key, default)` で後方互換性を確保。

**Alternatives considered**:
- `QSettings`: プラットフォームごとに保存場所が異なり（Windows はレジストリ）、`~/.looplayer/` への統一ができない。

---

## R-006: 再生位置の記憶（PlaybackPosition）

**Decision**: `~/.looplayer/positions.json` に `{filepath: position_ms}` 形式で保存。上限 10 件、古い順に削除。

**Rationale**:
- `recent_files.json` と独立した管理とすることで（Clarification Q1 の回答）、削除タイミングの差異（最近ファイルはメニュー操作で削除可能、位置情報は自動管理のみ）に対応できる。
- `dict` の挿入順序（Python 3.7+）を利用して「最近アクセス順」を管理する。

```json
{
  "/home/user/video1.mp4": 12300,
  "/home/user/video2.mkv": 45600
}
```

- 保存タイミング: 別ファイルを開く直前・アプリ終了時（`closeEvent`）。
- 読み込みタイミング: `_open_path()` 内でファイルを開いた直後。

---

## R-007: フォルダドロップとプレイリスト管理

**Decision**: `Playlist` クラス（`playlist.py`）でファイルリスト・現在インデックスを管理。`MediaPlayerEndReached` → `_handle_playback_ended()` → `playlist.advance()` で自動進行。

**Rationale**:
- プレイリストはセッション中のみ保持（永続化不要）なので、シンプルなデータクラスで十分。
- `dropEvent` の既存実装を拡張し、ドロップ対象が `QUrl.isLocalFile()` かつディレクトリの場合に `Playlist` を生成してから `_open_path()` を呼ぶ。

```python
# dropEvent の拡張
url = event.mimeData().urls()[0]
local = Path(url.toLocalFile())
if local.is_dir():
    files = sorted(
        p for p in local.iterdir()
        if not p.name.startswith('.') and p.suffix.lower() in _SUPPORTED_EXTENSIONS
    )
    if not files:
        QMessageBox.warning(self, "エラー", "対応する動画ファイルが見つかりませんでした。")
        return
    self._playlist = Playlist(files)
    self._open_path(str(self._playlist.current()))
```

---

## R-008: QStatusBar の追加

**Decision**: `QMainWindow.statusBar()` を初めて呼ぶことで QStatusBar を自動生成し、`showMessage(msg, timeout_ms)` で一時メッセージを表示する。

**Rationale**:
- `QMainWindow` は `statusBar()` を組み込みで持っており、追加コードなしに利用できる。
- `showMessage("...", 3000)` で 3 秒後に自動消去されるため、手動でクリアする必要がない。
- フルスクリーン時は `controls_panel` と同様に `statusBar().hide()` する。

```python
# スクリーンショット保存後
self.statusBar().showMessage(f"保存しました: {path}", 3000)

# 速度の端に達したとき
self.statusBar().showMessage("最大速度です", 2000)
```
