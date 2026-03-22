"""VideoPlayer メインウィンドウと起動関数。"""
import bisect
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
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox, QSplitter,
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal

import shutil
import subprocess
from pathlib import Path
from looplayer.bookmark_io import export_bookmarks, import_bookmarks
from looplayer.clip_export import ClipExportJob, ExportWorker
from looplayer.updater import UpdateChecker, DownloadDialog
from looplayer.widgets.export_dialog import ExportProgressDialog
from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t
from looplayer.recent_files import RecentFiles
from looplayer.sequential import SequentialPlayState
from looplayer.utils import ms_to_str
from looplayer.version import APP_NAME, VERSION
from looplayer.widgets.bookmark_panel import BookmarkPanel
from looplayer.widgets.bookmark_slider import BookmarkSlider
from looplayer.widgets.playlist_panel import PlaylistPanel

# US3: 動画情報ダイアログ、US4: ショートカットダイアログで使用
from PyQt6.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QScrollArea, QInputDialog
from PyQt6.QtGui import QShortcut


_PLAYBACK_RATES = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]


class VideoPlayer(QMainWindow):
    # VLC イベントスレッドから UI スレッドへ安全に渡すためのシグナル
    _error_occurred = pyqtSignal()
    # US3: VLC の MediaPlayerVideoChanged イベントを UI スレッドに転送
    _video_changed = pyqtSignal()
    # US4: VLC の MediaPlayerEndReached イベントを UI スレッドに転送
    _playback_ended = pyqtSignal()

    def __init__(self, store: BookmarkStore | None = None, recent_storage=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.setMinimumSize(800, 600)
        _icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if _icon_path.exists():
            self.setWindowIcon(QIcon(str(_icon_path)))

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self._current_video_path: str | None = None
        self._external_subtitle_path: Path | None = None
        self._is_audio: bool = False

        # FR-015: ファイルが開けない場合のエラーイベント購読
        self._error_occurred.connect(self._show_error_dialog)
        em = self.media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)

        # US4: 再生終了イベント → UI スレッドで終了時動作を実行
        self._playback_ended.connect(self._handle_playback_ended)
        em.event_attach(vlc.EventType.MediaPlayerEndReached, lambda e: self._playback_ended.emit())

        # US3: 動画変更イベント → UI スレッドでポーリング開始
        self._video_changed.connect(self._start_size_poll)
        self._size_poll_timer = QTimer(self)
        self._size_poll_timer.setInterval(50)
        self._size_poll_timer.timeout.connect(self._poll_video_size)
        self._auto_resizing = False
        self._size_poll_count: int = 0

        # US4: フルスクリーン中カーソル自動非表示
        self._cursor_hide_timer = QTimer(self)
        self._cursor_hide_timer.setSingleShot(True)
        self._cursor_hide_timer.setInterval(3000)
        self._cursor_hide_timer.timeout.connect(self._hide_cursor)

        # F-503: フルスクリーン中コントロールオーバーレイ自動非表示タイマー
        self._overlay_hide_timer = QTimer(self)
        self._overlay_hide_timer.setSingleShot(True)
        self._overlay_hide_timer.setInterval(3000)
        self._overlay_hide_timer.timeout.connect(self._hide_overlay)
        self._in_overlay_mode: bool = False  # フルスクリーンオーバーレイモード中フラグ

        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False

        # 連続再生状態
        self._seq_state: SequentialPlayState | None = None

        # US4: ループ間ポーズタイマー（スペースキーでキャンセル可能なので singleShot でなく QTimer インスタンス）
        self._pause_timer: QTimer | None = None

        # B点到達後のシーク完了待ちクールダウン（二重トリガー防止）
        self._b_handled_cooldown: int = 0

        # 音量状態
        self._volume: int = 80
        self._is_muted: bool = False
        self._pre_mute_volume: int = 80

        # 再生速度状態
        self._playback_rate: float = 1.0

        # 常に最前面フラグ
        self._always_on_top: bool = False

        # F-403: フルスクリーン前のウィンドウジオメトリ
        self._pre_fullscreen_geometry = None

        # US4: アプリ設定（再生終了動作など）
        from looplayer.app_settings import AppSettings
        self._app_settings = AppSettings()

        # US5: 再生位置の記憶
        from looplayer.playback_position import PlaybackPosition
        self._playback_position = PlaybackPosition()

        # US7: プレイリスト（フォルダドロップ時）
        self._playlist = None

        # ブックマークストア（テスト時は tmp_path を渡して実環境を汚染しない）
        self._store = store if store is not None else BookmarkStore()

        # US2: 最近開いたファイル（テスト時は tmp_path を渡す）
        self._recent = RecentFiles(storage_path=recent_storage)

        self._build_ui()
        self._build_menus()
        self._restore_window_geometry()

        # 010: 起動時更新確認（バックグラウンド）
        if self._app_settings.check_update_on_startup:
            self._start_update_check(silent=True)

        # US1: ドラッグ＆ドロップを有効化
        self.setAcceptDrops(True)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start()

        # F-501: 初回起動オンボーディング
        self._onboarding_overlay = None
        if not self._app_settings.onboarding_shown:
            from looplayer.widgets.onboarding_overlay import OnboardingOverlay
            self._onboarding_overlay = OnboardingOverlay(
                settings=self._app_settings, parent=self
            )
            self._onboarding_overlay.show()

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

        # 音楽再生中プレースホルダー（video_frame の子ウィジェットとしてオーバーレイ）
        self._audio_placeholder = QLabel("♫", self.video_frame)
        self._audio_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._audio_placeholder.setStyleSheet(
            "background-color: black; color: #888888; font-size: 64px;"
        )
        self._audio_placeholder.hide()

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
        self.volume_slider.setToolTip(t("tooltip.volume"))
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self._on_volume_slider_changed)
        volume_bar.addWidget(QLabel(t("label.volume")))
        volume_bar.addWidget(self.volume_slider)
        volume_bar.addWidget(self.volume_label)
        volume_bar.addStretch()
        controls_layout.addLayout(volume_bar)

        # Seek bar（BookmarkSlider でブックマーク区間を重ね描きする）
        seek_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.seek_slider = BookmarkSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setToolTip(t("tooltip.seekbar"))
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        self.seek_slider.bookmark_bar_clicked.connect(self._on_bookmark_bar_clicked)
        self.seek_slider.seek_requested.connect(self._on_seek_ms)
        self.seek_slider.ab_point_drag_finished.connect(self._on_ab_drag_finished)  # US3
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.time_label)
        controls_layout.addLayout(seek_layout)

        # Playback controls
        ctrl_layout = QHBoxLayout()
        self.open_btn = QPushButton(t("btn.open"))
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn = QPushButton(t("btn.play"))
        self.play_btn.setToolTip(t("tooltip.btn.play"))
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn = QPushButton(t("btn.stop"))
        self.stop_btn.clicked.connect(self.stop)
        ctrl_layout.addWidget(self.open_btn)
        ctrl_layout.addWidget(self.play_btn)
        ctrl_layout.addWidget(self.stop_btn)
        ctrl_layout.addStretch()
        controls_layout.addLayout(ctrl_layout)

        # AB loop controls
        ab_layout = QHBoxLayout()
        self.set_a_btn = QPushButton(t("btn.set_a"))
        self.set_a_btn.setToolTip(t("tooltip.btn.set_a"))
        self.set_a_btn.clicked.connect(self.set_point_a)
        self.set_b_btn = QPushButton(t("btn.set_b"))
        self.set_b_btn.setToolTip(t("tooltip.btn.set_b"))
        self.set_b_btn.clicked.connect(self.set_point_b)
        self.ab_toggle_btn = QPushButton(t("btn.ab_loop_off"))
        self.ab_toggle_btn.setToolTip(t("tooltip.btn.ab_loop"))
        self.ab_toggle_btn.setCheckable(True)
        self.ab_toggle_btn.clicked.connect(self.toggle_ab_loop)
        self.ab_reset_btn = QPushButton(t("btn.ab_reset"))
        self.ab_reset_btn.clicked.connect(self.reset_ab)
        self.ab_info_label = QLabel("A: --  B: --")
        self._zoom_btn = QPushButton(t("btn.zoom_mode"))
        self._zoom_btn.setToolTip(t("tooltip.btn.zoom_mode"))
        self._zoom_btn.setCheckable(True)
        self._zoom_btn.setEnabled(False)
        self._zoom_btn.clicked.connect(self._toggle_zoom_mode)
        ab_layout.addWidget(self.set_a_btn)
        ab_layout.addWidget(self.set_b_btn)
        ab_layout.addWidget(self.ab_toggle_btn)
        ab_layout.addWidget(self.ab_reset_btn)
        ab_layout.addWidget(self._zoom_btn)
        ab_layout.addWidget(self.ab_info_label)
        ab_layout.addStretch()
        controls_layout.addLayout(ab_layout)

        # ブックマーク保存ボタン（FR-001: A・B点設定済み時のみ有効）
        bookmark_save_layout = QHBoxLayout()
        self.save_bookmark_btn = QPushButton(t("btn.save_bookmark"))
        self.save_bookmark_btn.setEnabled(False)
        self.save_bookmark_btn.clicked.connect(self._save_bookmark)
        bookmark_save_layout.addWidget(self.save_bookmark_btn)
        bookmark_save_layout.addStretch()
        controls_layout.addLayout(bookmark_save_layout)

        # ブックマークパネル + プレイリストパネル（US8: QTabWidget で切り替え）
        from PyQt6.QtWidgets import QTabWidget
        self._panel_tabs = QTabWidget()

        self.bookmark_panel = BookmarkPanel(self._store)
        self.bookmark_panel.bookmark_selected.connect(self._on_bookmark_selected)
        self.bookmark_panel.sequential_started.connect(self._on_sequential_started)
        self.bookmark_panel.sequential_stopped.connect(self._on_sequential_stopped)
        self.bookmark_panel.export_requested.connect(self._export_clip_from_bookmark)
        self.bookmark_panel.frame_adjusted.connect(self._on_frame_adjusted)  # US2
        self.bookmark_panel.pause_ms_changed.connect(self._on_pause_ms_changed)  # US4
        self.bookmark_panel.play_count_reset.connect(self._on_play_count_reset)  # US6
        self.bookmark_panel.tags_changed.connect(self._on_tags_changed)  # US9
        self.bookmark_panel.seq_mode_toggled.connect(self._on_seq_mode_toggled)  # US5
        self.bookmark_panel.seek_to_ms_requested.connect(self._on_seek_to_ms)  # 022
        self.bookmark_panel.import_requested.connect(self._import_bookmarks)  # 022
        self.bookmark_panel.export_from_panel_requested.connect(self._export_bookmarks)  # 022

        self.playlist_panel = PlaylistPanel()
        self.playlist_panel.file_requested.connect(self._open_path)  # US8

        self._panel_tabs.addTab(self.bookmark_panel, t("tab.bookmarks"))
        self._playlist_tab_index = self._panel_tabs.addTab(self.playlist_panel, t("tab.playlist"))
        self._panel_tabs.setTabVisible(self._playlist_tab_index, False)

        # QSplitter で動画とパネルを横並びに（021: ブックマークサイドパネル）
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(self.video_frame)
        self._panel_tabs.setMinimumWidth(240)
        self._splitter.addWidget(self._panel_tabs)
        self.video_frame.setMinimumWidth(320)
        layout.insertWidget(0, self._splitter, stretch=1)

        # 初期サイズを AppSettings から遅延復元
        QTimer.singleShot(0, self._apply_initial_panel_width)

        # ステータスバー初期化（スクリーンショット通知・速度フィードバック等で使用）
        self.statusBar()

        # 022: 動画エリア右クリックオーバーレイ
        self._build_video_context_overlay()

    def _build_video_context_overlay(self) -> None:
        """動画エリアの右クリックを受け取るための透明オーバーレイ QWidget を生成する（022）。

        VLC が video_frame のネイティブウィンドウを占有するため、
        透明な子ウィジェットで右クリックイベントを受信する。
        """
        from PyQt6.QtWidgets import QWidget as _QWidget
        self._video_ctx_overlay = _QWidget(self.video_frame)
        self._video_ctx_overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._video_ctx_overlay.resize(self.video_frame.size())
        self._video_ctx_overlay.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._video_ctx_overlay.customContextMenuRequested.connect(self._show_video_context_menu)
        self._video_ctx_overlay.raise_()

    def _build_menus(self):
        """メニューバーを構築する（T005/T006/T007/T013/T015/T017/T019）。"""
        # ── ファイルメニュー ──────────────────────────────────
        file_menu = self.menuBar().addMenu(t("menu.file"))

        open_action = QAction(t("menu.file.open"), self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # US7: フォルダを開く
        open_folder_action = QAction(t("menu.file.open_folder"), self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        # US3: 動画情報（動画未選択時は無効）
        self._video_info_action = QAction(t("menu.file.video_info"), self)
        self._video_info_action.setEnabled(False)
        self._video_info_action.triggered.connect(self._show_video_info)
        file_menu.addAction(self._video_info_action)

        file_menu.addSeparator()

        # US2: 最近開いたファイル サブメニュー
        self._recent_menu = file_menu.addMenu(t("menu.file.recent"))
        self._rebuild_recent_menu()

        file_menu.addSeparator()

        # US3: スクリーンショット（動画未ロード時は無効）
        self._screenshot_action = QAction(t("menu.file.screenshot"), self)
        self._screenshot_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._screenshot_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._screenshot_action.setEnabled(False)
        self._screenshot_action.triggered.connect(self._take_screenshot)
        file_menu.addAction(self._screenshot_action)

        file_menu.addSeparator()

        # US6: ブックマークエクスポート（動画未選択時は無効）
        self._export_action = QAction(t("menu.file.export"), self)
        self._export_action.setEnabled(False)
        self._export_action.triggered.connect(self._export_bookmarks)
        file_menu.addAction(self._export_action)

        # US6: ブックマークインポート
        import_action = QAction(t("menu.file.import"), self)
        import_action.triggered.connect(self._import_bookmarks)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        # F-402: データバックアップ・復元
        backup_action = QAction(t("menu.file.backup_data"), self)
        backup_action.triggered.connect(self._backup_data)
        file_menu.addAction(backup_action)

        restore_action = QAction(t("menu.file.restore_data"), self)
        restore_action.triggered.connect(self._restore_data)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        # 011: クリップ書き出し
        self._clip_export_action = QAction(t("menu.file.export_clip"), self)
        self._clip_export_action.setShortcut(QKeySequence("Ctrl+E"))
        self._clip_export_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._clip_export_action.setEnabled(False)
        self._clip_export_action.triggered.connect(self._export_clip)
        file_menu.addAction(self._clip_export_action)

        file_menu.addSeparator()

        # F-401: 設定ダイアログ
        preferences_action = QAction(t("menu.file.preferences"), self)
        preferences_action.triggered.connect(self._open_preferences)
        file_menu.addAction(preferences_action)

        file_menu.addSeparator()

        quit_action = QAction(t("menu.file.quit"), self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ── 再生メニュー ──────────────────────────────────────
        play_menu = self.menuBar().addMenu(t("menu.playback"))

        play_pause_action = QAction(t("menu.playback.play_pause"), self)
        play_pause_action.setShortcut(QKeySequence("Space"))
        play_pause_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        play_pause_action.triggered.connect(self.toggle_play)
        play_menu.addAction(play_pause_action)

        stop_action = QAction(t("menu.playback.stop"), self)
        stop_action.triggered.connect(self.stop)
        play_menu.addAction(stop_action)

        play_menu.addSeparator()

        vol_up_action = QAction(t("menu.playback.vol_up"), self)
        vol_up_action.setShortcut(QKeySequence(Qt.Key.Key_Up))
        vol_up_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        vol_up_action.triggered.connect(lambda: self._set_volume(self._volume + 10))
        play_menu.addAction(vol_up_action)

        vol_down_action = QAction(t("menu.playback.vol_down"), self)
        vol_down_action.setShortcut(QKeySequence(Qt.Key.Key_Down))
        vol_down_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        vol_down_action.triggered.connect(lambda: self._set_volume(self._volume - 10))
        play_menu.addAction(vol_down_action)

        mute_action = QAction(t("menu.playback.mute"), self)
        mute_action.setShortcut(QKeySequence("M"))
        mute_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        mute_action.triggered.connect(self._toggle_mute)
        play_menu.addAction(mute_action)

        play_menu.addSeparator()

        # 再生速度サブメニュー（F-101: _PLAYBACK_RATES 10段階）
        speed_menu = play_menu.addMenu(t("menu.playback.speed"))
        self.speed_action_group = QActionGroup(self)
        self.speed_action_group.setExclusive(True)
        for rate in _PLAYBACK_RATES:
            label = (t("menu.playback.speed.standard").format(rate=rate) if rate == 1.0
                     else t("menu.playback.speed.rate").format(rate=rate))
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(rate == 1.0)
            action.setData(rate)
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            self.speed_action_group.addAction(action)
            speed_menu.addAction(action)
            action.triggered.connect(lambda checked, r=rate: self._set_playback_rate(r))

        play_menu.addSeparator()

        # US4: 再生終了時の動作サブメニュー
        end_action_menu = play_menu.addMenu(t("menu.playback.end_action"))
        end_action_group = QActionGroup(self)
        end_action_group.setExclusive(True)
        current_action = self._app_settings.end_of_playback_action
        for action_id, label in [("stop", t("menu.playback.end_stop")), ("rewind", t("menu.playback.end_rewind")), ("loop", t("menu.playback.end_loop"))]:
            a = QAction(label, self)
            a.setCheckable(True)
            a.setChecked(action_id == current_action)
            a.triggered.connect(lambda checked, v=action_id: setattr(self._app_settings, "end_of_playback_action", v))
            end_action_group.addAction(a)
            end_action_menu.addAction(a)
        self._end_action_menu = end_action_menu
        self._end_action_group = end_action_group

        play_menu.addSeparator()

        # US2: 音声トラック・字幕トラックサブメニュー
        self._audio_track_menu = play_menu.addMenu(t("menu.playback.audio_track"))
        self._audio_track_menu.setEnabled(False)
        self._audio_track_menu.aboutToShow.connect(self._rebuild_audio_track_menu)

        self._subtitle_menu = play_menu.addMenu(t("menu.playback.subtitle"))
        self._subtitle_menu.setEnabled(False)
        self._subtitle_menu.aboutToShow.connect(self._rebuild_subtitle_menu)

        # ── 表示メニュー ──────────────────────────────────────
        view_menu = self.menuBar().addMenu(t("menu.view"))

        self.fullscreen_action = QAction(t("menu.view.fullscreen"), self)
        self.fullscreen_action.setShortcut(QKeySequence("F"))
        self.fullscreen_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

        esc_action = QAction(t("menu.view.exit_fullscreen"), self)
        esc_action.setShortcut(QKeySequence("Escape"))
        esc_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        esc_action.triggered.connect(self._exit_fullscreen)
        view_menu.addAction(esc_action)
        # メニューバー非表示時（フルスクリーン中）でも ESC が確実に機能するよう
        # QShortcut を MainWindow に直接追加する（QAction ショートカットはメニューバー
        # が hide() されると ApplicationShortcut でも機能しなくなるため）
        esc_sc = QShortcut(QKeySequence("Escape"), self)
        esc_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        esc_sc.activated.connect(self._exit_fullscreen)

        view_menu.addSeparator()

        fit_window_action = QAction(t("menu.view.fit_window"), self)
        fit_window_action.triggered.connect(self._start_size_poll)
        view_menu.addAction(fit_window_action)

        view_menu.addSeparator()

        reset_window_action = QAction(t("menu.view.reset_window"), self)
        reset_window_action.triggered.connect(self._reset_window_geometry)
        view_menu.addAction(reset_window_action)

        view_menu.addSeparator()

        self.always_on_top_action = QAction(t("menu.view.always_on_top"), self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(False)
        self.always_on_top_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.always_on_top_action.triggered.connect(self._toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)

        # F-203: 左右反転（ミラー表示）
        self.mirror_action = QAction(t("menu.view.mirror_display"), self)
        self.mirror_action.setCheckable(True)
        self.mirror_action.setChecked(self._app_settings.mirror_display)
        self.mirror_action.triggered.connect(self._toggle_mirror_display)
        view_menu.addAction(self.mirror_action)

        # 021: ブックマークパネル表示切り替え（B キー）
        self._bookmark_panel_action = QAction(t("menu.view.bookmark_panel"), self)
        self._bookmark_panel_action.setCheckable(True)
        self._bookmark_panel_action.setChecked(self._app_settings.bookmark_panel_visible)
        self._bookmark_panel_action.setShortcut(QKeySequence("B"))
        self._bookmark_panel_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._bookmark_panel_action.triggered.connect(self._toggle_bookmark_panel)
        view_menu.addAction(self._bookmark_panel_action)

        # US5: ブックマーク削除 Undo (Ctrl+Z)
        undo_action = QAction(t("action.undo"), self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        undo_action.triggered.connect(self._handle_undo)
        self.addAction(undo_action)

        # シークショートカット（←/→は音量上下と競合しないよう個別追加）
        seek_back_action = QAction(t("action.seek_back"), self)
        seek_back_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        seek_back_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_back_action.triggered.connect(lambda: self._seek_relative(-5000))
        self.addAction(seek_back_action)

        seek_fwd_action = QAction(t("action.seek_fwd"), self)
        seek_fwd_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        seek_fwd_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_fwd_action.triggered.connect(lambda: self._seek_relative(5000))
        self.addAction(seek_fwd_action)

        # US1: 精細シーク ±1秒・±10秒
        seek_1s_back = QShortcut(QKeySequence("Shift+Left"), self)
        seek_1s_back.setContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_1s_back.activated.connect(lambda: self._seek_relative(-1000))
        seek_1s_fwd = QShortcut(QKeySequence("Shift+Right"), self)
        seek_1s_fwd.setContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_1s_fwd.activated.connect(lambda: self._seek_relative(1000))
        seek_10s_back = QShortcut(QKeySequence("Ctrl+Left"), self)
        seek_10s_back.setContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_10s_back.activated.connect(lambda: self._seek_relative(-10000))
        seek_10s_fwd = QShortcut(QKeySequence("Ctrl+Right"), self)
        seek_10s_fwd.setContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_10s_fwd.activated.connect(lambda: self._seek_relative(10000))

        # US1: 再生速度ショートカット
        speed_up_shortcut = QShortcut(QKeySequence("]"), self)
        speed_up_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        speed_up_shortcut.activated.connect(self._speed_up)
        speed_down_shortcut = QShortcut(QKeySequence("["), self)
        speed_down_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        speed_down_shortcut.activated.connect(self._speed_down)
        # F-101: 速度微調整ショートカット（0.05x 刻み）
        speed_fine_up_sc = QShortcut(QKeySequence("Shift+]"), self)
        speed_fine_up_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        speed_fine_up_sc.activated.connect(self._speed_fine_up)
        speed_fine_down_sc = QShortcut(QKeySequence("Shift+["), self)
        speed_fine_down_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        speed_fine_down_sc.activated.connect(self._speed_fine_down)

        # US1: フレームコマ送り
        frame_fwd_shortcut = QShortcut(QKeySequence("."), self)
        frame_fwd_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        frame_fwd_shortcut.activated.connect(self._frame_forward)
        frame_back_shortcut = QShortcut(QKeySequence(","), self)
        frame_back_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        frame_back_shortcut.activated.connect(self._frame_backward)

        # US1 (012): A/B 点キーボードショートカット（I=A点, O=B点）
        set_a_shortcut = QShortcut(QKeySequence("I"), self)
        set_a_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        set_a_shortcut.activated.connect(self.set_point_a)
        set_b_shortcut = QShortcut(QKeySequence("O"), self)
        set_b_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        set_b_shortcut.activated.connect(self.set_point_b)

        # US8: プレイリスト Alt+←/→ ナビゲーション
        playlist_next_sc = QShortcut(QKeySequence("Alt+Right"), self)
        playlist_next_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        playlist_next_sc.activated.connect(self._playlist_next)
        playlist_prev_sc = QShortcut(QKeySequence("Alt+Left"), self)
        playlist_prev_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        playlist_prev_sc.activated.connect(self._playlist_prev)

        # ── ヘルプメニュー ──────────────────────────────────────
        help_menu = self.menuBar().addMenu(t("menu.help"))

        shortcut_list_action = QAction(t("menu.help.shortcuts"), self)
        shortcut_list_action.triggered.connect(self._show_shortcut_dialog)
        help_menu.addAction(shortcut_list_action)

        # F-501: チュートリアル再表示
        tutorial_action = QAction(t("menu.help.tutorial"), self)
        tutorial_action.triggered.connect(self._show_tutorial)
        help_menu.addAction(tutorial_action)

        help_menu.addSeparator()

        check_update_action = QAction(t("menu.help.check_update"), self)
        check_update_action.triggered.connect(self._check_for_updates_manually)
        help_menu.addAction(check_update_action)

        self._auto_check_action = QAction(t("menu.help.auto_check"), self)
        self._auto_check_action.setCheckable(True)
        self._auto_check_action.setChecked(self._app_settings.check_update_on_startup)
        self._auto_check_action.toggled.connect(self._toggle_auto_check)
        help_menu.addAction(self._auto_check_action)

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
            t("dialog.open_video.title"),
            "",
            t("filter.media_file"),
        )
        if not path:
            return
        self._open_path(path)

    def open_folder(self) -> None:
        """US7: フォルダ選択ダイアログを開き、動画をプレイリストとして読み込む。"""
        from pathlib import Path as _Path
        folder = QFileDialog.getExistingDirectory(self, t("menu.file.open_folder"))
        if not folder:
            return
        self._open_folder(_Path(folder))

    def _open_path(self, path: str) -> None:
        """ダイアログなしでパスを直接開くコアロジック（D&D・最近開いたファイルで共用）。"""
        # US4: ファイル切替時にポーズタイマーをキャンセル
        self._cancel_pause_timer()
        # US5: 別ファイルを開く前に現在位置を保存
        if self._current_video_path:
            self._playback_position.save(
                self._current_video_path,
                self.media_player.get_time(),
                self.media_player.get_length(),
            )

        path = os.path.normpath(path)
        self._current_video_path = path
        self._external_subtitle_path = None
        # 音楽ファイル判定（拡張子ベース）とプレースホルダー表示更新
        self._is_audio = Path(path).suffix.lower() in self._SUPPORTED_AUDIO_EXTENSIONS
        self._update_audio_placeholder()
        media = self.instance.media_new(path)
        # F-203: ミラー表示が有効な場合、VLC の hflip フィルタを適用する
        if self._app_settings.mirror_display:
            media.add_option(':video-filter=transform')
            media.add_option(':transform-type=hflip')
        self.media_player.set_media(media)

        win_id = int(self.video_frame.winId())
        if sys.platform == "win32":
            self.media_player.set_hwnd(win_id)
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(win_id)
        else:
            self.media_player.set_xwindow(win_id)

        self.media_player.play()
        self.play_btn.setText(t("btn.pause"))
        self.setWindowTitle(f"{APP_NAME} - {os.path.basename(path)}")
        self.reset_ab()
        # US8: プレイリストパネルの現在ファイルハイライト更新
        if hasattr(self, "playlist_panel"):
            self.playlist_panel.update_current(path)

        # US5: 前回の再生位置を復元（少し遅延してシーク）
        saved_pos = self._playback_position.load(path)
        if saved_pos is not None:
            QTimer.singleShot(300, lambda: (
                self.media_player.set_time(saved_pos),
                self.media_player.pause(),
            ))

        # FR-008: 動画に紐づくブックマークを自動ロード
        self.bookmark_panel.load_video(path)

        # FR-012: ファイルを開き直すたびに再生速度を 1.0 にリセット
        self._set_playback_rate(1.0)

        # US2: 最近開いたファイルに追加
        self._recent.add(path)
        self._rebuild_recent_menu()

        # US3: 動画変更シグナルを emit してポーリング開始（音楽ファイルは映像なし）
        if not self._is_audio:
            self._video_changed.emit()

        # US6: 動画を開いたらエクスポートを有効化
        self._export_action.setEnabled(True)

        # US3: 動画を開いたら動画情報・スクリーンショットを有効化（音楽ファイルは無効）
        self._video_info_action.setEnabled(not self._is_audio)
        self._screenshot_action.setEnabled(not self._is_audio)

        # US2: 音声トラックメニューを有効化（音楽でも有効）、字幕は動画のみ
        self._audio_track_menu.setEnabled(True)
        self._subtitle_menu.setEnabled(not self._is_audio)

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
            QMessageBox.warning(self, t("msg.file_not_found.title"), t("msg.file_not_found.body").format(path=path))
            return
        self._open_path(path)

    # ── 011: クリップ書き出し ────────────────────────────────

    def _export_clip(self, start_ms: int | None = None, end_ms: int | None = None,
                     label: str | None = None) -> None:
        """AB ループ区間またはブックマーク区間をクリップとして書き出す。"""
        # ffmpeg 検出
        if shutil.which("ffmpeg") is None:
            QMessageBox.warning(
                self,
                t("msg.ffmpeg_not_found.title"),
                t("msg.ffmpeg_not_found.body"),
            )
            return

        # ソースファイル確認
        if self._current_video_path is None:
            return
        source = Path(self._current_video_path)
        if not source.exists():
            QMessageBox.warning(
                self,
                t("msg.file_not_found.title"),
                t("msg.file_not_found.body").format(path=source),
            )
            return

        # 区間の決定
        a_ms = start_ms if start_ms is not None else self.ab_point_a
        b_ms = end_ms if end_ms is not None else self.ab_point_b
        if a_ms is None or b_ms is None or a_ms >= b_ms:
            return

        # デフォルトファイル名の生成
        dummy_job = ClipExportJob(
            source_path=source,
            start_ms=a_ms,
            end_ms=b_ms,
            output_path=source.parent / "dummy",
        )
        if label:
            default_name = dummy_job.default_filename_for_bookmark(label)
        else:
            default_name = dummy_job.default_filename()

        # ファイル保存ダイアログ
        suffix = source.suffix
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            t("menu.file.export_clip"),
            str(source.parent / default_name),
            t("filter.audio_file_ext" if self._is_audio else "filter.video_file_ext").format(ext=suffix),
        )
        if not out_path:
            return

        # 書き出し実行
        job = ClipExportJob(
            source_path=source,
            start_ms=a_ms,
            end_ms=b_ms,
            output_path=Path(out_path),
        )
        self._clip_export_action.setEnabled(False)
        dlg = ExportProgressDialog(job, parent=self, settings=self._app_settings)
        result = dlg.exec()

        self._update_clip_export_action_state()

        if result == ExportProgressDialog.DialogCode.Accepted:
            out_file = Path(out_path)
            reply = QMessageBox.information(
                self,
                t("msg.export_success.title"),
                t("msg.export_success.body").format(filename=out_file.name),
                QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok,
            )
            if reply == QMessageBox.StandardButton.Open:
                self._open_folder_in_explorer(out_file.parent)

    def _export_clip_from_bookmark(self, a_ms: int, b_ms: int, label: str) -> None:
        """ブックマーク行からのクリップ書き出しリクエストを処理する。"""
        self._export_clip(start_ms=a_ms, end_ms=b_ms, label=label)

    @staticmethod
    def _open_folder_in_explorer(folder: Path) -> None:
        """OS のファイルマネージャーでフォルダを開く。"""
        import sys
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(folder)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    # ── US6: ブックマーク エクスポート/インポート ────────────

    def _export_bookmarks(self) -> None:
        """US6: 現在の動画のブックマークを JSON ファイルにエクスポートする。"""
        if self._current_video_path is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t("menu.file.export"), "", t("filter.json_file")
        )
        if not path:
            return
        bms = self._store.get_bookmarks(self._current_video_path)
        try:
            export_bookmarks(bms, path)
        except OSError as e:
            QMessageBox.warning(self, t("msg.export_error.title"), t("msg.export_error.body").format(error=e))

    def _import_bookmarks(self) -> None:
        """US6: JSON ファイルからブックマークをインポートする（重複スキップ）。"""
        if self._current_video_path is None:
            QMessageBox.warning(self, t("msg.no_video.title"), t("msg.no_video.body"))
            return
        path, _ = QFileDialog.getOpenFileName(
            self, t("menu.file.import"), "", t("filter.json_file")
        )
        if not path:
            return
        try:
            imported = import_bookmarks(path)
        except ValueError as e:
            QMessageBox.warning(self, t("msg.import_error.title"), str(e))
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

    def _start_size_poll(self) -> None:
        """UI スレッドでポーリングタイマーを開始する。"""
        self._size_poll_count = 0
        self._size_poll_timer.start()

    def _poll_video_size(self) -> None:
        """50ms ごとに動画サイズを確認し、非ゼロになったらリサイズしてタイマーを停止。
        100 回（5秒）経過しても動画サイズが取得できない場合はタイマーを強制停止する。
        """
        try:
            w, h = self.media_player.video_get_size()
        except Exception:
            self._size_poll_timer.stop()
            return
        if w and h:
            self._size_poll_timer.stop()
            self._resize_to_video(w, h)
            return
        self._size_poll_count += 1
        if self._size_poll_count >= 100:
            self._size_poll_timer.stop()

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
        # タイトルバー＋コントロール分の高さを加算してウィンドウサイズを求める
        ui_h_offset = self.height() - self.video_frame.height()
        # 幅方向: パネルが表示中の場合はパネル幅を加算する（021）
        panel_w = (
            self._splitter.sizes()[1]
            if hasattr(self, "_splitter") and not self._panel_tabs.isHidden()
            else 0
        )
        target_w = max(800, min(w + panel_w, max_w))
        target_h = max(600, min(h + ui_h_offset, max_h))
        # 自動リサイズ中フラグを立てて resizeEvent が誤ってタイマーを止めないようにする
        self._auto_resizing = True
        try:
            self.resize(target_w, target_h)
        finally:
            self._auto_resizing = False

    def _update_audio_placeholder(self) -> None:
        """音楽ファイル再生中プレースホルダーの表示状態を _is_audio に合わせて更新する。"""
        if self._is_audio:
            self._audio_placeholder.setGeometry(self.video_frame.rect())
            self._audio_placeholder.show()
            self._audio_placeholder.raise_()
        else:
            self._audio_placeholder.hide()

    def resizeEvent(self, event) -> None:
        """ユーザー手動リサイズ時にポーリングタイマーを停止する（自動リサイズ時は無視）。"""
        if not self._auto_resizing and self._size_poll_timer.isActive():
            self._size_poll_timer.stop()
        # F-501: オンボーディングオーバーレイを中央追従させる
        if self._onboarding_overlay is not None and not self._onboarding_overlay.isHidden():
            self._onboarding_overlay._reposition(self)
        # 音楽再生中プレースホルダーのジオメトリを更新する
        self._update_audio_placeholder()
        # 022: 動画エリア右クリックオーバーレイを video_frame に追従させる
        if hasattr(self, "_video_ctx_overlay"):
            self._video_ctx_overlay.resize(self.video_frame.size())
        super().resizeEvent(event)

    _SUPPORTED_VIDEO_EXTENSIONS = frozenset({
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    })
    _SUPPORTED_AUDIO_EXTENSIONS = frozenset({
        ".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus",
    })
    _SUPPORTED_EXTENSIONS = _SUPPORTED_VIDEO_EXTENSIONS | _SUPPORTED_AUDIO_EXTENSIONS

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """US1: URL を含む DragEnter イベントを受け付ける。"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """US1/US7: ドロップされたファイル・フォルダを処理する。"""
        from pathlib import Path as _Path
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            local = _Path(url.toLocalFile())
            if local.is_dir():
                self._open_folder(local)
                return
            if local.suffix.lower() in self._SUPPORTED_EXTENSIONS:
                self._playlist = None  # プレイリスト解除
                self._open_path(str(local))
                return

    def _open_folder(self, folder) -> None:
        """US7: フォルダ内の動画をファイル名昇順でプレイリスト再生する。"""
        from pathlib import Path as _Path
        from looplayer.playlist import Playlist
        from PyQt6.QtWidgets import QMessageBox
        files = sorted(
            p for p in _Path(folder).iterdir()
            if not p.name.startswith('.') and p.suffix.lower() in self._SUPPORTED_EXTENSIONS
        )
        if not files:
            QMessageBox.warning(self, t("msg.no_media_file.title"), t("msg.no_media_file.body"))
            return
        if len(files) == 1:
            self._playlist = None
            self._update_playlist_panel()
            self._open_path(str(files[0]))
            return
        self._playlist = Playlist(list(files))
        self._update_playlist_panel()
        self._open_path(str(self._playlist.current()))

    # ── 再生制御 ─────────────────────────────────────────────

    def toggle_play(self):
        # US4: ポーズタイマーがアクティブならキャンセルして再開
        if self._pause_timer is not None:
            self._cancel_pause_timer()
            if self.ab_point_a is not None:
                self._resume_after_pause(self.ab_point_a)
            elif self._seq_state and self._seq_state.active:
                self._resume_after_pause(self._seq_state.current_bookmark.point_a_ms)
            return
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_btn.setText(t("btn.play"))
        else:
            self.media_player.play()
            self.play_btn.setText(t("btn.pause"))

    def stop(self):
        self.media_player.stop()
        self.play_btn.setText(t("btn.play"))
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

    def _on_seek_ms(self, ms: int) -> None:
        """シークバークリック/ドラッグによる再生位置更新（FR-001, FR-001b）。"""
        if self.media_player.get_length() > 0:
            self.media_player.set_time(ms)

    def _on_timer(self):
        length_ms = self.media_player.get_length()
        pos = self.media_player.get_position()

        if length_ms > 0 and not self.seek_slider.isSliderDown() and not self.seek_slider.is_track_dragging:
            self.seek_slider.setValue(int(pos * 1000))
            self.time_label.setText(
                f"{ms_to_str(int(pos * length_ms))} / {ms_to_str(length_ms)}"
            )

        # ポーズタイマーアクティブ中はループ制御しない
        if self._pause_timer is not None:
            return

        # B点到達直後のシーク完了待ちクールダウン（二重トリガー防止）
        if self._b_handled_cooldown > 0:
            self._b_handled_cooldown -= 1
            return

        # 連続再生チェック（通常の AB ループより優先）
        if self._seq_state and self._seq_state.active:
            if length_ms > 0:
                current_ms = int(pos * length_ms)
                bm = self._seq_state.current_bookmark
                if current_ms >= bm.point_b_ms:
                    # US6: 再生回数インクリメント
                    if self._current_video_path:
                        self._store.increment_play_count(self._current_video_path, bm.id)
                        new_bms = self._store.get_bookmarks(self._current_video_path)
                        updated_bm = next((b for b in new_bms if b.id == bm.id), None)
                        if updated_bm:
                            self.bookmark_panel.update_play_count(bm.id, updated_bm.play_count)
                    next_a = self._seq_state.on_b_reached()
                    if next_a is None:
                        # US5: 1周停止モード — 連続再生終了
                        self._stop_seq_play()
                        return
                    self._b_handled_cooldown = 3  # 次の 3 tick（600ms）は B点判定をスキップ
                    self._start_pause_or_seek(next_a, bm.pause_ms)
                    self.bookmark_panel.update_seq_status(self._seq_state)
                    # US1 T017: ブックマーク遷移時にスライダーの強調表示を更新
                    self._sync_slider_bookmarks()
            return

        # 通常 AB ループチェック
        if self.ab_loop_active and self.ab_point_a is not None and self.ab_point_b is not None:
            if length_ms > 0:
                current_ms = int(pos * length_ms)
                if current_ms >= self.ab_point_b:
                    # US4: ポーズ間隔（通常 AB ループの場合は現在選択中ブックマークの pause_ms を使用）
                    pause_ms = 0
                    if self._current_video_path:
                        for bm in self._store.get_bookmarks(self._current_video_path):
                            if bm.point_a_ms == self.ab_point_a and bm.point_b_ms == self.ab_point_b:
                                pause_ms = bm.pause_ms
                                # US6: 再生回数インクリメント
                                self._store.increment_play_count(self._current_video_path, bm.id)
                                new_bms = self._store.get_bookmarks(self._current_video_path)
                                updated_bm = next((b for b in new_bms if b.id == bm.id), None)
                                if updated_bm:
                                    self.bookmark_panel.update_play_count(bm.id, updated_bm.play_count)
                                break
                    self._b_handled_cooldown = 3  # 次の 3 tick（600ms）は B点判定をスキップ
                    self._start_pause_or_seek(self.ab_point_a, pause_ms)

    def _start_pause_or_seek(self, next_a: int, pause_ms: int) -> None:
        """ポーズ間隔が設定されている場合はポーズタイマーを起動し、そうでなければ即座にシークする。"""
        if pause_ms > 0:
            self.media_player.pause()
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda a=next_a: self._resume_after_pause(a))
            self._pause_timer = timer
            timer.start(pause_ms)
        else:
            self.media_player.set_time(next_a)

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

    def _rebuild_audio_track_menu(self):
        """US2: 音声トラックメニューをリアルタイム再構築する（T010）。"""
        self._audio_track_menu.clear()
        descs = self.media_player.audio_get_track_description() or []
        group = QActionGroup(self)
        group.setExclusive(True)
        for track_id, name in descs:
            label = name.decode() if isinstance(name, bytes) else name
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.media_player.audio_get_track() == track_id)
            action.triggered.connect(lambda _, tid=track_id: self.media_player.audio_set_track(tid))
            group.addAction(action)
            self._audio_track_menu.addAction(action)
        self._audio_track_menu.setEnabled(len(descs) > 1)

    def _rebuild_subtitle_menu(self):
        """US2 / F-201 / F-202: 字幕メニューをリアルタイム再構築する。"""
        self._subtitle_menu.clear()
        # F-201: 「字幕ファイルを開く」は常に先頭に表示する
        open_action = QAction(t("menu.playback.subtitle.open_file"), self)
        open_action.triggered.connect(self._open_subtitle_file)
        self._subtitle_menu.addAction(open_action)
        # F-202: 「字幕からブックマーク生成」（外部字幕が読み込まれている場合のみ有効）
        gen_action = QAction(t("menu.playback.subtitle.generate_bookmarks"), self)
        gen_action.setEnabled(
            self._current_video_path is not None
            and self._external_subtitle_path is not None
        )
        gen_action.triggered.connect(self._generate_bookmarks_from_subtitles)
        self._subtitle_menu.addAction(gen_action)
        self._subtitle_menu.addSeparator()
        descs = self.media_player.video_get_spu_description() or []
        group = QActionGroup(self)
        group.setExclusive(True)
        off_action = QAction(t("menu.playback.subtitle.none"), self)
        off_action.setCheckable(True)
        off_action.setChecked(self.media_player.video_get_spu() == -1)
        off_action.triggered.connect(lambda: self.media_player.video_set_spu(-1))
        group.addAction(off_action)
        self._subtitle_menu.addAction(off_action)
        for track_id, name in descs:
            label = name.decode() if isinstance(name, bytes) else name
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.media_player.video_get_spu() == track_id)
            action.triggered.connect(lambda _, tid=track_id: self.media_player.video_set_spu(tid))
            group.addAction(action)
            self._subtitle_menu.addAction(action)

    def _open_preferences(self) -> None:
        """F-401: 設定ダイアログを開く。"""
        from looplayer.widgets.preferences_dialog import PreferencesDialog
        dialog = PreferencesDialog(settings=self._app_settings, parent=self)
        dialog.exec()

    def _show_tutorial(self) -> None:
        """F-501: チュートリアルオーバーレイを再表示する（ヘルプメニューから）。"""
        from looplayer.widgets.onboarding_overlay import OnboardingOverlay
        if self._onboarding_overlay is not None:
            self._onboarding_overlay.deleteLater()
        self._onboarding_overlay = OnboardingOverlay(
            settings=self._app_settings, parent=self
        )
        self._onboarding_overlay.show()

    def _open_subtitle_file(self) -> None:
        """F-201: 外部字幕ファイルを開いて VLC に読み込む（FR-102〜FR-106）。"""
        if self._current_video_path is None:
            QMessageBox.warning(
                self,
                t("msg.subtitle_no_video.title"),
                t("msg.subtitle_no_video.body"),
            )
            return

        path_str, _ = QFileDialog.getOpenFileName(
            self,
            t("menu.playback.subtitle.open_file"),
            "",
            t("filter.subtitle_file"),
        )
        if not path_str:
            return

        sub_path = Path(path_str)
        if sub_path.suffix.lower() not in (".srt", ".ass", ".ssa", ".vtt"):
            QMessageBox.warning(
                self,
                t("msg.subtitle_bad_format.title"),
                t("msg.subtitle_bad_format.body").format(ext=sub_path.suffix),
            )
            return

        uri = sub_path.as_uri()
        ok = self.media_player.add_slave(vlc.MediaSlaveType.subtitle, uri, True)
        if not ok:
            QMessageBox.warning(
                self,
                t("msg.subtitle_load_error.title"),
                t("msg.subtitle_load_error.body").format(path=str(sub_path)),
            )
            return

        self._external_subtitle_path = sub_path

    def _handle_undo(self) -> None:
        """Ctrl+Z: 一括生成 Undo を優先し、なければ削除 Undo にフォールバック（FR-008）。"""
        if self.bookmark_panel._last_bulk_add:
            self.bookmark_panel.undo_bulk_add()
        else:
            self.bookmark_panel.undo_delete()

    def _generate_bookmarks_from_subtitles(self) -> None:
        """F-202: 字幕ファイルからブックマークを一括生成する（FR-001〜FR-008）。"""
        from looplayer.subtitle_parser import parse_subtitle_file, entries_to_bookmarks
        if self._external_subtitle_path is None:
            QMessageBox.warning(
                self,
                t("msg.subtitle_not_loaded.title"),
                t("msg.subtitle_not_loaded.body"),
            )
            return
        if self._current_video_path is None:
            return
        try:
            entries = parse_subtitle_file(self._external_subtitle_path)
        except (ValueError, OSError):
            QMessageBox.warning(
                self,
                t("msg.encoding_error.title"),
                t("msg.encoding_error.body"),
            )
            return
        existing = self._store.get_bookmarks(self._current_video_path)
        result = entries_to_bookmarks(entries, start_order=len(existing))
        if result.bookmarks:
            self._store.add_many(self._current_video_path, result.bookmarks)
            self.bookmark_panel.set_last_bulk_add(result.bookmarks)
            self.bookmark_panel.load_video(self._current_video_path)
        if result.skipped > 0:
            QMessageBox.information(
                self,
                t("msg.subtitle_generate_skipped.title"),
                t("msg.subtitle_generate_skipped.body").format(
                    n=result.added, m=result.skipped
                ),
            )
        else:
            QMessageBox.information(
                self,
                t("msg.subtitle_generate_success.title"),
                t("msg.subtitle_generate_success.body").format(n=result.added),
            )

    def _backup_data(self) -> None:
        """F-402: データをバックアップする（FR-009〜FR-011）。"""
        from looplayer.data_backup import BackupError, create_backup, generate_backup_filename
        filename = generate_backup_filename()
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            t("menu.file.backup_data"),
            filename,
            t("filter.zip_file"),
        )
        if not path_str:
            return
        try:
            create_backup(Path(path_str))
            QMessageBox.information(
                self,
                t("msg.backup_success.title"),
                t("msg.backup_success.body").format(filename=Path(path_str).name),
            )
        except BackupError:
            QMessageBox.warning(
                self,
                t("msg.backup_no_data.title"),
                t("msg.backup_no_data.body"),
            )
        except OSError as e:
            QMessageBox.warning(
                self,
                t("msg.backup_write_error.title"),
                t("msg.backup_write_error.body").format(error=str(e)),
            )

    def _restore_data(self) -> None:
        """F-402: バックアップからデータを復元する（FR-012〜FR-015）。"""
        from looplayer.data_backup import BackupError, restore_backup
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            t("menu.file.restore_data"),
            "",
            t("filter.zip_file_all"),
        )
        if not path_str:
            return
        reply = QMessageBox.question(
            self,
            t("msg.restore_confirm.title"),
            t("msg.restore_confirm.body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            restore_backup(Path(path_str))
            QMessageBox.information(
                self,
                t("msg.restore_success.title"),
                t("msg.restore_success.body"),
            )
            QApplication.instance().quit()
        except BackupError as e:
            if e.reason == "corrupt":
                QMessageBox.warning(
                    self,
                    t("msg.restore_corrupt.title"),
                    t("msg.restore_corrupt.body"),
                )
            else:
                QMessageBox.warning(
                    self,
                    t("msg.restore_invalid.title"),
                    t("msg.restore_invalid.body"),
                )
        except OSError as e:
            QMessageBox.warning(
                self,
                t("msg.restore_write_error.title"),
                t("msg.restore_write_error.body").format(error=str(e)),
            )

    def _take_screenshot(self):
        """US3: 現在フレームをデスクトップに PNG 保存する（T013）。"""
        if not self._current_video_path:
            return
        from datetime import datetime
        from pathlib import Path
        desktop = Path.home() / "Desktop"
        save_dir = desktop if desktop.exists() else Path.home()
        filename = f"LoopPlayer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = save_dir / filename
        self.media_player.video_take_snapshot(0, str(path), 0, 0)
        self.statusBar().showMessage(t("status.screenshot_saved").format(path=path), 3000)

    def _speed_up(self):
        """再生速度を1段階上げる（US1）。微調整後の中間値でも次の固定段階へ進む。"""
        idx = bisect.bisect_right(_PLAYBACK_RATES, self._playback_rate)
        if idx < len(_PLAYBACK_RATES):
            self._set_playback_rate(_PLAYBACK_RATES[idx])
        else:
            self.statusBar().showMessage(t("status.max_speed"), 2000)

    def _speed_down(self):
        """再生速度を1段階下げる（US1）。微調整後の中間値でも前の固定段階へ戻る。"""
        idx = bisect.bisect_left(_PLAYBACK_RATES, self._playback_rate)
        if idx > 0:
            self._set_playback_rate(_PLAYBACK_RATES[idx - 1])
        else:
            self.statusBar().showMessage(t("status.min_speed"), 2000)

    def _speed_fine_up(self):
        """再生速度を 0.05x 単位で上げる（F-101）。上限 3.0x でクリップ。"""
        new_rate = min(3.0, round(self._playback_rate + 0.05, 2))
        self._set_playback_rate(new_rate)
        if new_rate >= 3.0:
            self.statusBar().showMessage(t("status.max_speed"), 2000)
        else:
            self.statusBar().showMessage(t("status.speed_fine_up"), 2000)

    def _speed_fine_down(self):
        """再生速度を 0.05x 単位で下げる（F-101）。下限 0.25x でクリップ。"""
        new_rate = max(0.25, round(self._playback_rate - 0.05, 2))
        self._set_playback_rate(new_rate)
        if new_rate <= 0.25:
            self.statusBar().showMessage(t("status.min_speed"), 2000)
        else:
            self.statusBar().showMessage(t("status.speed_fine_down"), 2000)

    def _frame_forward(self):
        """1フレーム進める（US1）。再生中は自動一時停止する。"""
        if self.media_player.is_playing():
            self.media_player.pause()
        self.media_player.next_frame()

    def _frame_backward(self):
        """1フレーム戻る（US1）。再生中は自動一時停止する。"""
        if self.media_player.is_playing():
            self.media_player.pause()
        fps = self.media_player.get_fps()
        frame_ms = int(1000.0 / fps) if fps > 0 else 40  # フォールバック: 25fps
        current_ms = self.media_player.get_time()
        self.media_player.set_time(max(0, current_ms - frame_ms))

    # ── フルスクリーン操作 ────────────────────────────────────

    def toggle_fullscreen(self):
        """フルスクリーンをトグルする。"""
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            # F-403: フルスクリーン突入前にジオメトリを保持する
            self._pre_fullscreen_geometry = self.geometry()
            self.showFullScreen()
            self._enter_fullscreen_overlay_mode()
            self.menuBar().hide()
            self.statusBar().hide()
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
            self._pre_fullscreen_geometry = None
            self._exit_fullscreen_overlay_mode()
            self.menuBar().show()
            self.statusBar().show()

    # ── F-503: フルスクリーンオーバーレイ ────────────────────────

    def _enter_fullscreen_overlay_mode(self) -> None:
        """controls_panel をレイアウトから外してフローティングオーバーレイに切り替える。"""
        # 021: フルスクリーン前のパネル表示状態を保存して非表示にする
        self._panel_tabs_was_visible = not self._panel_tabs.isHidden()
        self._panel_tabs.hide()
        layout = self.centralWidget().layout()
        layout.removeWidget(self.controls_panel)
        self.controls_panel.setParent(self)
        self._reposition_overlay()
        self.controls_panel.hide()
        self._in_overlay_mode = True

    def _exit_fullscreen_overlay_mode(self) -> None:
        """controls_panel をレイアウトに戻して通常表示に復元する。"""
        self._overlay_hide_timer.stop()
        self._in_overlay_mode = False
        layout = self.centralWidget().layout()
        layout.addWidget(self.controls_panel)
        self.controls_panel.show()
        # 021: フルスクリーン前の表示状態を復元する
        if getattr(self, "_panel_tabs_was_visible", False):
            self._panel_tabs.show()
            total = self._splitter.width()
            w = self._clamp_panel_width(total)
            self._splitter.setSizes([total - w, w])

    def _reposition_overlay(self) -> None:
        """controls_panel のオーバーレイ位置（画面下端）を計算してセットする。"""
        w = self.width()
        h = self.height()
        overlay_h = self.controls_panel.sizeHint().height() or 80
        self.controls_panel.setGeometry(0, h - overlay_h, w, overlay_h)
        self.controls_panel.raise_()

    def _show_overlay(self) -> None:
        """コントロールオーバーレイを表示してタイマーをリセットする。"""
        self._reposition_overlay()
        self.controls_panel.show()
        self.unsetCursor()
        self._overlay_hide_timer.start(3000)
        self._cursor_hide_timer.start(3000)

    def _hide_overlay(self) -> None:
        """コントロールオーバーレイを非表示にする（タイマーコールバック）。"""
        self.controls_panel.hide()

    def _hide_cursor(self) -> None:
        """US4: フルスクリーン中のみカーソルを非表示にする。
        F-503: オーバーレイモード中は controls_panel が表示されているときは非表示にしない。"""
        if self.isFullScreen():
            # オーバーレイモード中でコントロールが表示中はカーソルを隠さない
            if self._in_overlay_mode and not self.controls_panel.isHidden():
                return
            self.setCursor(Qt.CursorShape.BlankCursor)

    def mouseMoveEvent(self, event):
        """FR-016: フルスクリーン中のマウス追跡でメニューバーを自動表示。US4: カーソルを復元。F-503: overlay 表示。"""
        if self.isFullScreen():
            if event.pos().y() < 15:
                self.menuBar().show()
                self._menu_hide_timer.start(2000)
            # F-503: 画面下端10%でコントロールオーバーレイを表示
            if event.pos().y() > self.height() * 0.9:
                self._show_overlay()
            else:
                # US4: マウス移動でカーソル復元・タイマーリセット
                self.unsetCursor()
                self._cursor_hide_timer.start()
        super().mouseMoveEvent(event)

    # ── 動画エリア右クリックメニュー（022）────────────────────────────────

    def _show_video_context_menu(self, pos: QPoint) -> None:
        """動画エリアの右クリックコンテキストメニューを表示する（022）。"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        has_media = getattr(self, "_current_video_path", None) is not None

        play_pause_action = QAction(t("ctx.play_pause"), self)
        play_pause_action.setEnabled(has_media)
        play_pause_action.triggered.connect(self.toggle_play)
        menu.addAction(play_pause_action)

        stop_action = QAction(t("ctx.stop"), self)
        stop_action.setEnabled(has_media)
        stop_action.triggered.connect(self.stop)
        menu.addAction(stop_action)

        menu.addSeparator()

        set_a_action = QAction(t("ctx.set_a"), self)
        set_a_action.setEnabled(has_media)
        set_a_action.triggered.connect(self.set_point_a)
        menu.addAction(set_a_action)

        set_b_action = QAction(t("ctx.set_b"), self)
        set_b_action.setEnabled(has_media)
        set_b_action.triggered.connect(self.set_point_b)
        menu.addAction(set_b_action)

        add_bookmark_action = QAction(t("ctx.add_bookmark"), self)
        ab_both_set = (self.ab_point_a is not None and self.ab_point_b is not None)
        add_bookmark_action.setEnabled(ab_both_set)
        add_bookmark_action.triggered.connect(self._save_bookmark)
        menu.addAction(add_bookmark_action)

        menu.addSeparator()

        screenshot_action = QAction(t("ctx.screenshot"), self)
        screenshot_action.setEnabled(self._screenshot_action.isEnabled())
        screenshot_action.triggered.connect(self._take_screenshot)
        menu.addAction(screenshot_action)

        fullscreen_action = QAction(t("ctx.fullscreen"), self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        menu.addAction(fullscreen_action)

        menu.exec(self._video_ctx_overlay.mapToGlobal(pos))

    # ── 常に最前面操作 ────────────────────────────────────────

    def _toggle_mirror_display(self):
        """左右反転表示をトグルする（F-203）。再生中なら現在位置・速度・AB状態を保持してメディアを再生成する。"""
        new_val = not self._app_settings.mirror_display
        self._app_settings.mirror_display = new_val
        self.mirror_action.setChecked(new_val)
        if self._current_video_path is not None:
            pos = self.media_player.get_time()
            rate = self._playback_rate
            # _open_path 内の reset_ab() で AB 状態が消えるため事前に保存する
            saved_a = self.ab_point_a
            saved_b = self.ab_point_b
            saved_loop = self.ab_loop_active
            self._open_path(self._current_video_path)
            # VLC がデコードを開始するまで set_time/set_rate が無効なため遅延実行する
            def _restore():
                self.media_player.set_time(pos)
                self._set_playback_rate(rate)
                # AB 状態を復元
                self.ab_point_a = saved_a
                self.ab_point_b = saved_b
                self.ab_loop_active = saved_loop
                self.ab_toggle_btn.setChecked(saved_loop)
                self.ab_toggle_btn.setText(
                    t("btn.ab_loop_on") if saved_loop else t("btn.ab_loop_off")
                )
            QTimer.singleShot(300, _restore)

    # ── ブックマークサイドパネル操作（021） ───────────────────────────────

    def _clamp_panel_width(self, total: int) -> int:
        """保存済みパネル幅をウィンドウ幅に合わせてクランプして返す。"""
        w = min(self._app_settings.bookmark_panel_width, total - 320)
        return max(w, 240)

    def _apply_initial_panel_width(self) -> None:
        """起動時に AppSettings からパネル幅・表示状態を復元する（QTimer.singleShot 経由）。"""
        total = self._splitter.width()
        visible = self._app_settings.bookmark_panel_visible
        if not visible:
            self._panel_tabs.hide()
        else:
            w = self._clamp_panel_width(total)
            self._splitter.setSizes([total - w, w])
        self._bookmark_panel_action.setChecked(visible)

    def _toggle_bookmark_panel(self) -> None:
        """ブックマークパネルの表示・非表示を切り替える。"""
        visible = self._panel_tabs.isHidden()  # 隠れている → 表示に切り替える
        if visible:
            self._panel_tabs.show()
            total = self._splitter.width()
            w = self._clamp_panel_width(total)
            self._splitter.setSizes([total - w, w])
        else:
            sizes = self._splitter.sizes()
            if len(sizes) >= 2 and sizes[1] > 0:
                self._app_settings.bookmark_panel_width = sizes[1]
            self._panel_tabs.hide()
        self._app_settings.bookmark_panel_visible = visible
        self._bookmark_panel_action.setChecked(visible)

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
        pos_ms = self.media_player.get_time()
        if pos_ms < 0:
            return
        self.ab_point_a = pos_ms
        self._update_ab_info()
        self._update_save_btn_state()
        self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)  # US2

    def set_point_b(self):
        pos_ms = self.media_player.get_time()
        if pos_ms < 0:
            return
        self.ab_point_b = pos_ms
        self._update_ab_info()
        self._update_save_btn_state()
        self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)  # US2

    def toggle_ab_loop(self, checked):
        if checked and self.ab_point_a is not None and self.ab_point_b is not None:
            if self.ab_point_a >= self.ab_point_b:
                QMessageBox.warning(self, t("msg.ab_error.title"), t("msg.ab_error.body"))
                self.ab_toggle_btn.setChecked(False)
                return
        self.ab_loop_active = checked
        self.ab_toggle_btn.setChecked(checked)
        self.ab_toggle_btn.setText(t("btn.ab_loop_on") if checked else t("btn.ab_loop_off"))

    def reset_ab(self):
        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False
        self.ab_toggle_btn.setChecked(False)
        self.ab_toggle_btn.setText(t("btn.ab_loop_off"))
        self._update_ab_info()
        self._update_save_btn_state()
        self.seek_slider.set_ab_preview(None, None)  # US2
        # F-105: AB リセット時はズームも解除
        self._zoom_btn.setChecked(False)
        self.seek_slider.clear_zoom()

    def _on_ab_drag_finished(self, target: str, ms: int) -> None:
        """US3: AB 点マーカーのドラッグ完了時に呼ばれ、AB 点を更新する。"""
        if target == "a":
            self.ab_point_a = ms
        elif target == "b":
            self.ab_point_b = ms
        # A >= B になった場合はループを無効化（防御的ガード）
        if (
            self.ab_point_a is not None
            and self.ab_point_b is not None
            and self.ab_point_a >= self.ab_point_b
        ):
            self.ab_loop_active = False
        self._update_ab_info()
        self._update_save_btn_state()
        self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)

    def _update_ab_info(self):
        a_str = ms_to_str(self.ab_point_a) if self.ab_point_a is not None else "--"
        b_str = ms_to_str(self.ab_point_b) if self.ab_point_b is not None else "--"
        self.ab_info_label.setText(f"A: {a_str}  B: {b_str}")

    def _update_save_btn_state(self):
        """FR-001: A・B点が両方設定済み時のみ保存ボタンとズームボタンを有効化。"""
        enabled = self.ab_point_a is not None and self.ab_point_b is not None
        self.save_bookmark_btn.setEnabled(enabled)
        self._zoom_btn.setEnabled(enabled)
        if not enabled and self.seek_slider.zoom_enabled:
            # AB 点が消えた場合はズームも解除
            self._zoom_btn.setChecked(False)
            self.seek_slider.clear_zoom()
        elif enabled and self.seek_slider.zoom_enabled:
            # AB 点変化中でズームが有効なら範囲を自動更新
            self._apply_zoom_range()
        self._update_clip_export_action_state()

    def _toggle_zoom_mode(self, checked: bool | None = None) -> None:
        """F-105: ズームモードをトグルする。"""
        if checked is None:
            checked = self._zoom_btn.isChecked()
        if checked:
            self._apply_zoom_range()
        else:
            self.seek_slider.clear_zoom()

    def _apply_zoom_range(self) -> None:
        """F-105: AB 区間に ±10% パディングを加えてズーム範囲を設定する。"""
        if self.ab_point_a is None or self.ab_point_b is None:
            return
        ab_range = self.ab_point_b - self.ab_point_a
        padding = int(ab_range * 0.1)
        duration = self.media_player.get_length()
        start_ms = max(0, self.ab_point_a - padding)
        end_ms = self.ab_point_b + padding
        if duration > 0:
            end_ms = min(end_ms, duration)
        if end_ms <= start_ms:
            end_ms = start_ms + 1
        self.seek_slider.set_zoom(start_ms, end_ms)

    def _update_clip_export_action_state(self) -> None:
        """AB ループの状態に応じてクリップ書き出しアクションの有効/無効を更新する。"""
        enabled = (
            self.ab_point_a is not None
            and self.ab_point_b is not None
            and self.ab_point_a < self.ab_point_b
        )
        self._clip_export_action.setEnabled(enabled)

    # ── ブックマーク操作 ──────────────────────────────────────

    def _save_bookmark(self):
        """US3: 現在の AB 区間をブックマークとして保存する（名前入力ダイアログ付き）。"""
        if self.ab_point_a is None or self.ab_point_b is None:
            return
        # US3: 名前入力ダイアログを表示
        default_name = t("bookmark.default_name").format(
            time=f"{ms_to_str(self.ab_point_a)}-{ms_to_str(self.ab_point_b)}"
        )
        name, ok = QInputDialog.getText(
            self, t("bookmark.save_title"), t("bookmark.save_prompt"), text=default_name
        )
        if not ok:
            return
        bm = LoopBookmark(point_a_ms=self.ab_point_a, point_b_ms=self.ab_point_b, name=name.strip())
        video_length_ms = self.media_player.get_length()
        try:
            self.bookmark_panel.add_bookmark(bm, video_length_ms)
            self._sync_slider_bookmarks()
        except ValueError as e:
            QMessageBox.warning(self, t("msg.bookmark_error.title"), str(e))

    def _on_bookmark_selected(self, bookmark: LoopBookmark):
        """FR-003: ブックマーク選択時に AB ループを切り替える。"""
        self._seq_state = None
        self.bookmark_panel.stop_sequential()

        self.ab_point_a = bookmark.point_a_ms
        self.ab_point_b = bookmark.point_b_ms
        self.ab_loop_active = True
        self.ab_toggle_btn.setChecked(True)
        self.ab_toggle_btn.setText(t("btn.ab_loop_on"))
        self._update_ab_info()
        self._update_save_btn_state()
        self.media_player.set_time(bookmark.point_a_ms)
        if not self.media_player.is_playing():
            self.media_player.play()
            self.play_btn.setText(t("btn.pause"))
        self._sync_slider_bookmarks()

    # ── 連続再生操作 ──────────────────────────────────────────

    def _on_sequential_started(self, state: SequentialPlayState):
        """FR-006: 連続再生を開始する。"""
        self._seq_state = state
        # 通常 AB ループを無効化
        self.ab_loop_active = False
        self.ab_toggle_btn.setChecked(False)
        self.ab_toggle_btn.setText(t("btn.ab_loop_off"))
        # 最初の区間のA点から再生開始
        self.media_player.set_time(state.current_bookmark.point_a_ms)
        if not self.media_player.is_playing():
            self.media_player.play()
            self.play_btn.setText(t("btn.pause"))
        self._sync_slider_bookmarks()

    def _on_sequential_stopped(self):
        """連続再生を停止して通常再生モードに戻る。"""
        if self._seq_state:
            self._seq_state.stop()
        self._seq_state = None
        self._sync_slider_bookmarks()

    # ── US2: フレーム単位微調整 ──────────────────────────────────

    def _on_frame_adjusted(self, bm_id: str, point: str, new_ms: int) -> None:
        """US2: BookmarkRow の frame_adjusted シグナルを受けてストアを更新する。"""
        if self._current_video_path is None:
            return
        bms = self._store.get_bookmarks(self._current_video_path)
        bm = next((b for b in bms if b.id == bm_id), None)
        if bm is None:
            return
        # ポーズタイマーをクリア（フレーム調整時は中断）
        self._cancel_pause_timer()
        if point == "a":
            new_a, new_b = new_ms, bm.point_b_ms
        else:
            new_a, new_b = bm.point_a_ms, new_ms
        try:
            self._store.update_ab_points(self._current_video_path, bm_id, new_a, new_b)
        except ValueError:
            return
        self._sync_slider_bookmarks()

    def _cancel_pause_timer(self) -> None:
        """US4: ループ間ポーズタイマーをキャンセルしてクリアする。"""
        if self._pause_timer is not None:
            self._pause_timer.stop()
            self._pause_timer = None

    def _resume_after_pause(self, a_ms: int) -> None:
        """US4: ポーズ終了後に A 点にシークして再生を再開する。"""
        self._pause_timer = None
        self.media_player.set_time(a_ms)
        self.media_player.play()
        self.play_btn.setText(t("btn.pause"))

    def _on_pause_ms_changed(self, bm_id: str, pause_ms: int) -> None:
        """US4: pause_ms_changed シグナルを bookmark_panel 経由で受信（BookmarkPanel が永続化済み）。"""
        pass  # 永続化は BookmarkPanel._on_pause_ms_changed が担当

    def _on_play_count_reset(self, bm_id: str) -> None:
        """US6: 再生回数リセット。"""
        if self._current_video_path is None:
            return
        self._store.reset_play_count(self._current_video_path, bm_id)
        bms = self._store.get_bookmarks(self._current_video_path)
        bm = next((b for b in bms if b.id == bm_id), None)
        if bm:
            self.bookmark_panel.update_play_count(bm_id, 0)

    def _on_tags_changed(self, bm_id: str, tags: list[str]) -> None:
        """US9: tags_changed シグナルを bookmark_panel 経由で受信（BookmarkPanel が永続化済み）。"""
        pass  # 永続化は BookmarkPanel._on_tags_changed が担当

    def _on_seq_mode_toggled(self, one_round: bool) -> None:
        """US5: 連続再生モードトグル。"""
        if self._seq_state:
            self._seq_state.one_round_mode = one_round
        self.bookmark_panel.set_one_round_mode(one_round)
        self._app_settings.sequential_play_mode = "one_round" if one_round else "infinite"

    def _on_seek_to_ms(self, ms: int) -> None:
        """A点へジャンプ: 再生状態を変えずにシークする（022）。"""
        self.media_player.set_time(ms)

    def _stop_seq_play(self) -> None:
        """US5: 連続再生を停止する（on_b_reached が None を返したとき）。"""
        if self._seq_state:
            self._seq_state.stop()
        self._seq_state = None
        self.bookmark_panel.stop_sequential()
        self._sync_slider_bookmarks()

    # ── US8: プレイリスト UI ──────────────────────────────────────

    def _playlist_next(self) -> None:
        """US8: プレイリストの次ファイルへ移動する。"""
        if self._playlist and self._playlist.has_next():
            self._playlist.advance()
            self._open_path(str(self._playlist.current()))

    def _playlist_prev(self) -> None:
        """US8: プレイリストの前ファイルへ移動する。"""
        if self._playlist and self._playlist.index > 0:
            self._playlist.retreat()
            self._open_path(str(self._playlist.current()))

    def _update_playlist_panel(self) -> None:
        """US8: プレイリストパネルを更新し、プレイリストがある場合はタブを表示する。"""
        if hasattr(self, "playlist_panel") and hasattr(self, "_panel_tabs"):
            self.playlist_panel.set_playlist(self._playlist)
            has_playlist = self._playlist is not None and len(self._playlist) > 1
            self._panel_tabs.setTabVisible(self._playlist_tab_index, has_playlist)

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
            size_str = t("label.unknown")

        length_ms = self.media_player.get_length()
        length_str = ms_to_str(length_ms) if length_ms > 0 else t("label.unknown")

        # ── VLC トラック情報 ──
        resolution_str: str | None = None
        fps_str: str | None = None
        video_codec_str: str | None = None
        audio_codec_str: str | None = None

        media = self.media_player.get_media()
        if media is not None:
            # media.parse() は非推奨・UI スレッドをブロックするため使用しない。
            # 再生済みメディアのトラック情報は parse なしで取得できる。
            tracks = media.tracks_get()
            if tracks:
                for track in tracks:
                    # python-vlc 3.0.x では TrackType 属性名は小文字（.video / .audio）
                    if track.type == vlc.TrackType.video and resolution_str is None:
                        v = track.video.contents if track.video else None
                        if v:
                            if v.width and v.height:
                                resolution_str = f"{v.width} × {v.height}"
                            if v.frame_rate_num and v.frame_rate_den:
                                fps_val = v.frame_rate_num / v.frame_rate_den
                                fps_str = f"{fps_val:.2f}"
                        if track.codec:
                            desc = vlc.libvlc_media_get_codec_description(
                                vlc.TrackType.video, track.codec
                            )
                            if isinstance(desc, bytes):
                                desc = desc.decode("utf-8", errors="replace")
                            video_codec_str = desc if desc else None
                    elif track.type == vlc.TrackType.audio and audio_codec_str is None:
                        if track.codec:
                            desc = vlc.libvlc_media_get_codec_description(
                                vlc.TrackType.audio, track.codec
                            )
                            if isinstance(desc, bytes):
                                desc = desc.decode("utf-8", errors="replace")
                            audio_codec_str = desc if desc else None

        # ── ダイアログ構築 ──
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dialog.video_info.title"))
        dialog.setMinimumWidth(400)
        grid = QGridLayout(dialog)
        grid.setColumnMinimumWidth(0, 120)
        grid.setSpacing(6)

        unknown = t("label.unknown")
        rows = [
            (t("dialog.video_info.filename"),    filename),
            (t("dialog.video_info.filesize"),    size_str),
            (t("dialog.video_info.duration"),    length_str),
            (t("dialog.video_info.resolution"),  resolution_str or unknown),
            (t("dialog.video_info.framerate"),   fps_str or unknown),
            (t("dialog.video_info.video_codec"), video_codec_str or unknown),
            (t("dialog.video_info.audio_codec"), audio_codec_str or unknown),
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

    @staticmethod
    def _get_shortcuts() -> list:
        """ショートカット定義を返す（UI文字列は t() 経由で取得）。"""
        return [
            (t("shortcut.cat.playback"), [
                ("Space",     t("shortcut.play_pause")),
                ("←",        t("shortcut.seek_back5")),
                ("→",        t("shortcut.seek_fwd5")),
                ("Shift+←",  t("shortcut.seek_back1")),
                ("Shift+→",  t("shortcut.seek_fwd1")),
                ("Ctrl+←",   t("shortcut.seek_back10")),
                ("Ctrl+→",   t("shortcut.seek_fwd10")),
                (",",         t("shortcut.frame_back")),
                (".",         t("shortcut.frame_fwd")),
                ("[",         t("shortcut.speed_down")),
                ("]",         t("shortcut.speed_up")),
            ]),
            (t("shortcut.cat.volume"), [
                ("↑", t("shortcut.vol_up")),
                ("↓", t("shortcut.vol_down")),
                ("M", t("shortcut.mute")),
            ]),
            (t("shortcut.cat.ab_loop"), [
                ("I",                    t("shortcut.set_a")),
                ("O",                    t("shortcut.set_b")),
                (t("shortcut.set_a_btn"), t("shortcut.set_a_btn.desc")),
                (t("shortcut.set_b_btn"), t("shortcut.set_b_btn.desc")),
            ]),
            (t("shortcut.cat.bookmark"), [
                (t("shortcut.bookmark_save"), t("shortcut.bookmark_save.desc")),
                ("Ctrl+Z",                    t("shortcut.undo_delete")),
            ]),
            (t("shortcut.cat.view"), [
                ("F",      t("shortcut.fullscreen")),
                ("Escape", t("shortcut.fullscreen_exit")),
            ]),
            (t("shortcut.cat.file"), [
                ("Ctrl+O",       t("shortcut.open_file")),
                ("Ctrl+Shift+S", t("shortcut.screenshot")),
                ("Ctrl+Q",       t("shortcut.quit")),
                ("?",            t("shortcut.show_shortcuts")),
            ]),
        ]

    def _show_shortcut_dialog(self) -> None:
        """US4: ショートカット一覧ダイアログを表示する（FR-014）。"""
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dialog.shortcuts.title"))
        dialog.setMinimumWidth(420)

        outer = QVBoxLayout(dialog)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(4)
        grid.setColumnMinimumWidth(0, 160)
        grid.setColumnMinimumWidth(1, 200)

        row = 0
        for category, entries in self._get_shortcuts():
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

    # ── US4: 再生終了時の動作 ────────────────────────────────────

    def _handle_playback_ended(self):
        """US4: 再生終了時に設定に従って動作する。プレイリストがある場合は次へ進む。"""
        # プレイリスト有効 → 次のファイルへ（US7）
        if hasattr(self, "_playlist") and self._playlist and self._playlist.has_next():
            self._playlist.advance()
            self._open_path(str(self._playlist.current()))
            return
        # ABループ有効 → _on_timer が制御するため何もしない
        if self.ab_loop_active:
            return
        action = self._app_settings.end_of_playback_action
        if action == "rewind":
            self.media_player.stop()
            self.media_player.set_time(0)
            self.seek_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")
        elif action == "loop":
            self.media_player.stop()
            self.media_player.play()
        # "stop" は VLC が自動的に停止するため何もしない

    def closeEvent(self, event):
        """US5: アプリ終了時に現在の再生位置を保存する。F-403: ウィンドウジオメトリを保存する。021: パネル幅を保存する。"""
        self.timer.stop()
        # 021: パネルが表示中なら幅を保存する
        if self._panel_tabs.isVisible():
            sizes = self._splitter.sizes()
            if len(sizes) >= 2 and sizes[1] > 0:
                self._app_settings.bookmark_panel_width = sizes[1]
        if self._current_video_path:
            self._playback_position.save(
                self._current_video_path,
                self.media_player.get_time(),
                self.media_player.get_length(),
            )
        # F-403: フルスクリーン中はフルスクリーン前のジオメトリを保存する
        if self.isFullScreen() and self._pre_fullscreen_geometry is not None:
            geo = self._pre_fullscreen_geometry
        else:
            geo = self.geometry()
        self._app_settings.window_geometry = {
            "x": geo.x(), "y": geo.y(),
            "width": geo.width(), "height": geo.height(),
        }
        # VLC リソースを明示的に解放（GC タイミングによるクラッシュ防止）
        self.media_player.stop()
        self.media_player.release()
        self.instance.release()
        super().closeEvent(event)

    def _restore_window_geometry(self) -> None:
        """F-403: 保存済みウィンドウジオメトリを復元する。"""
        geo = self._app_settings.window_geometry
        if geo is None:
            return
        x, y = geo["x"], geo["y"]
        w = max(800, geo["width"])
        h = max(600, geo["height"])
        if QApplication.screenAt(QPoint(x, y)) is None:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - w) // 2
            y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _reset_window_geometry(self) -> None:
        """F-403: ウィンドウ位置をリセットして次回起動時にデフォルト位置で開く。"""
        self._app_settings.window_geometry = None

    # ── 自動更新 ──────────────────────────────────────────────

    def _start_update_check(self, silent: bool = False) -> None:
        """UpdateChecker を起動する。silent=True の場合、エラーを無視する。"""
        checker = UpdateChecker(settings=self._app_settings, parent=self)
        checker.update_available.connect(self._on_update_available)
        if silent:
            checker.up_to_date.connect(checker.deleteLater)
            checker.check_failed.connect(checker.deleteLater)  # サイレント（FR-007）
        else:
            checker.up_to_date.connect(self._on_up_to_date)
            checker.check_failed.connect(self._on_check_failed)
        checker.finished.connect(checker.deleteLater)
        checker.start()

    def _on_update_available(self, version: str, url: str) -> None:
        """新バージョンが利用可能な場合の通知ダイアログを表示する（FR-002/FR-003）。"""
        body = t("msg.update_available.body").format(current_ver=VERSION, ver=version)
        msg = QMessageBox(self)
        msg.setWindowTitle(t("msg.update_available.title"))
        msg.setText(body)
        download_btn = None
        if url:
            download_btn = msg.addButton(t("btn.download_now"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(t("btn.later"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if download_btn is not None and msg.clickedButton() == download_btn:
            dialog = DownloadDialog(url, version, parent=self)
            dialog.exec()

    def _check_for_updates_manually(self) -> None:
        """手動更新確認（ヘルプメニューから呼ばれる）。"""
        self._start_update_check(silent=False)

    def _on_up_to_date(self) -> None:
        """最新バージョン使用中の場合のダイアログを表示する（FR-009）。"""
        from looplayer.version import VERSION as _ver
        QMessageBox.information(
            self,
            t("msg.update_latest.title"),
            t("msg.update_latest.body").format(ver=_ver),
        )

    def _on_check_failed(self, error: str) -> None:
        """手動確認でのネットワークエラーダイアログを表示する（FR-007）。"""
        QMessageBox.warning(
            self,
            t("msg.update_check_failed.title"),
            f"{t('msg.update_check_failed.body')}\n\n{error}",
        )

    def _toggle_auto_check(self, checked: bool) -> None:
        """起動時チェックの ON/OFF を設定に保存する（FR-008）。"""
        self._app_settings.check_update_on_startup = checked

    # ── VLC エラーハンドリング ────────────────────────────────

    def _on_media_error(self, _event):
        """VLC エラーイベントのコールバック（VLC スレッドから呼ばれる）。"""
        self._error_occurred.emit()

    def _show_error_dialog(self):
        """UI スレッドでエラーダイアログを表示する。直前の再生状態は変更しない。"""
        QMessageBox.warning(self, t("msg.media_error.title"), t("msg.media_error.body"))


def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
