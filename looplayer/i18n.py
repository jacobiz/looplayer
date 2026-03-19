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
    "menu.file.export_clip":        {"ja": "クリップを書き出す...",           "en": "Export Clip..."},
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
    "menu.view.mirror_display":     {"ja": "左右反転",                        "en": "Mirror Display"},
    "menu.playback.speed.standard": {"ja": "標準 ({rate}倍)",                 "en": "Standard ({rate}x)"},
    "menu.playback.speed.rate":     {"ja": "{rate}倍",                        "en": "{rate}x"},
    "menu.help":                    {"ja": "ヘルプ(&H)",                     "en": "Help(&H)"},
    "menu.help.shortcuts":          {"ja": "キーボードショートカット一覧",    "en": "Keyboard Shortcuts"},
    "menu.help.check_update":       {"ja": "更新を確認...",                   "en": "Check for Updates..."},
    "menu.help.auto_check":         {"ja": "起動時に更新を確認する",          "en": "Check for Updates on Startup"},
    # コントロール・ラベル
    "label.volume":                 {"ja": "音量:",                          "en": "Volume:"},
    "btn.open":                     {"ja": "開く",                           "en": "Open"},
    "btn.stop":                     {"ja": "停止",                           "en": "Stop"},
    "btn.set_a":                    {"ja": "A点セット",                      "en": "Set A"},
    "btn.set_b":                    {"ja": "B点セット",                      "en": "Set B"},
    "btn.ab_reset":                 {"ja": "ABリセット",                     "en": "Reset AB"},
    "btn.save_bookmark":            {"ja": "ブックマーク保存",               "en": "Save Bookmark"},
    "action.undo":                  {"ja": "元に戻す",                       "en": "Undo"},
    "action.seek_back":             {"ja": "5秒戻る",                        "en": "Seek Back 5s"},
    "action.seek_fwd":              {"ja": "5秒進む",                        "en": "Seek Forward 5s"},
    "btn.play":                     {"ja": "再生",                           "en": "Play"},
    "btn.pause":                    {"ja": "一時停止",                       "en": "Pause"},
    "btn.ab_loop_on":               {"ja": "ABループ: ON",                   "en": "AB Loop: ON"},
    "btn.ab_loop_off":              {"ja": "ABループ: OFF",                  "en": "AB Loop: OFF"},
    # 自動更新ダイアログ・エラーメッセージ
    "msg.update_available.title":   {"ja": "更新があります",                  "en": "Update Available"},
    "msg.update_available.body":    {"ja": "バージョン {ver} が利用可能です（現在: {current_ver}）。今すぐダウンロードしますか？", "en": "Version {ver} is available (current: {current_ver}). Download now?"},
    "msg.update_latest.title":      {"ja": "最新バージョンです",              "en": "Up to Date"},
    "msg.update_latest.body":       {"ja": "最新バージョン {ver} を使用中です。", "en": "You are using the latest version ({ver})."},
    "msg.update_check_failed.title":{"ja": "更新確認エラー",                  "en": "Update Check Failed"},
    "msg.update_check_failed.body": {"ja": "更新確認に失敗しました。インターネット接続を確認してください。", "en": "Failed to check for updates. Please check your internet connection."},
    "msg.update_download_failed.title": {"ja": "ダウンロードエラー",          "en": "Download Failed"},
    "dialog.export.title":          {"ja": "書き出し中...",                   "en": "Exporting..."},
    "dialog.download.title":        {"ja": "更新をダウンロード中...",          "en": "Downloading Update..."},
    "btn.download_now":             {"ja": "今すぐダウンロード",              "en": "Download Now"},
    "btn.later":                    {"ja": "あとで",                         "en": "Later"},
    "btn.retry":                    {"ja": "再試行",                         "en": "Retry"},
    "status.update_checking":       {"ja": "更新を確認中...",                 "en": "Checking for updates..."},
    # ダイアログ・エラーメッセージ
    "msg.export_success.title":     {"ja": "書き出し完了",                    "en": "Export Complete"},
    "msg.export_success.body":      {"ja": "{filename} を書き出しました。",   "en": "Exported {filename}."},
    "msg.ffmpeg_not_found.title":   {"ja": "ffmpeg が見つかりません",         "en": "ffmpeg Not Found"},
    "msg.ffmpeg_not_found.body":    {"ja": "クリップの書き出しには ffmpeg が必要です。\nhttps://ffmpeg.org/download.html からインストールしてください。", "en": "ffmpeg is required for clip export.\nInstall from https://ffmpeg.org/download.html"},
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
    "status.speed_fine_up":         {"ja": "速度 +0.05x",                     "en": "Speed +0.05x"},
    "status.speed_fine_down":       {"ja": "速度 -0.05x",                     "en": "Speed -0.05x"},
    # ダイアログタイトル
    "dialog.video_info.title":      {"ja": "動画情報",                       "en": "Video Info"},
    "dialog.shortcuts.title":       {"ja": "キーボードショートカット一覧",    "en": "Keyboard Shortcuts"},
    # ブックマークパネル
    "bookmark.panel.title":         {"ja": "ブックマーク一覧",               "en": "Bookmarks"},
    "bookmark.panel.seq_play":      {"ja": "連続再生",                       "en": "Sequential Play"},
    "bookmark.panel.seq_stop":      {"ja": "連続再生 停止",                  "en": "Stop Sequential"},
    "bookmark.panel.seq_status":    {"ja": "▶ 現在: {cur}  →  次: {nxt}",   "en": "▶ Now: {cur}  →  Next: {nxt}"},
    "bookmark.row.export_clip":     {"ja": "クリップを書き出す",             "en": "Export Clip"},
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
    # US1: A/B 点ショートカット
    "shortcut.set_a":               {"ja": "A点をセット (I)",                 "en": "Set Point A (I)"},
    "shortcut.set_b":               {"ja": "B点をセット (O)",                 "en": "Set Point B (O)"},
    # US2: フレーム単位微調整
    "btn.frame_minus":              {"ja": "-1F",                             "en": "-1F"},
    "btn.frame_plus":               {"ja": "+1F",                             "en": "+1F"},
    # US4: ループ間ポーズ
    "label.pause_interval":         {"ja": "ポーズ(秒):",                     "en": "Pause(s):"},
    # US6: 練習カウンター
    "label.play_count":             {"ja": "再生回数:",                       "en": "Play count:"},
    "btn.reset_play_count":         {"ja": "再生回数をリセット",               "en": "Reset play count"},
    # US9: タグ付け
    "label.tags":                   {"ja": "タグ:",                           "en": "Tags:"},
    "btn.edit_tags":                {"ja": "🏷",                              "en": "🏷"},
    "tag.edit_title":               {"ja": "タグを編集",                      "en": "Edit Tags"},
    "tag.edit_prompt":              {"ja": "タグ（カンマ区切り）:",             "en": "Tags (comma-separated):"},
    "tag.filter_label":             {"ja": "タグフィルタ:",                    "en": "Tag filter:"},
    # US5: 連続再生モード
    "seq.one_round":                {"ja": "1周停止",                         "en": "One Round"},
    "seq.infinite":                 {"ja": "無限ループ",                      "en": "Infinite Loop"},
    # US10: エクスポートモード
    "dialog.export.mode_copy":      {"ja": "高速（ストリームコピー）",          "en": "Fast (stream copy)"},
    "dialog.export.mode_transcode": {"ja": "正確（再エンコード・H.264）",      "en": "Precise (re-encode H.264)"},
    # US3: ブックマーク保存ダイアログ
    "bookmark.save_title":          {"ja": "ブックマーク保存",                 "en": "Save Bookmark"},
    "bookmark.save_prompt":         {"ja": "ブックマーク名:",                  "en": "Bookmark name:"},
    # US8: プレイリストパネル タブ名
    "tab.bookmarks":                {"ja": "ブックマーク",                     "en": "Bookmarks"},
    "tab.playlist":                 {"ja": "プレイリスト",                     "en": "Playlist"},
    # US10: エクスポートダイアログ ボタン
    "btn.export_start":             {"ja": "書き出し開始",                     "en": "Export"},
    # ExportWorker エラーメッセージ
    "error.ffmpeg_not_found":       {"ja": "ffmpeg が見つかりません。https://ffmpeg.org/download.html からインストールしてください。",
                                     "en": "ffmpeg not found. Install from https://ffmpeg.org/download.html"},
    "error.source_not_found":       {"ja": "ソースファイルが見つかりません: {path}",
                                     "en": "Source file not found: {path}"},
    "error.ffmpeg_error":           {"ja": "ffmpeg エラー (code {code}): {detail}",
                                     "en": "ffmpeg error (code {code}): {detail}"},
    # ── 016-p1-features ────────────────────────────────────────────────────────
    # F-201: 外部字幕ファイルの読み込み
    "menu.playback.subtitle.open_file": {"ja": "字幕ファイルを開く...",          "en": "Open Subtitle File..."},
    "msg.subtitle_no_video.title":      {"ja": "動画が開かれていません",          "en": "No Video Open"},
    "msg.subtitle_no_video.body":       {"ja": "字幕ファイルを読み込むには動画を開いてください。", "en": "Please open a video to load a subtitle file."},
    "msg.subtitle_bad_format.title":    {"ja": "非対応のファイル形式",            "en": "Unsupported File Format"},
    "msg.subtitle_bad_format.body":     {"ja": "SRT または ASS 形式の字幕ファイルを選択してください。", "en": "Please select a subtitle file in SRT or ASS format."},
    "msg.subtitle_load_error.title":    {"ja": "字幕読み込みエラー",              "en": "Subtitle Load Error"},
    "msg.subtitle_load_error.body":     {"ja": "字幕ファイルの読み込みに失敗しました。UTF-8 形式のファイルを使用してください。", "en": "Failed to load subtitle file. Please use a UTF-8 encoded file."},
    # F-403: ウィンドウ位置・サイズの記憶
    "menu.view.reset_window":           {"ja": "ウィンドウ位置をリセット",        "en": "Reset Window Position"},
    # F-502: ツールチップ
    "tooltip.btn.play":                 {"ja": "再生/一時停止 (Space)",           "en": "Play/Pause (Space)"},
    "tooltip.seekbar":                  {"ja": "クリックまたはドラッグで再生位置を変更", "en": "Click or drag to seek"},
    "tooltip.volume":                   {"ja": "音量を調整 (↑/↓)",               "en": "Adjust volume (↑/↓)"},
    "tooltip.btn.frame_minus":          {"ja": "1フレーム戻す (,)",               "en": "Go back 1 frame (,)"},
    "tooltip.btn.frame_plus":           {"ja": "1フレーム進める (.)",             "en": "Go forward 1 frame (.)"},
    "tooltip.btn.frame_a_minus":        {"ja": "A点を1フレーム前にずらす (Shift+,)", "en": "Move A point back 1 frame (Shift+,)"},
    "tooltip.btn.frame_a_plus":         {"ja": "A点を1フレーム後にずらす (Shift+.)", "en": "Move A point forward 1 frame (Shift+.)"},
    "tooltip.btn.frame_b_minus":        {"ja": "B点を1フレーム前にずらす (Ctrl+,)", "en": "Move B point back 1 frame (Ctrl+,)"},
    "tooltip.btn.frame_b_plus":         {"ja": "B点を1フレーム後にずらす (Ctrl+.)", "en": "Move B point forward 1 frame (Ctrl+.)"},
    "tooltip.btn.set_a":                {"ja": "A点を設定 (I)",                   "en": "Set point A (I)"},
    "tooltip.btn.set_b":                {"ja": "B点を設定 (O)",                   "en": "Set point B (O)"},
    "tooltip.btn.ab_loop":              {"ja": "ABループを切り替える",             "en": "Toggle AB loop"},
    "tooltip.btn.edit_tags":            {"ja": "タグを編集",                      "en": "Edit tags"},
    "tooltip.btn.reset_play_count":     {"ja": "再生回数をリセット",               "en": "Reset play count"},
    "tooltip.pause_interval":           {"ja": "ループ間の一時停止時間（秒）",     "en": "Pause duration between loops (seconds)"},
    # ── 017-p2-ux-features ─────────────────────────────────────────────────────
    # F-401: 設定画面
    "menu.file.preferences":            {"ja": "設定...",                          "en": "Preferences..."},
    "dialog.prefs.title":               {"ja": "設定",                             "en": "Preferences"},
    "dialog.prefs.tab.playback":        {"ja": "再生",                             "en": "Playback"},
    "dialog.prefs.tab.view":            {"ja": "表示",                             "en": "View"},
    "dialog.prefs.tab.updates":         {"ja": "アップデート",                     "en": "Updates"},
    "dialog.prefs.end_action.label":    {"ja": "再生終了時の動作",                 "en": "End of playback"},
    "dialog.prefs.end_action.stop":     {"ja": "停止",                             "en": "Stop"},
    "dialog.prefs.end_action.rewind":   {"ja": "先頭に戻る",                       "en": "Rewind"},
    "dialog.prefs.end_action.loop":     {"ja": "ループ",                           "en": "Loop"},
    "dialog.prefs.seq_mode.label":      {"ja": "連続再生モード",                   "en": "Sequential play"},
    "dialog.prefs.encode_mode.label":   {"ja": "エクスポートエンコードモード",     "en": "Export encode mode"},
    "dialog.prefs.always_on_top.label": {"ja": "常に最前面に表示（メニューで変更）", "en": "Always on top (change via menu)"},
    "dialog.prefs.check_update.label":  {"ja": "起動時に更新を確認する",           "en": "Check for updates on startup"},
    # F-501: 初回起動オンボーディング
    "menu.help.tutorial":               {"ja": "チュートリアルを表示",             "en": "Show Tutorial"},
    "onboarding.step0.title":           {"ja": "ようこそ！looplay! へ",            "en": "Welcome to looplay!"},
    "onboarding.step0.body":            {"ja": "AB ループ練習ツールへようこそ。まず動画ファイルを開きましょう。「ファイル > ファイルを開く」またはウィンドウにドラッグ＆ドロップで動画を読み込めます。",
                                         "en": "Welcome to looplay! Start by opening a video file. Use \"File > Open File\" or drag and drop a video onto the window."},
    "onboarding.step1.title":           {"ja": "A/B 点を設定する",                 "en": "Set A/B Points"},
    "onboarding.step1.body":            {"ja": "動画を再生しながら「A点」ボタンでループ開始点、「B点」ボタンでループ終了点を設定します。シークバーで任意の位置に移動してから設定するとより正確です。",
                                         "en": "While the video plays, press \"Set A\" to mark the loop start, and \"Set B\" for the loop end. Seek to the exact position first for precise results."},
    "onboarding.step2.title":           {"ja": "AB ループを再生する",               "en": "Play the AB Loop"},
    "onboarding.step2.body":            {"ja": "「AB ループ: OFF」ボタンを押すとループ再生が開始されます。A 点と B 点の間を繰り返し再生します。",
                                         "en": "Press the \"AB Loop: OFF\" button to start loop playback. The video will repeat between your A and B points."},
    "onboarding.step3.title":           {"ja": "ブックマークに保存する",            "en": "Save as Bookmark"},
    "onboarding.step3.body":            {"ja": "「ブックマーク保存」でこの区間を名前を付けて保存できます。保存した区間は左パネルのリストに表示され、いつでも呼び出せます。",
                                         "en": "Click \"Save Bookmark\" to save this loop section with a name. Saved bookmarks appear in the left panel and can be recalled anytime."},
    "onboarding.btn.next":              {"ja": "次へ",                             "en": "Next"},
    "onboarding.btn.finish":            {"ja": "完了",                             "en": "Finish"},
    "onboarding.btn.skip":              {"ja": "スキップ",                         "en": "Skip"},
    "onboarding.progress":              {"ja": "{step} / {total}",                 "en": "{step} / {total}"},
    # F-105: ABループ区間のズーム表示
    "btn.zoom_mode":                    {"ja": "ズーム",                           "en": "Zoom"},
    "tooltip.btn.zoom_mode":            {"ja": "AB区間をシークバー全幅に拡大表示 (Z)", "en": "Zoom to AB section (Z)"},
    # ── 019-subtitle-bookmark-backup ────────────────────────────────────────────
    # F-202: 字幕からブックマーク自動生成
    "menu.playback.subtitle.generate_bookmarks": {"ja": "字幕からブックマーク生成",        "en": "Generate Bookmarks from Subtitles"},
    "msg.subtitle_not_loaded.title":    {"ja": "字幕が読み込まれていません",         "en": "No Subtitle Loaded"},
    "msg.subtitle_not_loaded.body":     {"ja": "字幕ファイルが読み込まれていません。先に字幕ファイルを開いてください。", "en": "No subtitle file is loaded. Please open a subtitle file first."},
    "msg.subtitle_generate_success.title": {"ja": "ブックマーク生成完了",           "en": "Bookmarks Generated"},
    "msg.subtitle_generate_success.body":  {"ja": "{n} 件のブックマークを生成しました。", "en": "Generated {n} bookmarks."},
    "msg.subtitle_generate_skipped.title": {"ja": "ブックマーク生成完了",           "en": "Bookmarks Generated"},
    "msg.subtitle_generate_skipped.body":  {"ja": "{n} 件のブックマークを生成しました（{m} 件スキップ）。", "en": "Generated {n} bookmarks ({m} skipped)."},
    "msg.encoding_error.title":         {"ja": "エンコーディングエラー",             "en": "Encoding Error"},
    "msg.encoding_error.body":          {"ja": "字幕ファイルのエンコーディングを認識できませんでした。UTF-8 または Shift-JIS 形式のファイルを使用してください。", "en": "Could not detect subtitle file encoding. Please use UTF-8 or Shift-JIS encoding."},
    # F-402: データの一括バックアップ・復元
    "menu.file.backup_data":            {"ja": "データをバックアップ...",            "en": "Backup Data..."},
    "menu.file.restore_data":           {"ja": "データを復元...",                    "en": "Restore Data..."},
    "msg.backup_success.title":         {"ja": "バックアップ完了",                   "en": "Backup Complete"},
    "msg.backup_success.body":          {"ja": "{filename} にバックアップを保存しました。", "en": "Backup saved to {filename}."},
    "msg.backup_no_data.title":         {"ja": "バックアップ対象なし",               "en": "No Data to Backup"},
    "msg.backup_no_data.body":          {"ja": "バックアップ対象のデータファイルが見つかりませんでした。", "en": "No data files found to backup."},
    "msg.backup_write_error.title":     {"ja": "バックアップエラー",                 "en": "Backup Error"},
    "msg.backup_write_error.body":      {"ja": "バックアップの保存に失敗しました:\n{error}", "en": "Failed to save backup:\n{error}"},
    "msg.restore_confirm.title":        {"ja": "データを復元",                       "en": "Restore Data"},
    "msg.restore_confirm.body":         {"ja": "現在のデータはすべて上書きされます。よろしいですか？", "en": "All current data will be overwritten. Are you sure?"},
    "msg.restore_success.title":        {"ja": "復元完了",                           "en": "Restore Complete"},
    "msg.restore_success.body":         {"ja": "復元が完了しました。アプリを再起動してください。", "en": "Restore complete. Please restart the application."},
    "msg.restore_invalid.title":        {"ja": "無効なバックアップファイル",          "en": "Invalid Backup File"},
    "msg.restore_invalid.body":         {"ja": "このファイルは looplay! バックアップではありません。", "en": "This file is not a looplay! backup."},
    "msg.restore_corrupt.title":        {"ja": "バックアップファイルが破損しています",  "en": "Corrupt Backup File"},
    "msg.restore_corrupt.body":         {"ja": "バックアップファイルが破損しているため復元できません。", "en": "The backup file is corrupt and cannot be restored."},
    "msg.restore_write_error.title":    {"ja": "復元エラー",                         "en": "Restore Error"},
    "msg.restore_write_error.body":     {"ja": "データの復元に失敗しました:\n{error}", "en": "Failed to restore data:\n{error}"},
}

# ── 公開 API ────────────────────────────────────────────────


def t(key: str) -> str:
    """翻訳文字列を返す。未登録キーはキー文字列をそのまま返す（フォールバック）。"""
    return _STRINGS.get(key, {}).get(_lang, key)
