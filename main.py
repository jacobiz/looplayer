import os
import sys
import vlc
from dataclasses import dataclass, field
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QInputDialog, QSpinBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QTimer, QEvent, pyqtSignal
from PyQt6.QtGui import QMouseEvent

from bookmark_store import BookmarkStore, LoopBookmark


# ── SequentialPlayState ───────────────────────────────────────

@dataclass
class SequentialPlayState:
    """連続再生の進行状態を管理する。"""
    bookmarks: list
    current_index: int = 0
    active: bool = True
    remaining_repeats: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.bookmarks:
            raise ValueError("bookmarks は1件以上必要です")
        self.remaining_repeats = self.bookmarks[self.current_index].repeat_count

    @property
    def current_bookmark(self) -> LoopBookmark:
        return self.bookmarks[self.current_index]

    @property
    def next_bookmark_name(self) -> str:
        next_idx = (self.current_index + 1) % len(self.bookmarks)
        return self.bookmarks[next_idx].name

    def on_b_reached(self) -> int:
        """B点到達時に呼び出す。次に移動すべき A点タイムスタンプ（ms）を返す。"""
        self.remaining_repeats -= 1
        if self.remaining_repeats > 0:
            # 同じ区間を繰り返す
            return self.current_bookmark.point_a_ms

        # 次の区間へ（最後なら先頭へ）
        self.current_index = (self.current_index + 1) % len(self.bookmarks)
        self.remaining_repeats = self.current_bookmark.repeat_count
        return self.current_bookmark.point_a_ms

    def stop(self) -> None:
        self.active = False


# ── BookmarkRow ───────────────────────────────────────────────

class BookmarkRow(QWidget):
    """ブックマーク一覧の1行ウィジェット。"""
    deleted = pyqtSignal(str)          # bookmark_id
    repeat_changed = pyqtSignal(str, int)  # bookmark_id, count
    name_changed = pyqtSignal(str, str)    # bookmark_id, new_name

    def __init__(self, bookmark: LoopBookmark, parent=None):
        super().__init__(parent)
        self.bookmark_id = bookmark.id
        self._build(bookmark)

    def _build(self, bm: LoopBookmark) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self.name_label = QLabel(bm.name)
        self.name_label.setMinimumWidth(80)
        self.name_label.setToolTip("ダブルクリックで名前を編集")
        self.name_label.installEventFilter(self)

        time_label = QLabel(
            f"A:{_ms_to_str(bm.point_a_ms)}  B:{_ms_to_str(bm.point_b_ms)}"
        )
        time_label.setStyleSheet("color: #888; font-size: 11px;")

        repeat_label = QLabel("繰返:")
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setMinimum(1)
        self.repeat_spin.setMaximum(99)
        self.repeat_spin.setValue(bm.repeat_count)
        self.repeat_spin.setFixedWidth(55)
        self.repeat_spin.valueChanged.connect(
            lambda v: self.repeat_changed.emit(self.bookmark_id, v)
        )

        del_btn = QPushButton("×")
        del_btn.setFixedWidth(24)
        del_btn.setToolTip("削除")
        del_btn.clicked.connect(lambda: self.deleted.emit(self.bookmark_id))

        layout.addWidget(self.name_label)
        layout.addWidget(time_label)
        layout.addStretch()
        layout.addWidget(repeat_label)
        layout.addWidget(self.repeat_spin)
        layout.addWidget(del_btn)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """名前ラベルのダブルクリックを捕捉して編集ダイアログを開く（FR-004）。"""
        if obj is self.name_label and event.type() == QEvent.Type.MouseButtonDblClick:
            new_name, ok = QInputDialog.getText(
                self, "名前を編集", "ブックマーク名:", text=self.name_label.text()
            )
            if ok and new_name.strip():
                self.name_label.setText(new_name.strip())
                self.name_changed.emit(self.bookmark_id, new_name.strip())
            return True
        return super().eventFilter(obj, event)

    def set_name(self, name: str) -> None:
        self.name_label.setText(name)


# ── BookmarkPanel ─────────────────────────────────────────────

class BookmarkPanel(QWidget):
    """ブックマーク一覧パネル。"""
    bookmark_selected = pyqtSignal(object)   # LoopBookmark
    sequential_started = pyqtSignal(object)  # SequentialPlayState
    sequential_stopped = pyqtSignal()

    def __init__(self, store: BookmarkStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._video_path: str | None = None
        self._seq_active = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # ── ヘッダー行 ──
        header = QHBoxLayout()
        header.addWidget(QLabel("ブックマーク一覧"))
        header.addStretch()
        self.seq_btn = QPushButton("連続再生")
        self.seq_btn.setCheckable(True)
        self.seq_btn.setEnabled(False)
        self.seq_btn.clicked.connect(self._on_seq_btn)
        header.addWidget(self.seq_btn)
        layout.addLayout(header)

        # ── 連続再生ステータス ──
        self.seq_status_label = QLabel("")
        self.seq_status_label.setStyleSheet("color: #4a9; font-size: 11px;")
        self.seq_status_label.hide()
        layout.addWidget(self.seq_status_label)

        # ── リスト ──
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setMinimumHeight(120)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.list_widget)

    # ── 公開メソッド ────────────────────────────────────────

    def load_video(self, video_path: str) -> None:
        """動画ファイルが開かれたときに呼び出す（FR-008）。"""
        self._video_path = video_path
        self._seq_active = False
        self.seq_btn.setChecked(False)
        self.seq_status_label.hide()
        self._refresh_list()

    def add_bookmark(self, bookmark: LoopBookmark, video_length_ms: int = 0) -> None:
        """ブックマークをストアに追加してリストを更新する（FR-001）。"""
        if self._video_path is None:
            return
        self._store.add(self._video_path, bookmark, video_length_ms)
        self._refresh_list()

    def update_seq_status(self, state: SequentialPlayState) -> None:
        """連続再生中のステータスラベルを更新する（FR-007）。"""
        if not state.active:
            self.seq_status_label.hide()
            return
        cur = state.current_bookmark.name
        nxt = state.next_bookmark_name
        self.seq_status_label.setText(f"▶ 現在: {cur}  →  次: {nxt}")
        self.seq_status_label.show()

    # ── 内部処理 ────────────────────────────────────────────

    def _refresh_list(self) -> None:
        self.list_widget.clear()
        if self._video_path is None:
            return
        bms = self._store.get_bookmarks(self._video_path)
        for bm in bms:
            item = QListWidgetItem()
            row = BookmarkRow(bm)
            row.deleted.connect(self._on_delete)
            row.repeat_changed.connect(self._on_repeat_changed)
            row.name_changed.connect(self._on_name_changed)
            item.setSizeHint(row.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, bm.id)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
        self.seq_btn.setEnabled(len(bms) > 0)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        if self._video_path is None:
            return
        bookmark_id = item.data(Qt.ItemDataRole.UserRole)
        bms = self._store.get_bookmarks(self._video_path)
        for bm in bms:
            if bm.id == bookmark_id:
                self.bookmark_selected.emit(bm)
                break

    def _on_delete(self, bookmark_id: str) -> None:
        if self._video_path is None:
            return
        self._store.delete(self._video_path, bookmark_id)
        self._refresh_list()

    def _on_repeat_changed(self, bookmark_id: str, count: int) -> None:
        if self._video_path is None:
            return
        self._store.update_repeat_count(self._video_path, bookmark_id, count)

    def _on_name_changed(self, bookmark_id: str, new_name: str) -> None:
        if self._video_path is None:
            return
        self._store.update_name(self._video_path, bookmark_id, new_name)

    def _on_rows_moved(self, *_) -> None:
        """ドラッグ＆ドロップ後に並び順を永続化する（FR-009）。"""
        if self._video_path is None:
            return
        ordered_ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            ordered_ids.append(item.data(Qt.ItemDataRole.UserRole))
        self._store.update_order(self._video_path, ordered_ids)

    def stop_sequential(self) -> None:
        """連続再生を停止してUIをリセットする公開メソッド（FR-006）。"""
        self._seq_active = False
        self.seq_status_label.hide()
        self.seq_btn.setChecked(False)
        self.seq_btn.setText("連続再生")

    def _on_seq_btn(self, checked: bool) -> None:
        if not checked:
            self.stop_sequential()
            self.sequential_stopped.emit()
            return

        if self._video_path is None:
            self.seq_btn.setChecked(False)
            return
        bms = self._store.get_bookmarks(self._video_path)
        if not bms:
            self.seq_btn.setChecked(False)
            return

        self._seq_active = True
        self.seq_btn.setText("連続再生 停止")
        state = SequentialPlayState(bookmarks=bms)
        self.update_seq_status(state)
        self.sequential_started.emit(state)


# ── VideoPlayer ───────────────────────────────────────────────

class VideoPlayer(QMainWindow):
    # VLC イベントスレッドから UI スレッドへ安全に渡すためのシグナル
    _error_occurred = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setMinimumSize(800, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self._current_video_path: str | None = None

        # FR-015: ファイルが開けない場合のエラーイベント購読
        self._error_occurred.connect(self._show_error_dialog)
        em = self.media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)

        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False

        # 連続再生状態
        self._seq_state: SequentialPlayState | None = None

        # ブックマークストア
        self._store = BookmarkStore()

        self._build_ui()

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

        # Video frame
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        layout.addWidget(self.video_frame, stretch=1)

        # Seek bar
        seek_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.time_label)
        layout.addLayout(seek_layout)

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
        layout.addLayout(ctrl_layout)

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
        layout.addLayout(ab_layout)

        # ブックマーク保存ボタン（FR-001: A・B点設定済み時のみ有効）
        bookmark_save_layout = QHBoxLayout()
        self.save_bookmark_btn = QPushButton("ブックマーク保存")
        self.save_bookmark_btn.setEnabled(False)
        self.save_bookmark_btn.clicked.connect(self._save_bookmark)
        bookmark_save_layout.addWidget(self.save_bookmark_btn)
        bookmark_save_layout.addStretch()
        layout.addLayout(bookmark_save_layout)

        # ブックマークパネル
        self.bookmark_panel = BookmarkPanel(self._store)
        self.bookmark_panel.bookmark_selected.connect(self._on_bookmark_selected)
        self.bookmark_panel.sequential_started.connect(self._on_sequential_started)
        self.bookmark_panel.sequential_stopped.connect(self._on_sequential_stopped)
        layout.addWidget(self.bookmark_panel)

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

        self._current_video_path = path
        media = self.instance.media_new(path)
        self.media_player.set_media(media)

        win_id = int(self.video_frame.winId())
        if sys.platform == "win32":
            self.media_player.set_hwnd(win_id)
        else:
            self.media_player.set_xwindow(win_id)

        self.media_player.play()
        self.play_btn.setText("一時停止")
        self.setWindowTitle(f"Video Player - {os.path.basename(path)}")
        self.reset_ab()

        # FR-008: 動画に紐づくブックマークを自動ロード
        self.bookmark_panel.load_video(path)

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

    def _on_seek(self, value):
        if self.media_player.get_length() > 0:
            self.media_player.set_position(value / 1000.0)

    def _on_timer(self):
        length_ms = self.media_player.get_length()
        pos = self.media_player.get_position()

        if length_ms > 0 and not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(int(pos * 1000))
            self.time_label.setText(
                f"{_ms_to_str(int(pos * length_ms))} / {_ms_to_str(length_ms)}"
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
            return

        # 通常 AB ループチェック
        if self.ab_loop_active and self.ab_point_a is not None and self.ab_point_b is not None:
            current_ms = int(pos * length_ms) if length_ms > 0 else 0
            if current_ms >= self.ab_point_b:
                self.media_player.set_time(self.ab_point_a)

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
        a_str = _ms_to_str(self.ab_point_a) if self.ab_point_a is not None else "--"
        b_str = _ms_to_str(self.ab_point_b) if self.ab_point_b is not None else "--"
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

    def _on_sequential_stopped(self):
        """連続再生を停止して通常再生モードに戻る。"""
        if self._seq_state:
            self._seq_state.stop()
        self._seq_state = None

    # ── VLC エラーハンドリング ────────────────────────────────

    def _on_media_error(self, _event):
        """VLC エラーイベントのコールバック（VLC スレッドから呼ばれる）。"""
        self._error_occurred.emit()

    def _show_error_dialog(self):
        """UI スレッドでエラーダイアログを表示する。直前の再生状態は変更しない。"""
        QMessageBox.warning(self, "エラー", "動画ファイルを開けませんでした。")


# ── ユーティリティ ────────────────────────────────────────────

def _ms_to_str(ms):
    if ms is None or ms < 0:
        return "00:00"
    s = ms // 1000
    minutes, seconds = divmod(s, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
