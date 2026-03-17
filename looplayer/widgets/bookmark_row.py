"""BookmarkRow: ブックマーク一覧の1行ウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpinBox,
    QDoubleSpinBox, QInputDialog, QCheckBox, QMenu,
)
from PyQt6.QtCore import QEvent, Qt, pyqtSignal

from looplayer.bookmark_store import LoopBookmark
from looplayer.i18n import t
from looplayer.utils import ms_to_str

_DEFAULT_FPS = 25.0


class BookmarkRow(QWidget):
    """ブックマーク一覧の1行ウィジェット。"""
    deleted = pyqtSignal(str)              # bookmark_id
    repeat_changed = pyqtSignal(str, int)  # bookmark_id, count
    name_changed = pyqtSignal(str, str)    # bookmark_id, new_name
    enabled_changed = pyqtSignal(str, bool)  # bookmark_id, enabled（FR-006）
    memo_clicked = pyqtSignal(str)         # bookmark_id（US6）
    export_requested = pyqtSignal(int, int, str)  # a_ms, b_ms, label（011）
    frame_adjusted = pyqtSignal(str, str, int)   # bookmark_id, "a"|"b", new_ms（US2）
    pause_ms_changed = pyqtSignal(str, int)      # bookmark_id, pause_ms（US4）
    play_count_reset = pyqtSignal(str)           # bookmark_id（US6）
    tags_changed = pyqtSignal(str, list)         # bookmark_id, tags（US9）

    def __init__(self, bookmark: LoopBookmark, fps: float = _DEFAULT_FPS, parent=None):
        super().__init__(parent)
        self.bookmark_id = bookmark.id
        self._notes = bookmark.notes
        self._point_a_ms = bookmark.point_a_ms
        self._point_b_ms = bookmark.point_b_ms
        self._name = bookmark.name
        self._fps = fps if fps > 0 else _DEFAULT_FPS
        self._play_count = bookmark.play_count
        self._tags = list(bookmark.tags)
        self._build(bookmark)

    def _build(self, bm: LoopBookmark) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(2)

        # ── 1行目: 主要情報 ──
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # FR-006: 連続再生対象チェックボックス
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(bm.enabled)
        self.enabled_checkbox.setToolTip(t("bookmark.row.enabled_tip"))
        self.enabled_checkbox.stateChanged.connect(
            lambda _: self.enabled_changed.emit(self.bookmark_id, self.enabled_checkbox.isChecked())
        )
        layout.addWidget(self.enabled_checkbox)

        self.name_label = QLabel(bm.name)
        self.name_label.setMinimumWidth(80)
        self.name_label.setToolTip(t("bookmark.row.name_tip"))
        self.name_label.installEventFilter(self)

        self.time_label = QLabel(
            f"A:{ms_to_str(bm.point_a_ms)}  B:{ms_to_str(bm.point_b_ms)}"
        )
        self.time_label.setStyleSheet("color: #888; font-size: 11px;")

        repeat_label = QLabel(t("bookmark.row.repeat"))
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
        del_btn.setToolTip(t("bookmark.row.delete_tip"))
        del_btn.clicked.connect(lambda: self.deleted.emit(self.bookmark_id))

        # US6: メモボタン
        self.memo_btn = QPushButton("✎")
        self.memo_btn.setFixedSize(24, 24)
        self._refresh_memo_style(bm.notes)
        self.memo_btn.clicked.connect(lambda: self.memo_clicked.emit(self.bookmark_id))

        layout.addWidget(self.name_label)
        layout.addWidget(self.time_label)
        layout.addStretch()
        layout.addWidget(repeat_label)
        layout.addWidget(self.repeat_spin)
        layout.addWidget(self.memo_btn)
        layout.addWidget(del_btn)
        outer.addLayout(layout)

        # ── 2行目: フレーム微調整 / ポーズ / 再生回数 / タグ ──
        row2 = QHBoxLayout()
        row2.setContentsMargins(20, 0, 0, 0)

        # US2: A点 フレーム微調整ボタン
        a_minus_btn = QPushButton(t("btn.frame_minus"))
        a_minus_btn.setFixedWidth(36)
        a_minus_btn.setToolTip("A点 -1フレーム")
        a_minus_btn.clicked.connect(lambda: self._adjust_frame("a", -1))
        a_plus_btn = QPushButton(t("btn.frame_plus"))
        a_plus_btn.setFixedWidth(36)
        a_plus_btn.setToolTip("A点 +1フレーム")
        a_plus_btn.clicked.connect(lambda: self._adjust_frame("a", +1))

        row2.addWidget(QLabel("A:"))
        row2.addWidget(a_minus_btn)
        row2.addWidget(a_plus_btn)

        # US2: B点 フレーム微調整ボタン
        b_minus_btn = QPushButton(t("btn.frame_minus"))
        b_minus_btn.setFixedWidth(36)
        b_minus_btn.setToolTip("B点 -1フレーム")
        b_minus_btn.clicked.connect(lambda: self._adjust_frame("b", -1))
        b_plus_btn = QPushButton(t("btn.frame_plus"))
        b_plus_btn.setFixedWidth(36)
        b_plus_btn.setToolTip("B点 +1フレーム")
        b_plus_btn.clicked.connect(lambda: self._adjust_frame("b", +1))

        row2.addWidget(QLabel("B:"))
        row2.addWidget(b_minus_btn)
        row2.addWidget(b_plus_btn)

        # US4: ポーズ間隔スピンボックス
        row2.addWidget(QLabel(t("label.pause_interval")))
        self.pause_spin = QDoubleSpinBox()
        self.pause_spin.setRange(0.0, 10.0)
        self.pause_spin.setSingleStep(0.5)
        self.pause_spin.setDecimals(1)
        self.pause_spin.setValue(bm.pause_ms / 1000.0)
        self.pause_spin.setFixedWidth(64)
        self.pause_spin.valueChanged.connect(
            lambda v: self.pause_ms_changed.emit(self.bookmark_id, int(v * 1000))
        )
        row2.addWidget(self.pause_spin)

        # US6: 再生回数表示
        self.play_count_label = QLabel(self._play_count_text(bm.play_count))
        self.play_count_label.setStyleSheet("color: #888; font-size: 11px;")
        row2.addWidget(self.play_count_label)

        # US9: タグ表示 + 編集ボタン
        self.tags_label = QLabel(self._tags_text(bm.tags))
        self.tags_label.setStyleSheet("color: #4a9; font-size: 11px;")
        row2.addWidget(self.tags_label)

        tags_btn = QPushButton(t("btn.edit_tags"))
        tags_btn.setFixedSize(28, 24)
        tags_btn.setToolTip(t("label.tags"))
        tags_btn.clicked.connect(self._on_edit_tags)
        row2.addWidget(tags_btn)

        row2.addStretch()
        outer.addLayout(row2)

        # 011: コンテキストメニュー用の書き出しアクション
        can_export = (
            bm.point_a_ms is not None
            and bm.point_b_ms is not None
            and bm.point_a_ms < bm.point_b_ms
        )
        from PyQt6.QtGui import QAction
        self._export_clip_action = QAction(t("bookmark.row.export_clip"), self)
        self._export_clip_action.setEnabled(can_export)
        self._export_clip_action.triggered.connect(self._on_export_clip)
        # US6: 再生回数リセット
        self._reset_play_count_action = QAction(t("btn.reset_play_count"), self)
        self._reset_play_count_action.triggered.connect(
            lambda: self.play_count_reset.emit(self.bookmark_id)
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction(self._export_clip_action)
        menu.addAction(self._reset_play_count_action)
        menu.exec(self.mapToGlobal(pos))

    def _on_export_clip(self) -> None:
        self.export_requested.emit(self._point_a_ms, self._point_b_ms, self._name)

    def _adjust_frame(self, point: str, direction: int) -> None:
        """US2: フレーム単位で A点 or B点を調整する。"""
        frame_ms = int(1000 / self._fps)
        if point == "a":
            new_ms = self._point_a_ms + direction * frame_ms
            if new_ms >= self._point_b_ms or new_ms < 0:
                return
            self._point_a_ms = new_ms
            self.time_label.setText(f"A:{ms_to_str(self._point_a_ms)}  B:{ms_to_str(self._point_b_ms)}")
            self.frame_adjusted.emit(self.bookmark_id, "a", new_ms)
        else:  # point == "b"
            new_ms = self._point_b_ms + direction * frame_ms
            if new_ms <= self._point_a_ms:
                return
            self._point_b_ms = new_ms
            self.time_label.setText(f"A:{ms_to_str(self._point_a_ms)}  B:{ms_to_str(self._point_b_ms)}")
            self.frame_adjusted.emit(self.bookmark_id, "b", new_ms)

    def _on_edit_tags(self) -> None:
        """US9: タグ編集ダイアログを開く。"""
        current_text = ", ".join(self._tags)
        text, ok = QInputDialog.getText(
            self, t("tag.edit_title"), t("tag.edit_prompt"), text=current_text
        )
        if ok:
            raw = [s.strip() for s in text.split(",") if s.strip()]
            self._tags = raw
            self.tags_label.setText(self._tags_text(raw))
            self.tags_changed.emit(self.bookmark_id, raw)

    @staticmethod
    def _play_count_text(count: int) -> str:
        if count == 0:
            return ""
        return f"×{count}"

    @staticmethod
    def _tags_text(tags: list[str]) -> str:
        if not tags:
            return ""
        return " ".join(f"#{t}" for t in tags)

    def update_play_count(self, count: int) -> None:
        """US6: 再生回数表示を更新する。"""
        self._play_count = count
        self.play_count_label.setText(self._play_count_text(count))

    def set_fps(self, fps: float) -> None:
        """US2: fps を更新する（動画読み込み後に呼ぶ）。"""
        self._fps = fps if fps > 0 else _DEFAULT_FPS

    def eventFilter(self, obj, event: QEvent) -> bool:
        """名前ラベルのダブルクリックを捕捉して編集ダイアログを開く（FR-004）。"""
        if obj is self.name_label and event.type() == QEvent.Type.MouseButtonDblClick:
            new_name, ok = QInputDialog.getText(
                self, t("bookmark.name.edit_title"), t("bookmark.name.edit_prompt"), text=self.name_label.text()
            )
            if ok and new_name.strip():
                self.name_label.setText(new_name.strip())
                self.name_changed.emit(self.bookmark_id, new_name.strip())
            return True
        return super().eventFilter(obj, event)

    def _refresh_memo_style(self, notes: str) -> None:
        """メモの有無に応じてボタンのスタイルとツールチップを更新する。"""
        if notes:
            self.memo_btn.setToolTip(t("bookmark.row.memo_tip_content").format(notes=notes))
            self.memo_btn.setStyleSheet("font-weight: bold;")
        else:
            self.memo_btn.setToolTip(t("bookmark.row.memo_tip"))
            self.memo_btn.setStyleSheet("")

    def update_notes(self, notes: str) -> None:
        """メモを更新してボタンスタイルに反映する。"""
        self._notes = notes
        self._refresh_memo_style(notes)

    def set_name(self, name: str) -> None:
        self.name_label.setText(name)
