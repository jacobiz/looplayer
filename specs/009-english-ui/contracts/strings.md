# 翻訳文字列カタログ

**Feature**: `009-english-ui`
**File**: `looplayer/i18n.py` — `_STRINGS` 辞書
**Date**: 2026-03-16

---

## フォーマット

```python
_STRINGS: dict[str, dict[str, str]] = {
    "key": {"ja": "日本語テキスト", "en": "English text"},
    ...
}
```

`t(key: str) -> str` は `_STRINGS[key][_lang]` を返す。キーが未登録の場合はキー文字列をそのまま返す（フォールバック）。

---

## メニューバー

| キー | 日本語 | 英語 |
|------|--------|------|
| `menu.file` | `ファイル(&F)` | `File(&F)` |
| `menu.file.open` | `ファイルを開く(&O)` | `Open File(&O)` |
| `menu.file.open_folder` | `フォルダを開く` | `Open Folder` |
| `menu.file.recent` | `最近開いたファイル(&R)` | `Recent Files(&R)` |
| `menu.file.video_info` | `動画情報` | `Video Info` |
| `menu.file.screenshot` | `スクリーンショット` | `Screenshot` |
| `menu.file.export` | `ブックマークをエクスポート` | `Export Bookmarks` |
| `menu.file.import` | `ブックマークをインポート` | `Import Bookmarks` |
| `menu.file.quit` | `終了(&Q)` | `Quit(&Q)` |
| `menu.playback` | `再生(&P)` | `Playback(&P)` |
| `menu.playback.play_pause` | `再生/一時停止` | `Play/Pause` |
| `menu.playback.stop` | `停止` | `Stop` |
| `menu.playback.vol_up` | `音量アップ` | `Volume Up` |
| `menu.playback.vol_down` | `音量ダウン` | `Volume Down` |
| `menu.playback.mute` | `ミュート` | `Mute` |
| `menu.playback.speed` | `再生速度` | `Playback Speed` |
| `menu.playback.end_action` | `再生終了時の動作(&E)` | `End of Playback(&E)` |
| `menu.playback.end_stop` | `停止` | `Stop` |
| `menu.playback.end_rewind` | `先頭に戻る` | `Rewind` |
| `menu.playback.end_loop` | `ループ` | `Loop` |
| `menu.playback.audio_track` | `音声トラック(&A)` | `Audio Track(&A)` |
| `menu.playback.subtitle` | `字幕(&S)` | `Subtitles(&S)` |
| `menu.view` | `表示(&V)` | `View(&V)` |
| `menu.view.fullscreen` | `フルスクリーン` | `Fullscreen` |
| `menu.view.exit_fullscreen` | `フルスクリーン解除` | `Exit Fullscreen` |
| `menu.view.fit_window` | `ウィンドウをビデオに合わせる` | `Fit Window to Video` |
| `menu.view.always_on_top` | `常に最前面に表示` | `Always on Top` |
| `menu.help` | `ヘルプ(&H)` | `Help(&H)` |
| `menu.help.shortcuts` | `キーボードショートカット一覧` | `Keyboard Shortcuts` |

---

## コントロール・ラベル

| キー | 日本語 | 英語 |
|------|--------|------|
| `label.volume` | `音量:` | `Volume:` |
| `btn.play` | `再生` | `Play` |
| `btn.pause` | `一時停止` | `Pause` |
| `btn.ab_loop_on` | `ABループ: ON` | `AB Loop: ON` |
| `btn.ab_loop_off` | `ABループ: OFF` | `AB Loop: OFF` |

---

## ダイアログ・エラーメッセージ

| キー | 日本語 | 英語 |
|------|--------|------|
| `msg.file_not_found.title` | `ファイルが見つかりません` | `File Not Found` |
| `msg.file_not_found.body` | `ファイルが見つかりません:\n{path}` | `File not found:\n{path}` |
| `msg.export_error.title` | `エクスポートエラー` | `Export Error` |
| `msg.export_error.body` | `ファイルの書き込みに失敗しました:\n{error}` | `Failed to write file:\n{error}` |
| `msg.no_video.title` | `動画が開かれていません` | `No Video Open` |
| `msg.no_video.body` | `ブックマークをインポートするには動画を開いてください。` | `Please open a video to import bookmarks.` |
| `msg.import_error.title` | `インポートエラー` | `Import Error` |
| `msg.no_video_file.title` | `エラー` | `Error` |
| `msg.no_video_file.body` | `対応する動画ファイルが見つかりませんでした。` | `No supported video files found.` |
| `msg.ab_error.title` | `ABループエラー` | `AB Loop Error` |
| `msg.ab_error.body` | `A点はB点より前に設定してください。` | `Point A must be before Point B.` |
| `msg.bookmark_error.title` | `ブックマーク保存エラー` | `Bookmark Save Error` |

---

## ステータスバー

| キー | 日本語 | 英語 |
|------|--------|------|
| `status.screenshot_saved` | `保存しました: {path}` | `Saved: {path}` |
| `status.max_speed` | `最大速度です` | `Maximum speed` |
| `status.min_speed` | `最小速度です` | `Minimum speed` |

---

## ダイアログタイトル

| キー | 日本語 | 英語 |
|------|--------|------|
| `dialog.video_info.title` | `動画情報` | `Video Info` |
| `dialog.shortcuts.title` | `キーボードショートカット一覧` | `Keyboard Shortcuts` |

---

## ブックマークパネル

| キー | 日本語 | 英語 |
|------|--------|------|
| `bookmark.panel.title` | `ブックマーク一覧` | `Bookmarks` |
| `bookmark.panel.seq_play` | `連続再生` | `Sequential Play` |
| `bookmark.panel.seq_stop` | `連続再生 停止` | `Stop Sequential` |
| `bookmark.panel.seq_status` | `▶ 現在: {cur}  →  次: {nxt}` | `▶ Now: {cur}  →  Next: {nxt}` |
| `bookmark.row.repeat` | `繰返:` | `Repeat:` |
| `bookmark.row.enabled_tip` | `連続再生の対象にする` | `Include in sequential play` |
| `bookmark.row.name_tip` | `ダブルクリックで名前を編集` | `Double-click to edit name` |
| `bookmark.row.delete_tip` | `削除` | `Delete` |
| `bookmark.row.memo_tip` | `メモ` | `Memo` |
| `bookmark.row.memo_tip_content` | `メモ: {notes}` | `Memo: {notes}` |
| `bookmark.memo.title` | `メモを編集` | `Edit Memo` |
| `bookmark.memo.prompt` | `「{name}」のメモ:` | `Memo for "{name}":` |

---

## 注記

- `{path}`, `{error}`, `{cur}`, `{nxt}`, `{notes}`, `{name}` はフォーマット変数（Python f-string または `.format()` で埋め込む）
- キーが `_STRINGS` に存在しない場合、`t(key)` はキー文字列をそのまま返す（フォールバック）
- 字幕・音声トラック名はメディアファイル由来のためこのカタログの対象外
- 再生速度の値（`0.5x`, `1.0x` 等）は言語非依存のため対象外
