"""VideoPlayer メインウィンドウと起動関数。"""
import os
import sys
import vlc

# バンドルされた exe 実行時に VLC プラグインパスを設定
if getattr(sys, 'frozen', False):
    _vlc_plugins = os.path.join(sys._MEIPASS, 'plugins')
    if os.path.exists(_vlc_plugins):
        os.environ['VLC_PLUGIN_PATH'] = _vlc_plugins
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from looplayer.bookmark_io import export_bookmarks, import_bookmarks
from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.recent_files import RecentFiles
from looplayer.sequential import SequentialPlayState
from looplayer.utils import ms_to_str
from looplayer.version import APP_NAME, VERSION
from looplayer.widgets.bookmark_panel import BookmarkPanel
from looplayer.widgets.bookmark_slider import BookmarkSlider

# US3: 動画情報ダイアログ、US4: ショートカットダイアログで使用
from PyQt6.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QScrollArea
from PyQt6.QtGui import QShortcut


class VideoPlayer(QMainWindow):
    # VLC イベントスレッドから UI スレッドへ安全に渡すためのシグナル
    _error_occurred = pyqtSignal()
    # US3: VLC の MediaPlayerVideoChanged イベントを UI スレッドに転送
    _video_changed = pyqtSignal()

    def __init__(self, store: BookmarkStore | None = None, recent_storage=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.setMinimumSize(800, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self._current_video_path: str | None = None

        # FR-015: ファイルが開けない場合のエラーイベント購読
        self._error_occurred.connect(self._show_error_dialog)
        em = self.media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)

        # US3: 動画変更イベント → UI スレッドでポーリング開始
        self._video_changed.connect(self._start_size_poll)
        self._size_poll_timer = QTimer(self)
        self._size_poll_timer.setInterval(50)
        self._size_poll_timer.timeout.connect(self._poll_video_size)
        self._auto_resizing = False

        # US4: フルスクリーン中カーソル自動非表示
        self._cursor_hide_timer = QTimer(self)
        self._cursor_hide_timer.setSingleShot(True)
        self._cursor_hide_timer.setInterval(3000)
        self._cursor_hide_timer.timeout.connect(self._hide_cursor)

        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False

        # 連続再生状態
        self._seq_state: SequentialPlayState | None = None

        # 音量状態
        self._volume: int = 80
        self._is_muted: bool = False
        self._pre_mute_volume: int = 80

        # 再生速度状態
        self._playback_rate: float = 1.0

        # 常に最前面フラグ
        self._always_on_top: bool = False

        # ブックマークストア（テスト時は tmp_path を渡して実環境を汚染しない）
        self._store = store if store is not None else BookmarkStore()

        # US2: 最近開いたファイル（テスト時は tmp_path を渡す）
        self._recent = RecentFiles(storage_path=recent_storage)

        self._build_ui()
        self._build_menus()

        # US1: ドラッグ＆ドロップを有効化
        self.setAcceptDrops(True)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Video frame（フルスクリーン時も常時表示）
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        layout.addWidget(self.video_frame, stretch=1)

        # コントロール群コンテナ（フルスクリーン時に一括 hide/show）
        self.controls_panel = QWidget()
        controls_layout = QVBoxLayout(self.controls_panel)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        layout.addWidget(self.controls_panel)

        # 音量スライダー（シークバーの上）
        volume_bar = QHBoxLayout()
        self.volume_label = QLabel("80%")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self._on_volume_slider_changed)
        volume_bar.addWidget(QLabel("音量:"))
        volume_bar.addWidget(self.volume_slider)
        volume_bar.addWidget(self.volume_label)
        volume_bar.addStretch()
        controls_layout.addLayout(volume_bar)

        # Seek bar（BookmarkSlider でブックマーク区間を重ね描きする）
        seek_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.seek_slider = BookmarkSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        self.seek_slider.bookmark_bar_clicked.connect(self._on_bookmark_bar_clicked)
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.time_label)
        controls_layout.addLayout(seek_layout)

        # Playback controls
        ctrl_layout = QHBoxLayout()
        self.open_btn = QPushButton("開く")
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn = QPushButton("再生")
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop)
        ctrl_layout.addWidget(self.open_btn)
        ctrl_layout.addWidget(self.play_btn)
        ctrl_layout.addWidget(self.stop_btn)
        ctrl_layout.addStretch()
        controls_layout.addLayout(ctrl_layout)

        # AB loop controls
        ab_layout = QHBoxLayout()
        self.set_a_btn = QPushButton("A点セット")
        self.set_a_btn.clicked.connect(self.set_point_a)
        self.set_b_btn = QPushButton("B点セット")
        self.set_b_btn.clicked.connect(self.set_point_b)
        self.ab_toggle_btn = QPushButton("ABループ: OFF")
        self.ab_toggle_btn.setCheckable(True)
        self.ab_toggle_btn.clicked.connect(self.toggle_ab_loop)
        self.ab_reset_btn = QPushButton("ABリセット")
        self.ab_reset_btn.clicked.connect(self.reset_ab)
        self.ab_info_label = QLabel("A: --  B: --")
        ab_layout.addWidget(self.set_a_btn)
        ab_layout.addWidget(self.set_b_btn)
        ab_layout.addWidget(self.ab_toggle_btn)
        ab_layout.addWidget(self.ab_reset_btn)
        ab_layout.addWidget(self.ab_info_label)
        ab_layout.addStretch()
        controls_layout.addLayout(ab_layout)

        # ブックマーク保存ボタン（FR-001: A・B点設定済み時のみ有効）
        bookmark_save_layout = QHBoxLayout()
        self.save_bookmark_btn = QPushButton("ブックマーク保存")
        self.save_bookmark_btn.setEnabled(False)
        self.save_bookmark_btn.clicked.connect(self._save_bookmark)
        bookmark_save_layout.addWidget(self.save_bookmark_btn)
        bookmark_save_layout.addStretch()
        controls_layout.addLayout(bookmark_save_layout)

        # ブックマークパネル
        self.bookmark_panel = BookmarkPanel(self._store)
        self.bookmark_panel.bookmark_selected.connect(self._on_bookmark_selected)
        self.bookmark_panel.sequential_started.connect(self._on_sequential_started)
        self.bookmark_panel.sequential_stopped.connect(self._on_sequential_stopped)
        controls_layout.addWidget(self.bookmark_panel)

    def _build_menus(self):
        """メニューバーを構築する（T005/T006/T007/T013/T015/T017/T019）。"""
        # ── ファイルメニュー ──────────────────────────────────
        file_menu = self.menuBar().addMenu("ファイル(&F)")

        open_action = QAction("開く...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # US3: 動画情報（動画未選択時は無効）
        self._video_info_action = QAction("動画情報...", self)
        self._video_info_action.setEnabled(False)
        self._video_info_action.triggered.connect(self._show_video_info)
        file_menu.addAction(self._video_info_action)

        file_menu.addSeparator()

        # US2: 最近開いたファイル サブメニュー
        self._recent_menu = file_menu.addMenu("最近開いたファイル(&R)")
        self._rebuild_recent_menu()

        file_menu.addSeparator()

        # US6: ブックマークエクスポート（動画未選択時は無効）
        self._export_action = QAction("ブックマークをエクスポート...", self)
        self._export_action.setEnabled(False)
        self._export_action.triggered.connect(self._export_bookmarks)
        file_menu.addAction(self._export_action)

        # US6: ブックマークインポート
        import_action = QAction("ブックマークをインポート...", self)
        import_action.triggered.connect(self._import_bookmarks)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        quit_action = QAction("終了", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ── 再生メニュー ──────────────────────────────────────
        play_menu = self.menuBar().addMenu("再生(&P)")

        play_pause_action = QAction("再生/一時停止", self)
        play_pause_action.setShortcut(QKeySequence("Space"))
        play_pause_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        play_pause_action.triggered.connect(self.toggle_play)
        play_menu.addAction(play_pause_action)

        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.stop)
        play_menu.addAction(stop_action)

        play_menu.addSeparator()

        vol_up_action = QAction("音量を上げる", self)
        vol_up_action.setShortcut(QKeySequence(Qt.Key.Key_Up))
        vol_up_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        vol_up_action.triggered.connect(lambda: self._set_volume(self._volume + 10))
        play_menu.addAction(vol_up_action)

        vol_down_action = QAction("音量を下げる", self)
        vol_down_action.setShortcut(QKeySequence(Qt.Key.Key_Down))
        vol_down_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        vol_down_action.triggered.connect(lambda: self._set_volume(self._volume - 10))
        play_menu.addAction(vol_down_action)

        mute_action = QAction("ミュート", self)
        mute_action.setShortcut(QKeySequence("M"))
        mute_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        mute_action.triggered.connect(self._toggle_mute)
        play_menu.addAction(mute_action)

        play_menu.addSeparator()

        # 再生速度サブメニュー
        speed_menu = play_menu.addMenu("再生速度")
        self.speed_action_group = QActionGroup(self)
        self.speed_action_group.setExclusive(True)
        for rate, label in [(0.5, "0.5倍"), (0.75, "0.75倍"), (1.0, "標準 (1.0倍)"),
                            (1.25, "1.25倍"), (1.5, "1.5倍"), (2.0, "2.0倍")]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(rate == 1.0)
            action.setData(rate)
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            self.speed_action_group.addAction(action)
            speed_menu.addAction(action)
            action.triggered.connect(lambda checked, r=rate: self._set_playback_rate(r))

        # ── 表示メニュー ──────────────────────────────────────
        view_menu = self.menuBar().addMenu("表示(&V)")

        self.fullscreen_action = QAction("フルスクリーン", self)
        self.fullscreen_action.setShortcut(QKeySequence("F"))
        self.fullscreen_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

        esc_action = QAction("フルスクリーン解除", self)
        esc_action.setShortcut(QKeySequence("Escape"))
        esc_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        esc_action.triggered.connect(self._exit_fullscreen)
        view_menu.addAction(esc_action)

        view_menu.addSeparator()

        fit_window_action = QAction("ウィンドウを動画サイズに合わせる", self)
        fit_window_action.triggered.connect(self._start_size_poll)
        view_menu.addAction(fit_window_action)

        view_menu.addSeparator()

        self.always_on_top_action = QAction("常に最前面に表示", self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(False)
        self.always_on_top_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.always_on_top_action.triggered.connect(self._toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)

        # US5: ブックマーク削除 Undo (Ctrl+Z)
        undo_action = QAction("元に戻す", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        undo_action.triggered.connect(lambda: self.bookmark_panel.undo_delete())
        self.addAction(undo_action)

        # シークショートカット（←/→は音量上下と競合しないよう個別追加）
        seek_back_action = QAction("5秒戻る", self)
        seek_back_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        seek_back_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_back_action.triggered.connect(lambda: self._seek_relative(-5000))
        self.addAction(seek_back_action)

        seek_fwd_action = QAction("5秒進む", self)
        seek_fwd_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        seek_fwd_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_fwd_action.triggered.connect(lambda: self._seek_relative(5000))
        self.addAction(seek_fwd_action)

        # ── ヘルプメニュー ──────────────────────────────────────
        help_menu = self.menuBar().addMenu("ヘルプ(&H)")

        shortcut_list_action = QAction("ショートカット一覧", self)
        shortcut_list_action.triggered.connect(self._show_shortcut_dialog)
        help_menu.addAction(shortcut_list_action)

        # US4: ? キーでショートカット一覧を表示（ApplicationShortcut コンテキスト）
        self._shortcut_dialog_key = QShortcut(QKeySequence("?"), self)
        self._shortcut_dialog_key.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcut_dialog_key.activated.connect(self._show_shortcut_dialog)

        # フルスクリーン中のメニューバー自動非表示タイマー
        self._menu_hide_timer = QTimer(self)
        self._menu_hide_timer.setSingleShot(True)
        self._menu_hide_timer.timeout.connect(lambda: self.menuBar().hide() if self.isFullScreen() else None)

    # ── ファイル操作 ─────────────────────────────────────────

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "動画ファイルを開く",
            "",
            "動画ファイル (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;すべてのファイル (*)"
        )
        if not path:
            return
        self._open_path(path)

    def _open_path(self, path: str) -> None:
        """ダイアログなしでパスを直接開くコアロジック（D&D・最近開いたファイルで共用）。"""
        path = os.path.normpath(path)
        self._current_video_path = path
        media = self.instance.media_new(path)
        self.media_player.set_media(media)

        win_id = int(self.video_frame.winId())
        if sys.platform == "win32":
            self.media_player.set_hwnd(win_id)
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(win_id)
        else:
            self.media_player.set_xwindow(win_id)

        self.media_player.play()
        self.play_btn.setText("一時停止")
        self.setWindowTitle(f"Video Player - {os.path.basename(path)}")
        self.reset_ab()

        # FR-008: 動画に紐づくブックマークを自動ロード
        self.bookmark_panel.load_video(path)

        # FR-012: ファイルを開き直すたびに再生速度を 1.0 にリセット
        self._set_playback_rate(1.0)

        # US2: 最近開いたファイルに追加
        self._recent.add(path)
        self._rebuild_recent_menu()

        # US3: 動画変更シグナルを emit してポーリング開始
        self._video_changed.emit()

        # US6: 動画を開いたらエクスポートを有効化
        self._export_action.setEnabled(True)

        # US3: 動画を開いたら動画情報を有効化
        self._video_info_action.setEnabled(True)

        # US1: タイムラインバーを更新
        self._sync_slider_bookmarks()

    def _rebuild_recent_menu(self) -> None:
        """US2: 最近開いたファイルメニューを再構築する。"""
        from pathlib import Path as _Path
        self._recent_menu.clear()
        for p in self._recent.files:
            action = QAction(_Path(p).name, self)
            action.setToolTip(p)
            action.setData(p)
            action.triggered.connect(lambda checked, path=p: self._open_recent(path))
            self._recent_menu.addAction(action)

    def _open_recent(self, path: str) -> None:
        """US2: 最近開いたファイルを選択したときに呼ばれる。"""
        import os as _os
        if not _os.path.exists(path):
            self._recent.remove(path)
            self._rebuild_recent_menu()
            QMessageBox.warning(self, "ファイルが見つかりません", f"ファイルが見つかりません:\n{path}")
            return
        self._open_path(path)

    # ── US6: ブックマーク エクスポート/インポート ────────────

    def _export_bookmarks(self) -> None:
        """US6: 現在の動画のブックマークを JSON ファイルにエクスポートする。"""
        if self._current_video_path is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "ブックマークをエクスポート", "", "JSON ファイル (*.json);;すべてのファイル (*)"
        )
        if not path:
            return
        bms = self._store.get_bookmarks(self._current_video_path)
        try:
            export_bookmarks(bms, path)
        except OSError as e:
            QMessageBox.warning(self, "エクスポートエラー", f"ファイルの書き込みに失敗しました:\n{e}")

    def _import_bookmarks(self) -> None:
        """US6: JSON ファイルからブックマークをインポートする（重複スキップ）。"""
        if self._current_video_path is None:
            QMessageBox.warning(self, "動画が開かれていません", "ブックマークをインポートするには動画を開いてください。")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "ブックマークをインポート", "", "JSON ファイル (*.json);;すべてのファイル (*)"
        )
        if not path:
            return
        try:
            imported = import_bookmarks(path)
        except ValueError as e:
            QMessageBox.warning(self, "インポートエラー", str(e))
            return
        existing = self._store.get_bookmarks(self._current_video_path)
        existing_pairs = {(bm.point_a_ms, bm.point_b_ms) for bm in existing}
        for bm_dict in imported:
            pair = (bm_dict["point_a_ms"], bm_dict["point_b_ms"])
            if pair in existing_pairs:
                continue
            try:
                new_bm = LoopBookmark(
                    point_a_ms=bm_dict["point_a_ms"],
                    point_b_ms=bm_dict["point_b_ms"],
                    name=bm_dict.get("name", ""),
                    repeat_count=bm_dict.get("repeat_count", 1),
                    enabled=bm_dict.get("enabled", True),
                )
                self._store.add(self._current_video_path, new_bm)
                existing_pairs.add(pair)
            except ValueError:
                continue  # 不正なブックマーク（A >= B など）はスキップ
        self.bookmark_panel._refresh_list()
        self._sync_slider_bookmarks()

    # ── US3: ウィンドウリサイズ ──────────────────────────────

    def _on_vlc_video_changed(self) -> None:
        """動画変更時に呼ばれる → シグナル経由でポーリングを開始。"""
        self._video_changed.emit()

    def _start_size_poll(self) -> None:
        """UI スレッドでポーリングタイマーを開始する。"""
        self._user_resized = False
        self._size_poll_timer.start()

    def _poll_video_size(self) -> None:
        """50ms ごとに動画サイズを確認し、非ゼロになったらリサイズしてタイマーを停止。"""
        w, h = self.media_player.video_get_size()
        if w and h:
            self._size_poll_timer.stop()
            self._resize_to_video(w, h)

    def _resize_to_video(self, w: int, h: int) -> None:
        """動画解像度に合わせてウィンドウをリサイズする（クランプあり）。"""
        if self.isFullScreen():
            return
        screen = self.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            max_w, max_h = avail.width(), avail.height()
        else:
            max_w, max_h = 1920, 1080
        target_w = max(800, min(w, max_w))
        target_h = max(600, min(h, max_h))
        # 自動リサイズ中フラグを立てて resizeEvent が誤ってタイマーを止めないようにする
        self._auto_resizing = True
        try:
            self.resize(target_w, target_h)
        finally:
            self._auto_resizing = False

    def resizeEvent(self, event) -> None:
        """ユーザー手動リサイズ時にポーリングタイマーを停止する（自動リサイズ時は無視）。"""
        if not self._auto_resizing and self._size_poll_timer.isActive():
            self._size_poll_timer.stop()
        super().resizeEvent(event)

    _SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """US1: URL を含む DragEnter イベントを受け付ける。"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """US1: ドロップされたファイルのうち最初の対応拡張子ローカルファイルを開く。"""
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.splitext(path)[1].lower() in self._SUPPORTED_EXTENSIONS:
                    self._open_path(path)
                    return

    # ── 再生制御 ─────────────────────────────────────────────

    def toggle_play(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_btn.setText("再生")
        else:
            self.media_player.play()
            self.play_btn.setText("一時停止")

    def stop(self):
        self.media_player.stop()
        self.play_btn.setText("再生")
        self.seek_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def _seek_relative(self, ms: int):
        """現在位置から ms ミリ秒だけシークする。"""
        length_ms = self.media_player.get_length()
        if length_ms <= 0:
            return
        current_ms = self.media_player.get_time()
        new_ms = max(0, min(current_ms + ms, length_ms))
        self.media_player.set_time(new_ms)

    def _on_seek(self, value):
        if self.media_player.get_length() > 0:
            self.media_player.set_position(value / 1000.0)

    def _on_timer(self):
        length_ms = self.media_player.get_length()
        pos = self.media_player.get_position()

        if length_ms > 0 and not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(int(pos * 1000))
            self.time_label.setText(
                f"{ms_to_str(int(pos * length_ms))} / {ms_to_str(length_ms)}"
            )

        # 連続再生チェック（通常の AB ループより優先）
        if self._seq_state and self._seq_state.active:
            if length_ms > 0:
                current_ms = int(pos * length_ms)
                bm = self._seq_state.current_bookmark
                if current_ms >= bm.point_b_ms:
                    next_a = self._seq_state.on_b_reached()
                    self.media_player.set_time(next_a)
                    self.bookmark_panel.update_seq_status(self._seq_state)
                    # US1 T017: ブックマーク遷移時にスライダーの強調表示を更新
                    self._sync_slider_bookmarks()
            return

        # 通常 AB ループチェック
        if self.ab_loop_active and self.ab_point_a is not None and self.ab_point_b is not None:
            if length_ms > 0:
                current_ms = int(pos * length_ms)
                if current_ms >= self.ab_point_b:
                    self.media_player.set_time(self.ab_point_a)

    # ── 音量・ミュート操作 ────────────────────────────────────

    def _on_volume_slider_changed(self, value: int):
        """スライダー操作時に音量を更新する（スライダーへの再帰更新を避ける）。"""
        self._volume = value
        self._is_muted = False
        self.volume_label.setText(f"{self._volume}%")
        self.media_player.audio_set_volume(self._volume)

    def _set_volume(self, v: int):
        """音量を設定する（0〜100 クランプ・スライダー同期・VLC 反映）。"""
        self._is_muted = False
        self._volume = max(0, min(v, 100))
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(self._volume)
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(f"{self._volume}%")
        self.media_player.audio_set_volume(self._volume)

    def _toggle_mute(self):
        """ミュートをトグルする。"""
        if self._is_muted:
            self._volume = self._pre_mute_volume
            self._is_muted = False
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(self._volume)
            self.volume_slider.blockSignals(False)
            self.volume_label.setText(f"{self._volume}%")
            self.media_player.audio_set_volume(self._volume)
        else:
            self._pre_mute_volume = self._volume
            self._is_muted = True
            self._volume = 0
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(0)
            self.volume_slider.blockSignals(False)
            self.volume_label.setText("0%")
            self.media_player.audio_set_volume(0)

    # ── 再生速度操作 ──────────────────────────────────────────

    def _set_playback_rate(self, rate: float):
        """再生速度を設定し、メニューのチェックマークを更新する。"""
        self._playback_rate = rate
        self.media_player.set_rate(rate)
        # メニューのチェック状態を更新
        if hasattr(self, "speed_action_group"):
            for action in self.speed_action_group.actions():
                action.setChecked(action.data() == rate)

    # ── フルスクリーン操作 ────────────────────────────────────

    def toggle_fullscreen(self):
        """フルスクリーンをトグルする。"""
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self.showFullScreen()
            self.controls_panel.hide()
            self.menuBar().hide()
            self.video_frame.setMouseTracking(True)
            self.centralWidget().setMouseTracking(True)
            self.setMouseTracking(True)
            # US4: フルスクリーン突入時にカーソル非表示タイマー起動
            self._cursor_hide_timer.start()

    def _exit_fullscreen(self):
        """フルスクリーンを解除して通常ウィンドウに戻る。"""
        if self.isFullScreen():
            self._menu_hide_timer.stop()
            # US4: フルスクリーン解除時にタイマー停止・カーソル復元
            self._cursor_hide_timer.stop()
            self.unsetCursor()
            self.showNormal()
            self.controls_panel.show()
            self.menuBar().show()

    def _hide_cursor(self) -> None:
        """US4: フルスクリーン中のみカーソルを非表示にする。"""
        if self.isFullScreen():
            self.setCursor(Qt.CursorShape.BlankCursor)

    def mouseMoveEvent(self, event):
        """FR-016: フルスクリーン中のマウス追跡でメニューバーを自動表示。US4: カーソルを復元。"""
        if self.isFullScreen():
            if event.pos().y() < 15:
                self.menuBar().show()
                self._menu_hide_timer.start(2000)
            # US4: マウス移動でカーソル復元・タイマーリセット
            self.unsetCursor()
            self._cursor_hide_timer.start()
        super().mouseMoveEvent(event)

    # ── 常に最前面操作 ────────────────────────────────────────

    def _toggle_always_on_top(self):
        """常に最前面フラグをトグルする。"""
        self._always_on_top = not self._always_on_top
        flags = self.windowFlags()
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        was_fullscreen = self.isFullScreen()
        self.setWindowFlags(flags)
        if was_fullscreen:
            self.showFullScreen()
        else:
            self.show()
        self.always_on_top_action.setChecked(self._always_on_top)

    # ── AB ループ操作 ─────────────────────────────────────────

    def set_point_a(self):
        t = self.media_player.get_time()
        if t < 0:
            return
        self.ab_point_a = t
        self._update_ab_info()
        self._update_save_btn_state()

    def set_point_b(self):
        t = self.media_player.get_time()
        if t < 0:
            return
        self.ab_point_b = t
        self._update_ab_info()
        self._update_save_btn_state()

    def toggle_ab_loop(self, checked):
        if checked and self.ab_point_a is not None and self.ab_point_b is not None:
            if self.ab_point_a >= self.ab_point_b:
                QMessageBox.warning(self, "ABループエラー", "A点はB点より前に設定してください。")
                self.ab_toggle_btn.setChecked(False)
                return
        self.ab_loop_active = checked
        self.ab_toggle_btn.setChecked(checked)
        self.ab_toggle_btn.setText("ABループ: ON" if checked else "ABループ: OFF")

    def reset_ab(self):
        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False
        self.ab_toggle_btn.setChecked(False)
        self.ab_toggle_btn.setText("ABループ: OFF")
        self._update_ab_info()
        self._update_save_btn_state()

    def _update_ab_info(self):
        a_str = ms_to_str(self.ab_point_a) if self.ab_point_a is not None else "--"
        b_str = ms_to_str(self.ab_point_b) if self.ab_point_b is not None else "--"
        self.ab_info_label.setText(f"A: {a_str}  B: {b_str}")

    def _update_save_btn_state(self):
        """FR-001: A・B点が両方設定済み時のみ保存ボタンを有効化。"""
        enabled = self.ab_point_a is not None and self.ab_point_b is not None
        self.save_bookmark_btn.setEnabled(enabled)

    # ── ブックマーク操作 ──────────────────────────────────────

    def _save_bookmark(self):
        """FR-001: 現在の AB 区間をブックマークとして保存する。"""
        if self.ab_point_a is None or self.ab_point_b is None:
            return
        bm = LoopBookmark(point_a_ms=self.ab_point_a, point_b_ms=self.ab_point_b)
        video_length_ms = self.media_player.get_length()
        try:
            self.bookmark_panel.add_bookmark(bm, video_length_ms)
            self._sync_slider_bookmarks()
        except ValueError as e:
            QMessageBox.warning(self, "ブックマーク保存エラー", str(e))

    def _on_bookmark_selected(self, bookmark: LoopBookmark):
        """FR-003: ブックマーク選択時に AB ループを切り替える。"""
        self._seq_state = None
        self.bookmark_panel.stop_sequential()

        self.ab_point_a = bookmark.point_a_ms
        self.ab_point_b = bookmark.point_b_ms
        self.ab_loop_active = True
        self.ab_toggle_btn.setChecked(True)
        self.ab_toggle_btn.setText("ABループ: ON")
        self._update_ab_info()
        self._update_save_btn_state()
        self.media_player.set_time(bookmark.point_a_ms)
        if not self.media_player.is_playing():
            self.media_player.play()
            self.play_btn.setText("一時停止")
        self._sync_slider_bookmarks()

    # ── 連続再生操作 ──────────────────────────────────────────

    def _on_sequential_started(self, state: SequentialPlayState):
        """FR-006: 連続再生を開始する。"""
        self._seq_state = state
        # 通常 AB ループを無効化
        self.ab_loop_active = False
        self.ab_toggle_btn.setChecked(False)
        self.ab_toggle_btn.setText("ABループ: OFF")
        # 最初の区間のA点から再生開始
        self.media_player.set_time(state.current_bookmark.point_a_ms)
        if not self.media_player.is_playing():
            self.media_player.play()
            self.play_btn.setText("一時停止")
        self._sync_slider_bookmarks()

    def _on_sequential_stopped(self):
        """連続再生を停止して通常再生モードに戻る。"""
        if self._seq_state:
            self._seq_state.stop()
        self._seq_state = None
        self._sync_slider_bookmarks()

    # ── US3: 動画情報ダイアログ ──────────────────────────────────

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """ファイルサイズをバイト→人間可読形式に変換する（FR-013）。"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        return f"{size_bytes / 1024 ** 3:.2f} GB"

    def _show_video_info(self) -> None:
        """US3: 動画情報ダイアログを表示する（FR-013）。"""
        if self._current_video_path is None:
            return

        # ── ファイル情報 ──
        filename = os.path.basename(self._current_video_path)
        try:
            size_str = self._format_file_size(os.path.getsize(self._current_video_path))
        except OSError:
            size_str = "不明"

        length_ms = self.media_player.get_length()
        length_str = ms_to_str(length_ms) if length_ms > 0 else "不明"

        # ── VLC トラック情報 ──
        resolution_str = "不明"
        fps_str = "不明"
        video_codec_str = "不明"
        audio_codec_str = "不明"

        media = self.media_player.get_media()
        if media is not None:
            media.parse()
            tracks = media.tracks_get()
            if tracks:
                for track in tracks:
                    if track.type == vlc.TrackType.Video and resolution_str == "不明":
                        v = track.video.contents if track.video else None
                        if v:
                            if v.width and v.height:
                                resolution_str = f"{v.width} × {v.height}"
                            if v.frame_rate_num and v.frame_rate_den:
                                fps_val = v.frame_rate_num / v.frame_rate_den
                                fps_str = f"{fps_val:.2f}"
                        if track.codec:
                            desc = vlc.libvlc_media_get_codec_description(
                                vlc.TrackType.Video, track.codec
                            )
                            video_codec_str = desc if desc else "不明"
                    elif track.type == vlc.TrackType.Audio and audio_codec_str == "不明":
                        if track.codec:
                            desc = vlc.libvlc_media_get_codec_description(
                                vlc.TrackType.Audio, track.codec
                            )
                            audio_codec_str = desc if desc else "不明"

        # ── ダイアログ構築 ──
        dialog = QDialog(self)
        dialog.setWindowTitle("動画情報")
        dialog.setMinimumWidth(400)
        grid = QGridLayout(dialog)
        grid.setColumnMinimumWidth(0, 120)
        grid.setSpacing(6)

        rows = [
            ("ファイル名", filename),
            ("ファイルサイズ", size_str),
            ("再生時間", length_str),
            ("解像度", resolution_str),
            ("フレームレート", fps_str),
            ("映像コーデック", video_codec_str),
            ("音声コーデック", audio_codec_str),
        ]
        for row_idx, (key, value) in enumerate(rows):
            key_label = QLabel(key + ":")
            key_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_label = QLabel(value)
            val_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(key_label, row_idx, 0)
            grid.addWidget(val_label, row_idx, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        grid.addWidget(buttons, len(rows), 0, 1, 2)

        dialog.exec()

    # ── US4: ショートカット一覧ダイアログ ──────────────────────────

    # 全ショートカット定義（6カテゴリ）
    _SHORTCUTS = [
        ("再生操作", [
            ("Space", "再生 / 一時停止"),
            ("←", "5秒戻る"),
            ("→", "5秒進む"),
        ]),
        ("音量操作", [
            ("↑", "音量を上げる (+10)"),
            ("↓", "音量を下げる (−10)"),
            ("M", "ミュート切り替え"),
        ]),
        ("AB ループ操作", [
            ("A点セット", "ボタンクリックで A 点を設定"),
            ("B点セット", "ボタンクリックで B 点を設定"),
        ]),
        ("ブックマーク操作", [
            ("ブックマーク保存", "ボタンクリックで現在の AB 区間を保存"),
            ("Ctrl+Z", "ブックマーク削除を元に戻す（5 秒以内）"),
        ]),
        ("表示操作", [
            ("F", "フルスクリーン 切り替え"),
            ("Escape", "フルスクリーン 解除"),
        ]),
        ("ファイル操作", [
            ("Ctrl+O", "ファイルを開く"),
            ("Ctrl+Q", "終了"),
            ("?", "ショートカット一覧を表示"),
        ]),
    ]

    def _show_shortcut_dialog(self) -> None:
        """US4: ショートカット一覧ダイアログを表示する（FR-014）。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("キーボードショートカット一覧")
        dialog.setMinimumWidth(420)

        outer = QVBoxLayout(dialog)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(4)
        grid.setColumnMinimumWidth(0, 160)
        grid.setColumnMinimumWidth(1, 200)

        row = 0
        for category, entries in self._SHORTCUTS:
            cat_label = QLabel(f"【{category}】")
            cat_label.setStyleSheet("font-weight: bold; margin-top: 6px;")
            grid.addWidget(cat_label, row, 0, 1, 2)
            row += 1
            for key, desc in entries:
                key_label = QLabel(key)
                key_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                key_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                desc_label = QLabel(desc)
                desc_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                grid.addWidget(key_label, row, 0)
                grid.addWidget(desc_label, row, 1)
                row += 1

        scroll = QScrollArea()
        scroll.setWidget(grid_widget)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        outer.addWidget(buttons)

        dialog.exec()

    # ── US1: タイムライン同期 ────────────────────────────────────

    def _sync_slider_bookmarks(self) -> None:
        """US1: スライダーのブックマークバーを現在の動画・連続再生状態に合わせて更新する。"""
        if self._current_video_path is None:
            self.seek_slider.set_bookmarks([], 0)
            return
        bms = self._store.get_bookmarks(self._current_video_path)
        duration_ms = self.media_player.get_length()
        current_id = self._seq_state.current_bookmark.id if (self._seq_state and self._seq_state.active) else None
        self.seek_slider.set_bookmarks(bms, duration_ms, current_id)

    def _on_bookmark_bar_clicked(self, bookmark_id: str) -> None:
        """US1: スライダー上のブックマークバーをクリックしたときに該当ブックマークを選択する。"""
        if self._current_video_path is None:
            return
        for bm in self._store.get_bookmarks(self._current_video_path):
            if bm.id == bookmark_id:
                self._on_bookmark_selected(bm)
                break

    # ── VLC エラーハンドリング ────────────────────────────────

    def _on_media_error(self, _event):
        """VLC エラーイベントのコールバック（VLC スレッドから呼ばれる）。"""
        self._error_occurred.emit()

    def _show_error_dialog(self):
        """UI スレッドでエラーダイアログを表示する。直前の再生状態は変更しない。"""
        QMessageBox.warning(self, "エラー", "動画ファイルを開けませんでした。")


def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
