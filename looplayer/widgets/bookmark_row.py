"""BookmarkRow: ブックマーク一覧の1行ウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSpinBox, QInputDialog, QCheckBox,
    QMenu,
)
from PyQt6.QtCore import QEvent, Qt, pyqtSignal

from looplayer.bookmark_store import LoopBookmark
from looplayer.i18n import t
from looplayer.utils import ms_to_str


class BookmarkRow(QWidget):
    """ブックマーク一覧の1行ウィジェット。"""
    deleted = pyqtSignal(str)              # bookmark_id
    repeat_changed = pyqtSignal(str, int)  # bookmark_id, count
    name_changed = pyqtSignal(str, str)    # bookmark_id, new_name
    enabled_changed = pyqtSignal(str, bool)  # bookmark_id, enabled（FR-006）
    memo_clicked = pyqtSignal(str)         # bookmark_id（US6）
    export_requested = pyqtSignal(int, int, str)  # a_ms, b_ms, label（011）

    def __init__(self, bookmark: LoopBookmark, parent=None):
        super().__init__(parent)
        self.bookmark_id = bookmark.id
        self._notes = bookmark.notes
        self._point_a_ms = bookmark.point_a_ms
        self._point_b_ms = bookmark.point_b_ms
        self._name = bookmark.name
        self._build(bookmark)

    def _build(self, bm: LoopBookmark) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        # FR-006: 連続再生対象チェックボックス（デフォルト: enabled の値）
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

        time_label = QLabel(
            f"A:{ms_to_str(bm.point_a_ms)}  B:{ms_to_str(bm.point_b_ms)}"
        )
        time_label.setStyleSheet("color: #888; font-size: 11px;")

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
        layout.addWidget(time_label)
        layout.addStretch()
        layout.addWidget(repeat_label)
        layout.addWidget(self.repeat_spin)
        layout.addWidget(self.memo_btn)
        layout.addWidget(del_btn)

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
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction(self._export_clip_action)
        menu.exec(self.mapToGlobal(pos))

    def _on_export_clip(self) -> None:
        self.export_requested.emit(self._point_a_ms, self._point_b_ms, self._name)

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
