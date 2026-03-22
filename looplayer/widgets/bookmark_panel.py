"""BookmarkPanel: ブックマーク一覧パネルウィジェット。"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog, QMenu,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.i18n import t
from looplayer.sequential import SequentialPlayState
from looplayer.widgets.bookmark_row import BookmarkRow


class BookmarkPanel(QWidget):
    """ブックマーク一覧パネル。"""
    bookmark_selected = pyqtSignal(object)          # LoopBookmark
    sequential_started = pyqtSignal(object)         # SequentialPlayState
    sequential_stopped = pyqtSignal()
    export_requested = pyqtSignal(int, int, str)    # a_ms, b_ms, label
    frame_adjusted = pyqtSignal(str, str, int)      # bm_id, point, new_ms（US2）
    pause_ms_changed = pyqtSignal(str, int)         # bm_id, pause_ms（US4）
    play_count_reset = pyqtSignal(str)              # bm_id（US6）
    tags_changed = pyqtSignal(str, list)            # bm_id, tags（US9）
    seq_mode_toggled = pyqtSignal(bool)             # one_round（US5）
    seek_to_ms_requested = pyqtSignal(int)          # ms（022）
    import_requested = pyqtSignal()                 # パネル空白エリアからのインポート要求（022）
    export_from_panel_requested = pyqtSignal()      # パネル空白エリアからのエクスポート要求（022）

    def __init__(self, store: BookmarkStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._video_path: str | None = None
        self._seq_active = False
        self._fps: float = 25.0  # US2: フレーム微調整に使用
        self._one_round_mode: bool = False  # US5: 1周停止モード
        self._active_tag_filter: list[str] = []  # US9: タグフィルタ

        # US5: 削除 Undo 用の保留状態
        self._pending_delete: dict | None = None
        # F-202: 一括生成 Undo 用の最終追加リスト
        self._last_bulk_add: list[LoopBookmark] = []
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
        # US5: 1周停止 / 無限ループ トグルボタン
        self.one_round_btn = QToolButton()
        self.one_round_btn.setText(t("seq.infinite"))
        self.one_round_btn.setCheckable(True)
        self.one_round_btn.setChecked(False)
        self.one_round_btn.clicked.connect(self._on_one_round_toggled)
        header.addWidget(self.one_round_btn)
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
        # 022: 空白エリアの右クリックメニュー
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_panel_context_menu)
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
        all_bms = self._store.get_bookmarks(self._video_path)
        # US9: タグフィルタ（OR ロジック）
        if self._active_tag_filter:
            bms = [bm for bm in all_bms if any(tag in bm.tags for tag in self._active_tag_filter)]
        else:
            bms = all_bms
        for bm in bms:
            item = QListWidgetItem()
            row = BookmarkRow(bm, fps=self._fps)
            row.deleted.connect(self._on_delete)
            row.repeat_changed.connect(self._on_repeat_changed)
            row.name_changed.connect(self._on_name_changed)
            row.enabled_changed.connect(self._on_enabled_changed)  # FR-006
            row.memo_clicked.connect(self._on_memo_clicked)  # US6
            row.export_requested.connect(self.export_requested)  # 011
            row.frame_adjusted.connect(self.frame_adjusted)  # US2
            row.pause_ms_changed.connect(self._on_pause_ms_changed)  # US4
            row.play_count_reset.connect(self.play_count_reset)  # US6
            row.tags_changed.connect(self._on_tags_changed)  # US9
            row.jump_to_a_requested.connect(self._on_jump_to_a)  # 022
            row.duplicate_requested.connect(self._on_duplicate)  # 022
            item.setSizeHint(row.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, bm.id)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
        # FR-008: チェック済みが1件以上ある場合のみ連続再生ボタンを有効化
        self.seq_btn.setEnabled(any(bm.enabled for bm in all_bms))

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
        # dataclasses.replace でコピーを渡し、add() による order/name の副作用が
        # スナップショットオブジェクトに波及しないようにする。
        from dataclasses import replace as _dc_replace
        self._store.add(self._video_path, _dc_replace(bm))
        # 削除前の ID 順序スナップショットで完全復元（再採番問題を回避）
        self._store.update_order(self._video_path, order_snapshot)
        self._refresh_list()

    def undo_delete(self) -> None:
        """US5: _undo_delete の公開インターフェース（player.py から呼ぶ用）。"""
        self._undo_delete()

    # ── F-202: 字幕からの一括生成 Undo ──────────────────────

    def set_last_bulk_add(self, bookmarks: list[LoopBookmark]) -> None:
        """一括生成されたブックマークを Undo 用に記録する（FR-008）。"""
        self._last_bulk_add = list(bookmarks)

    def undo_bulk_add(self) -> None:
        """一括生成されたブックマークを全件削除する（FR-008）。

        player.py の Ctrl+Z ハンドラから呼ぶ用。
        _pending_delete（削除 Undo）が有効な場合は先にコミットして競合を防ぐ。
        """
        if not self._last_bulk_add or self._video_path is None:
            return
        # 削除 Undo 待機中の場合は先にコミットして状態を一貫させる
        if self._pending_delete is not None:
            self._commit_delete()
        for bm in self._last_bulk_add:
            self._store.delete(self._video_path, bm.id)
        self._last_bulk_add = []
        self._refresh_list()

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
        state = SequentialPlayState(bookmarks=enabled_bms, one_round_mode=self._one_round_mode)
        self.update_seq_status(state)
        self.sequential_started.emit(state)

    # ── US5: 連続再生モードトグル ──────────────────────────────────

    def _on_one_round_toggled(self, checked: bool) -> None:
        self._one_round_mode = checked
        self.one_round_btn.setText(t("seq.one_round") if checked else t("seq.infinite"))
        self.seq_mode_toggled.emit(checked)

    # ── US4: ポーズ間隔 ──────────────────────────────────────────

    def _on_pause_ms_changed(self, bookmark_id: str, pause_ms: int) -> None:
        if self._video_path is None:
            return
        self._store.update_pause_ms(self._video_path, bookmark_id, pause_ms)

    # ── US5: 連続再生モードトグル ──────────────────────────────────

    def set_one_round_mode(self, one_round: bool) -> None:
        """US5: 1周停止モードを設定する（player.py から呼ぶ）。"""
        self._one_round_mode = one_round

    # ── US6: 練習カウンター更新 ────────────────────────────────────

    def update_play_count(self, bookmark_id: str, count: int) -> None:
        """US6: 指定ブックマーク行の再生回数表示を更新する。"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == bookmark_id:
                row = self.list_widget.itemWidget(item)
                if hasattr(row, "update_play_count"):
                    row.update_play_count(count)
                break

    # ── US2: fps 更新 ──────────────────────────────────────────────

    def set_fps(self, fps: float) -> None:
        """US2: 全 BookmarkRow の fps を更新する（動画読み込み後に呼ぶ）。"""
        self._fps = fps if fps > 0 else 25.0
        for i in range(self.list_widget.count()):
            row = self.list_widget.itemWidget(self.list_widget.item(i))
            if hasattr(row, "set_fps"):
                row.set_fps(self._fps)

    # ── US9: タグ ───────────────────────────────────────────────────

    def _on_tags_changed(self, bookmark_id: str, tags: list[str]) -> None:
        if self._video_path is None:
            return
        self._store.update_tags(self._video_path, bookmark_id, tags)
        self._refresh_tag_filter_ui()

    # ── 022: A点ジャンプ / 複製 / パネル空白エリアメニュー ────────────────────

    def _on_jump_to_a(self, bookmark_id: str) -> None:
        """A点へジャンプ: seek_to_ms_requested シグナルを emit する（022）。"""
        if self._video_path is None:
            return
        bms = self._store.get_bookmarks(self._video_path)
        bm = next((b for b in bms if b.id == bookmark_id), None)
        if bm is not None:
            self.seek_to_ms_requested.emit(bm.point_a_ms)

    def _on_duplicate(self, bookmark_id: str) -> None:
        """複製: insert_after() で直後に複製ブックマークを挿入する（022）。"""
        if self._video_path is None:
            return
        bms = self._store.get_bookmarks(self._video_path)
        bm = next((b for b in bms if b.id == bookmark_id), None)
        if bm is None:
            return
        import uuid as _uuid
        from dataclasses import replace as _dc_replace
        new_bm = _dc_replace(
            bm,
            id=str(_uuid.uuid4()),
            name=bm.name + t("bookmark.copy_suffix"),
            play_count=0,
        )
        self._store.insert_after(self._video_path, new_bm, after_id=bookmark_id)
        self._refresh_list()

    def _show_panel_context_menu(self, pos) -> None:
        """パネルの空白エリア右クリックメニューを表示する（022）。

        行の上をクリックした場合は BookmarkRow のメニューが処理するため無視する。
        """
        if self.list_widget.itemAt(pos) is not None:
            return
        menu = QMenu(self)

        import_action = QAction(t("ctx.import_bookmarks"), self)
        import_action.triggered.connect(self.import_requested.emit)
        menu.addAction(import_action)

        export_action = QAction(t("ctx.export_bookmarks"), self)
        has_bookmarks = (
            self._video_path is not None
            and bool(self._store.get_bookmarks(self._video_path))
        )
        export_action.setEnabled(has_bookmarks)
        export_action.triggered.connect(self.export_from_panel_requested.emit)
        menu.addAction(export_action)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def _refresh_tag_filter_ui(self) -> None:
        """US9: タグフィルタ UI を更新する。"""
        if not hasattr(self, "tag_filter_list"):
            return
        all_tags: set[str] = set()
        if self._video_path:
            for bm in self._store.get_bookmarks(self._video_path):
                all_tags.update(bm.tags)
        self.tag_filter_list.blockSignals(True)
        self.tag_filter_list.clear()
        for tag in sorted(all_tags):
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(tag)
            item.setCheckState(Qt.CheckState.Checked if tag in self._active_tag_filter else Qt.CheckState.Unchecked)
            self.tag_filter_list.addItem(item)
        self.tag_filter_list.blockSignals(False)

    def _on_tag_filter_changed(self) -> None:
        """US9: タグフィルタの選択変更時に一覧を再描画する。"""
        self._active_tag_filter = []
        for i in range(self.tag_filter_list.count()):
            item = self.tag_filter_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self._active_tag_filter.append(item.text())
        self._refresh_list()
