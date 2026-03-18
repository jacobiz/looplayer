# Research: P1優先度機能の実装

**Branch**: `016-p1-features` | **Date**: 2026-03-18

---

## F-201 外部字幕ファイルの読み込み

### Decision
実行中のメディアに字幕を追加する API として `media_player.add_slave(type, uri, select)` を採用する。

### Rationale
- `media.add_option(':sub-file=<path>')` はメディア作成時のオプション注入であり、動画再生中に呼べない
- `add_slave()` は VLC 3.0+ のランタイム API で、メディアを再作成せずに字幕を追加できる
- python-vlc 3.0.21203 で利用可能。シグネチャ: `add_slave(type: MediaSlaveType, uri: str, select: bool) -> int`
- `uri` は `Path.as_uri()` で `file:///...` 形式に変換する（日本語パス対応）

### Alternatives considered
| API | 理由で却下 |
|-----|-----------|
| `media.add_option(':sub-file=<path>')` | 再生前のメディア生成時にしか機能しない |
| `media.add_option(':input-slave=<path>')` | 音声スレーブ向け。字幕には非推奨 |
| メディア再作成 + add_option | 再生位置がリセットされる、UX 劣化 |

### 動画切替時のリセット
`_open_video()` 内で `self._external_subtitle_path = None` をリセットし、
字幕メニューに外部字幕エントリが残らないようにする。

### エンコーディング
UTF-8 のみ対応。ファイル読み取りは VLC に委任するため Python 側でのデコードは不要。
ただし、ファイルダイアログで選択されたパス処理は `str(Path(...))` で正規化する。

---

## F-403 ウィンドウ位置・サイズの記憶

### Decision
`AppSettings` に `window_geometry` プロパティを追加し、`dict` で `{x, y, width, height}` を保存する。
フルスクリーン突入時に `_pre_fullscreen_geometry` として直前のジオメトリを `VideoPlayer` に保持し、
フルスクリーン中に終了した場合はこの値を保存する。

### Rationale
- 既存の `AppSettings` パターン（property + `_data[key]` + `save()`）に完全に沿った実装
- 新規モジュール不要（constitution III 準拠）
- PyQt6 の `self.geometry()` で `QRect(x, y, w, h)` を取得できる
- 画面範囲外チェック: `QApplication.screenAt(QPoint(x, y))` が `None` を返したらプライマリスクリーン中央に移動

### フルスクリーン終了時の挙動
```
toggle_fullscreen() 呼び出し時:
  self._pre_fullscreen_geometry = self.geometry()  ← 保存
  self.showFullScreen()

closeEvent():
  if self.isFullScreen():
    geo = self._pre_fullscreen_geometry
  else:
    geo = self.geometry()
  settings.window_geometry = {x, y, w, h}
```

### Alternatives considered
| 手法 | 理由で却下 |
|------|-----------|
| `QSettings` | 既存コードが `settings.json` / `AppSettings` に統一されている |
| `saveGeometry()` / `restoreGeometry()` (バイナリ) | JSON で人間が読めるべき（他のデータと一貫性） |

---

## F-502 ツールチップの充実

### Decision
`setToolTip(t("tooltip.<key>"))` を各ウィジェットに追加。新規 i18n キーを `i18n.py` に追記する。

### Rationale
- 既存の `t()` 関数と翻訳辞書をそのまま拡張するだけで対応可能
- `setToolTip()` は PyQt6 のすべての `QWidget` サブクラスに標準装備
- ショートカットキーはツールチップテキストに直接埋め込む（例: `"A 点を設定 (I)"`）

### 対象コントロール（FR-304 より）
| コントロール | i18n キー案 |
|-------------|------------|
| 再生/停止ボタン | `tooltip.btn.play` / `tooltip.btn.pause` |
| シークバー | `tooltip.seekbar` |
| 音量スライダー | `tooltip.volume` |
| +1F/-1F ボタン | `tooltip.btn.frame_plus` / `tooltip.btn.frame_minus` |
| A 点ボタン | `tooltip.btn.set_a` |
| B 点ボタン | `tooltip.btn.set_b` |
| AB ループトグル | `tooltip.btn.ab_loop` |
| ブックマーク: メモ | 既存 `bookmark.row.memo_tip` を活用 |
| ブックマーク: タグ | `tooltip.btn.edit_tags` |
| ブックマーク: カウンター | `tooltip.btn.reset_play_count` |
| ブックマーク: 削除 | 既存 `bookmark.row.delete_tip` を活用 |
| ポーズ秒スピンボックス | `tooltip.pause_interval` |

### Alternatives considered
| 手法 | 理由で却下 |
|------|-----------|
| `QToolTip::setFont()` でフォントカスタマイズ | スコープ外・YAGNI |
| ホバーイベントで独自ポップアップ | 標準 `setToolTip` で十分 |
