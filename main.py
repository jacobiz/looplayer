import os
import sys
import vlc
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox, QStyle
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon


class VideoPlayer(QMainWindow):
    # VLC イベントスレッドから UI スレッドへ安全に渡すためのシグナル
    _error_occurred = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setMinimumSize(800, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # FR-015: ファイルが開けない場合のエラーイベント購読
        self._error_occurred.connect(self._show_error_dialog)
        em = self.media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)

        self.ab_point_a = None
        self.ab_point_b = None
        self.ab_loop_active = False

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

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "動画ファイルを開く",
            "",
            "動画ファイル (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;すべてのファイル (*)"
        )
        if not path:
            return

        media = self.instance.media_new(path)
        self.media_player.set_media(media)

        # Attach video output to our widget
        win_id = int(self.video_frame.winId())
        if sys.platform == "win32":
            self.media_player.set_hwnd(win_id)
        else:
            self.media_player.set_xwindow(win_id)

        self.media_player.play()
        self.play_btn.setText("一時停止")
        self.setWindowTitle(f"Video Player - {os.path.basename(path)}")
        self.reset_ab()

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

        # AB loop check
        if self.ab_loop_active and self.ab_point_a is not None and self.ab_point_b is not None:
            current_ms = int(pos * length_ms) if length_ms > 0 else 0
            if current_ms >= self.ab_point_b:
                self.media_player.set_time(self.ab_point_a)

    def set_point_a(self):
        t = self.media_player.get_time()
        if t < 0:
            return
        self.ab_point_a = t
        self._update_ab_info()

    def set_point_b(self):
        t = self.media_player.get_time()
        if t < 0:
            return
        self.ab_point_b = t
        self._update_ab_info()

    def toggle_ab_loop(self, checked):
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

    def _on_media_error(self, _event):
        """VLC エラーイベントのコールバック（VLC スレッドから呼ばれる）。"""
        self._error_occurred.emit()

    def _show_error_dialog(self):
        """UI スレッドでエラーダイアログを表示する。直前の再生状態は変更しない。"""
        QMessageBox.warning(self, "エラー", "動画ファイルを開けませんでした。")

    def _update_ab_info(self):
        a_str = _ms_to_str(self.ab_point_a) if self.ab_point_a is not None else "--"
        b_str = _ms_to_str(self.ab_point_b) if self.ab_point_b is not None else "--"
        self.ab_info_label.setText(f"A: {a_str}  B: {b_str}")


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
