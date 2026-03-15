"""BookmarkRow: ブックマーク一覧の1行ウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSpinBox, QInputDialog,
)
from PyQt6.QtCore import QEvent, pyqtSignal

from looplayer.bookmark_store import LoopBookmark
from looplayer.utils import _ms_to_str


class BookmarkRow(QWidget):
    """ブックマーク一覧の1行ウィジェット。"""
    deleted = pyqtSignal(str)              # bookmark_id
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
