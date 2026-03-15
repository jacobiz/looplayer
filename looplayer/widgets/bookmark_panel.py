"""BookmarkPanel: ブックマーク一覧パネルウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.sequential import SequentialPlayState
from looplayer.widgets.bookmark_row import BookmarkRow


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

    def stop_sequential(self) -> None:
        """連続再生を停止してUIをリセットする公開メソッド（FR-006）。"""
        self._seq_active = False
        self.seq_status_label.hide()
        self.seq_btn.setChecked(False)
        self.seq_btn.setText("連続再生")

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
