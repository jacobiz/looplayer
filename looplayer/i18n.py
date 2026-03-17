"""i18n: OS ロケールに基づく UI テキストの日本語/英語切替モジュール。

起動時に QLocale.system() でロケールを一度だけ検出し、t(key) で翻訳文字列を返す。
"""
from PyQt6.QtCore import QLocale

# ── ロケール検出 ────────────────────────────────────────────


def _detect_lang() -> str:
    """OS ロケールを検出して "ja" または "en" を返す。"""
    if QLocale.system().language() == QLocale.Language.Japanese:
        return "ja"
    return "en"


_lang: str = _detect_lang()

# ── 翻訳文字列辞書 ──────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    # メニューバー
    "menu.file":                    {"ja": "ファイル(&F)",                  "en": "File(&F)"},
    "menu.file.open":               {"ja": "ファイルを開く(&O)",             "en": "Open File(&O)"},
    "menu.file.open_folder":        {"ja": "フォルダを開く",                 "en": "Open Folder"},
    "menu.file.recent":             {"ja": "最近開いたファイル(&R)",          "en": "Recent Files(&R)"},
    "menu.file.video_info":         {"ja": "動画情報",                       "en": "Video Info"},
    "menu.file.screenshot":         {"ja": "スクリーンショット",              "en": "Screenshot"},
    "menu.file.export":             {"ja": "ブックマークをエクスポート",       "en": "Export Bookmarks"},
    "menu.file.import":             {"ja": "ブックマークをインポート",         "en": "Import Bookmarks"},
    "menu.file.quit":               {"ja": "終了(&Q)",                       "en": "Quit(&Q)"},
    "menu.playback":                {"ja": "再生(&P)",                       "en": "Playback(&P)"},
    "menu.playback.play_pause":     {"ja": "再生/一時停止",                   "en": "Play/Pause"},
    "menu.playback.stop":           {"ja": "停止",                           "en": "Stop"},
    "menu.playback.vol_up":         {"ja": "音量アップ",                     "en": "Volume Up"},
    "menu.playback.vol_down":       {"ja": "音量ダウン",                     "en": "Volume Down"},
    "menu.playback.mute":           {"ja": "ミュート",                       "en": "Mute"},
    "menu.playback.speed":          {"ja": "再生速度",                       "en": "Playback Speed"},
    "menu.playback.end_action":     {"ja": "再生終了時の動作(&E)",            "en": "End of Playback(&E)"},
    "menu.playback.end_stop":       {"ja": "停止",                           "en": "Stop"},
    "menu.playback.end_rewind":     {"ja": "先頭に戻る",                     "en": "Rewind"},
    "menu.playback.end_loop":       {"ja": "ループ",                         "en": "Loop"},
    "menu.playback.audio_track":    {"ja": "音声トラック(&A)",                "en": "Audio Track(&A)"},
    "menu.playback.subtitle":       {"ja": "字幕(&S)",                       "en": "Subtitles(&S)"},
    "menu.view":                    {"ja": "表示(&V)",                       "en": "View(&V)"},
    "menu.view.fullscreen":         {"ja": "フルスクリーン",                  "en": "Fullscreen"},
    "menu.view.exit_fullscreen":    {"ja": "フルスクリーン解除",              "en": "Exit Fullscreen"},
    "menu.view.fit_window":         {"ja": "ウィンドウをビデオに合わせる",    "en": "Fit Window to Video"},
    "menu.view.always_on_top":      {"ja": "常に最前面に表示",               "en": "Always on Top"},
    "menu.help":                    {"ja": "ヘルプ(&H)",                     "en": "Help(&H)"},
    "menu.help.shortcuts":          {"ja": "キーボードショートカット一覧",    "en": "Keyboard Shortcuts"},
    # コントロール・ラベル
    "label.volume":                 {"ja": "音量:",                          "en": "Volume:"},
    "btn.play":                     {"ja": "再生",                           "en": "Play"},
    "btn.pause":                    {"ja": "一時停止",                       "en": "Pause"},
    "btn.ab_loop_on":               {"ja": "ABループ: ON",                   "en": "AB Loop: ON"},
    "btn.ab_loop_off":              {"ja": "ABループ: OFF",                  "en": "AB Loop: OFF"},
    # ダイアログ・エラーメッセージ
    "msg.file_not_found.title":     {"ja": "ファイルが見つかりません",        "en": "File Not Found"},
    "msg.file_not_found.body":      {"ja": "ファイルが見つかりません:\n{path}", "en": "File not found:\n{path}"},
    "msg.export_error.title":       {"ja": "エクスポートエラー",              "en": "Export Error"},
    "msg.export_error.body":        {"ja": "ファイルの書き込みに失敗しました:\n{error}", "en": "Failed to write file:\n{error}"},
    "msg.no_video.title":           {"ja": "動画が開かれていません",          "en": "No Video Open"},
    "msg.no_video.body":            {"ja": "ブックマークをインポートするには動画を開いてください。", "en": "Please open a video to import bookmarks."},
    "msg.import_error.title":       {"ja": "インポートエラー",                "en": "Import Error"},
    "msg.no_video_file.title":      {"ja": "エラー",                         "en": "Error"},
    "msg.no_video_file.body":       {"ja": "対応する動画ファイルが見つかりませんでした。", "en": "No supported video files found."},
    "msg.ab_error.title":           {"ja": "ABループエラー",                  "en": "AB Loop Error"},
    "msg.ab_error.body":            {"ja": "A点はB点より前に設定してください。", "en": "Point A must be before Point B."},
    "msg.bookmark_error.title":     {"ja": "ブックマーク保存エラー",          "en": "Bookmark Save Error"},
    # ステータスバー
    "status.screenshot_saved":      {"ja": "保存しました: {path}",           "en": "Saved: {path}"},
    "status.max_speed":             {"ja": "最大速度です",                    "en": "Maximum speed"},
    "status.min_speed":             {"ja": "最小速度です",                    "en": "Minimum speed"},
    # ダイアログタイトル
    "dialog.video_info.title":      {"ja": "動画情報",                       "en": "Video Info"},
    "dialog.shortcuts.title":       {"ja": "キーボードショートカット一覧",    "en": "Keyboard Shortcuts"},
    # ブックマークパネル
    "bookmark.panel.title":         {"ja": "ブックマーク一覧",               "en": "Bookmarks"},
    "bookmark.panel.seq_play":      {"ja": "連続再生",                       "en": "Sequential Play"},
    "bookmark.panel.seq_stop":      {"ja": "連続再生 停止",                  "en": "Stop Sequential"},
    "bookmark.panel.seq_status":    {"ja": "▶ 現在: {cur}  →  次: {nxt}",   "en": "▶ Now: {cur}  →  Next: {nxt}"},
    "bookmark.row.repeat":          {"ja": "繰返:",                          "en": "Repeat:"},
    "bookmark.row.enabled_tip":     {"ja": "連続再生の対象にする",            "en": "Include in sequential play"},
    "bookmark.row.name_tip":        {"ja": "ダブルクリックで名前を編集",      "en": "Double-click to edit name"},
    "bookmark.row.delete_tip":      {"ja": "削除",                           "en": "Delete"},
    "bookmark.row.memo_tip":        {"ja": "メモ",                           "en": "Memo"},
    "bookmark.row.memo_tip_content":{"ja": "メモ: {notes}",                 "en": "Memo: {notes}"},
    "bookmark.memo.title":          {"ja": "メモを編集",                     "en": "Edit Memo"},
    "bookmark.memo.prompt":         {"ja": "「{name}」のメモ:",              "en": 'Memo for "{name}":'},
    "bookmark.name.edit_title":     {"ja": "名前を編集",                     "en": "Edit Name"},
    "bookmark.name.edit_prompt":    {"ja": "ブックマーク名:",                 "en": "Bookmark name:"},
}

# ── 公開 API ────────────────────────────────────────────────


def t(key: str) -> str:
    """翻訳文字列を返す。未登録キーはキー文字列をそのまま返す（フォールバック）。"""
    return _STRINGS.get(key, {}).get(_lang, key)
