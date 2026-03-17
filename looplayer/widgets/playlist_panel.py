"""PlaylistPanel: プレイリスト UI パネルウィジェット（US8）。"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt

from looplayer.i18n import t


class PlaylistPanel(QWidget):
    """プレイリストのファイル一覧を表示する。ファイルクリックで file_requested を emit する。"""

    file_requested = pyqtSignal(str)  # ファイルパス

    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlist = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def set_playlist(self, playlist) -> None:
        """プレイリストをセット/クリアする。None でクリア。"""
        self._playlist = playlist
        self.list_widget.clear()
        if playlist is None:
            return
        for path in playlist.files:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.list_widget.addItem(item)
        if playlist.files:
            self.update_current(str(playlist.current()))

    def update_current(self, path: str) -> None:
        """現在再生中のファイルをハイライトする。"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.list_widget.setCurrentRow(i)
                break

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.file_requested.emit(path)
