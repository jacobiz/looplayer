"""BookmarkPanel: ブックマーク一覧パネルウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t
from looplayer.sequential import SequentialPlayState
from looplayer.widgets.bookmark_row import BookmarkRow


class BookmarkPanel(QWidget):
    """ブックマーク一覧パネル。"""
    bookmark_selected = pyqtSignal(object)       # LoopBookmark
    sequential_started = pyqtSignal(object)      # SequentialPlayState
    sequential_stopped = pyqtSignal()
    export_requested = pyqtSignal(int, int, str) # a_ms, b_ms, label

    def __init__(self, store: BookmarkStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._video_path: str | None = None
        self._seq_active = False

        # US5: 削除 Undo 用の保留状態
        self._pending_delete: dict | None = None
        self._undo_timer = QTimer(self)
        self._undo_timer.setSingleShot(True)
        self._undo_timer.setInterval(5000)
        self._undo_timer.timeout.connect(self._commit_delete)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # ── ヘッダー行 ──
        header = QHBoxLayout()
        header.addWidget(QLabel(t("bookmark.panel.title")))
        header.addStretch()
        self.seq_btn = QPushButton(t("bookmark.panel.seq_play"))
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
        """動画ファイルが開かれたときに呼び出す（FR-008）。US5: 保留削除を確定する。"""
        self._commit_delete()
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
        self.seq_status_label.setText(t("bookmark.panel.seq_status").format(cur=cur, nxt=nxt))
        self.seq_status_label.show()

    def stop_sequential(self) -> None:
        """連続再生を停止してUIをリセットする公開メソッド（FR-006）。"""
        self._seq_active = False
        self.seq_status_label.hide()
        self.seq_btn.setChecked(False)
        self.seq_btn.setText(t("bookmark.panel.seq_play"))

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
            row.enabled_changed.connect(self._on_enabled_changed)  # FR-006
            row.memo_clicked.connect(self._on_memo_clicked)  # US6
            row.export_requested.connect(self.export_requested)  # 011
            item.setSizeHint(row.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, bm.id)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
        # FR-008: チェック済みが1件以上ある場合のみ連続再生ボタンを有効化
        self.seq_btn.setEnabled(any(bm.enabled for bm in bms))

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
        """US5: 即時削除せず _pending_delete に保留し、5秒後に確定する。"""
        if self._video_path is None:
            return
        # 前の保留があればコミット
        if self._pending_delete is not None:
            self._commit_delete()
        # 削除対象を取得してから Store から削除（削除前の全順序を保存）
        bms = self._store.get_bookmarks(self._video_path)
        bm = next((b for b in bms if b.id == bookmark_id), None)
        if bm is None:
            return
        # 削除前の ID 順序スナップショットを保存（Undo 時に完全復元するため）
        order_snapshot = [b.id for b in bms]
        self._pending_delete = {"bookmark": bm, "order_snapshot": order_snapshot}
        self._store.delete(self._video_path, bookmark_id)
        self._undo_timer.start()
        self._refresh_list()

    def _commit_delete(self) -> None:
        """US5: 保留中の削除を確定する（タイマー発火時・次の削除・動画切替時）。"""
        self._undo_timer.stop()
        self._pending_delete = None

    def _undo_delete(self) -> None:
        """US5: 保留中の削除を取り消して元の順序で完全復元する。"""
        if self._pending_delete is None:
            return
        bm = self._pending_delete["bookmark"]
        order_snapshot = self._pending_delete["order_snapshot"]
        self._undo_timer.stop()
        self._pending_delete = None
        if self._video_path is None:
            return
        self._store.add(self._video_path, bm)
        # 削除前の ID 順序スナップショットで完全復元（再採番問題を回避）
        self._store.update_order(self._video_path, order_snapshot)
        self._refresh_list()

    def undo_delete(self) -> None:
        """US5: _undo_delete の公開インターフェース（player.py から呼ぶ用）。"""
        self._undo_delete()

    def _on_enabled_changed(self, bookmark_id: str, enabled: bool) -> None:
        """FR-006/FR-009: チェックボックス変更時に enabled を永続化し、seq_btn の有効状態を更新する。"""
        if self._video_path is None:
            return
        self._store.update_enabled(self._video_path, bookmark_id, enabled)
        bms = self._store.get_bookmarks(self._video_path)
        self.seq_btn.setEnabled(any(bm.enabled for bm in bms))

    def _on_repeat_changed(self, bookmark_id: str, count: int) -> None:
        if self._video_path is None:
            return
        self._store.update_repeat_count(self._video_path, bookmark_id, count)

    def _on_name_changed(self, bookmark_id: str, new_name: str) -> None:
        if self._video_path is None:
            return
        self._store.update_name(self._video_path, bookmark_id, new_name)

    def _on_memo_clicked(self, bookmark_id: str) -> None:
        """US6: メモボタンクリック時にメモ入力ダイアログを表示して保存する。"""
        if self._video_path is None:
            return
        bms = self._store.get_bookmarks(self._video_path)
        bm = next((b for b in bms if b.id == bookmark_id), None)
        if bm is None:
            return
        text, ok = QInputDialog.getMultiLineText(
            self, t("bookmark.memo.title"), t("bookmark.memo.prompt").format(name=bm.name), bm.notes
        )
        if ok:
            self._store.update_notes(self._video_path, bookmark_id, text)
            # リスト内の対応する BookmarkRow のスタイルを更新
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == bookmark_id:
                    row = self.list_widget.itemWidget(item)
                    if hasattr(row, "update_notes"):
                        row.update_notes(text)
                    break

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

        # FR-006: チェック済みのブックマークのみを連続再生対象とする
        enabled_bms = [bm for bm in bms if bm.enabled]
        if not enabled_bms:
            self.seq_btn.setChecked(False)
            return

        self._seq_active = True
        self.seq_btn.setText(t("bookmark.panel.seq_stop"))
        state = SequentialPlayState(bookmarks=enabled_bms)
        self.update_seq_status(state)
        self.sequential_started.emit(state)
