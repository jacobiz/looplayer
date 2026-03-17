# Research: AB Loop Player Improvements

## 1. ポーズ間隔（pause_ms）の実装方式

**Decision**: `QTimer.singleShot` でポーズ後に A 点へシーク

**Rationale**:
- `_on_timer()` は 200ms ポーリングのため、ms 精度のポーズには `QTimer.singleShot` が適切
- B 点到達時に `media_player.pause()` → `QTimer.singleShot(pause_ms, callback)` → callback で A 点にシークして再生再開
- ポーズ中のスペースキーキャンセル: `self._pause_timer.stop()` + 即 A 点シーク
- `self._pause_timer: QTimer | None = None` をインスタンス変数で管理し、ファイル切替時に `stop()` してクリア

**Alternatives considered**:
- `_on_timer()` 内でポーズ経過時間を計測: タイマー精度が 200ms に縛られるため却下

---

## 2. 連続再生「1周停止」モードの実装方式

**Decision**: `SequentialPlayState.on_b_reached()` の戻り値を `int | None` に変更し、1周完了時は `None` を返す

**Rationale**:
- 現在の `on_b_reached()` は常に `int` を返す（player.py:863）
- `None` 返却を「連続再生終了」のシグナルとして扱う
- `player.py` 側で `next_a = state.on_b_reached(); if next_a is None: self._stop_seq_play()`
- `SequentialPlayMode` は `AppSettings` に `sequential_play_mode: str = "infinite"` として保存

**Alternatives considered**:
- `SequentialPlayState` に `finished` シグナルを追加: QObject でないため不採用
- `active` フラグを `on_b_reached()` 内で False にする: 呼び出し元が返り値を使えなくなるため却下

---

## 3. フレーム単位微調整の fps 取得

**Decision**: `media_player.get_fps()` を使用し、0 の場合は 25fps にフォールバック（既存の `_frame_backward()` と同じパターン）

**Rationale**:
- player.py の `_frame_backward()` がすでに同パターンを使用
- `frame_ms = max(1, int(1000 / fps))` で 1ms 以上を保証

---

## 4. `Alt+←` / `Alt+→` の PyQt6 実装

**Decision**: `QShortcut(QKeySequence(Qt.Key.Key_Left | Qt.KeyboardModifier.AltModifier), self)` + `ApplicationShortcut` コンテキスト

**Rationale**:
- 既存の `Shift+←`/`Ctrl+←` と同じ `QShortcut` パターン（player.py:424-451）
- `QKeySequence("Alt+Left")` の文字列形式でも可（既存コードで確認済み）
- macOS での `Alt+←` 文字カーソル移動との競合: `ApplicationShortcut` は `QLineEdit` 等の入力フォーカス中は無効になるため問題なし

---

## 5. プレイリスト UI のレイアウト

**Decision**: `BookmarkPanel` と同じ右サイドパネルに `QTabWidget` でタブ切り替え

**Rationale**:
- 既存の `QSplitter` 構造（video | right_panel）を変更せず、`right_panel` 内に `QTabWidget` を追加
- タブ 1: 「ブックマーク」（既存 `BookmarkPanel`）
- タブ 2: 「プレイリスト」（新規 `PlaylistPanel`）
- プレイリストが存在しない場合はタブ 2 を非表示にする
- `Playlist` クラスに `retreat()` メソッドを追加（`index` を -1 方向へ移動）

---

## 6. `BookmarkRow` のレイアウト拡張

**Decision**: 新規ボタン・スピンボックスを `repeat_spin` の直後に挿入

**既存レイアウト** (bookmark_row.py:31-81):
```
[enabled_checkbox] [name_label] [time_label] <stretch> [repeat_label] [repeat_spin] [memo_btn] [del_btn]
```

**拡張後レイアウト**:
```
[enabled_checkbox] [name_label] [time_label] <stretch> [repeat_label] [repeat_spin]
  [pause_label] [pause_spin]
  [play_count_label]
  [A:-1F][A:+1F] [B:-1F][B:+1F]
  [memo_btn] [del_btn]
```

**Rationale**: ボタン数が増えるため 2 行目に折り返す。`QVBoxLayout` + 2 行の `QHBoxLayout` に変更するのが最もシンプル。

---

## 7. タグ入力 UI

**Decision**: メモ編集と同じポップアップダイアログパターン（`QInputDialog.getText`）を使用し、カンマ区切りで入力

**Rationale**:
- 専用の tag editor ウィジェットを作るより `QInputDialog` の再利用が最もシンプル（Constitution II）
- `BookmarkRow` にタグ表示ラベル + 「タグ編集（🏷）」ボタンを追加
- `bookmark_panel.py` にタグフィルタ（`QComboBox` または `QListWidget`）を追加

---

## 8. クリップ書き出しトランスコード

**Decision**: `ClipExportJob` に `encode_mode: str = "copy"` フィールドを追加し、`ExportWorker.run()` 内で ffmpeg コマンドを分岐

**ffmpeg コマンド差分**:
- copy モード: `[..., "-c", "copy", ...]`（既存）
- transcode モード: `[..., "-c:v", "libx264", "-c:a", "aac", "-crf", "23", ...]`

**`export_dialog.py` の変更**: `QRadioButton` 2 個を追加し、選択を `ClipExportJob.encode_mode` に反映

---

## 9. ブックマーク保存時名前入力

**Decision**: `QInputDialog.getText` を使ってインラインダイアログを表示

**Rationale**:
- PyQt6 標準ダイアログで追加ウィジェット不要
- `player._save_bookmark()` に `QInputDialog.getText(self, ..., default_name)` を追加するだけ
- OK → 入力名で保存、Cancel → 保存しない

