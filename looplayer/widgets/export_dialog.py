"""export_dialog.py — クリップ書き出し進捗ダイアログ。"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
)

from looplayer.clip_export import ClipExportJob, ExportWorker
from looplayer.i18n import t


class ExportProgressDialog(QDialog):
    """不確定プログレスバーとキャンセルボタンを持つ書き出し進捗ダイアログ。"""

    def __init__(self, job: ClipExportJob, parent=None):
        super().__init__(parent)
        self._job = job
        self._worker: ExportWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(t("dialog.export.title"))
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        self._label = QLabel(t("dialog.export.title"))
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # 不確定（往復アニメーション）
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        self._cancel_btn = QPushButton(t("btn.later"))
        self._cancel_btn.clicked.connect(self._cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def exec(self) -> int:
        self._start_export()
        return super().exec()

    def _start_export(self) -> None:
        self._worker = ExportWorker(self._job, parent=self)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait()
        self.reject()

    def _on_finished(self, path: str) -> None:
        """書き出し完了 — ダイアログを閉じる（成功通知は呼び出し元が担当）。"""
        self.accept()

    def _on_failed(self, error: str) -> None:
        self._progress.setRange(0, 1)  # 不確定アニメーションを停止
        self._label.setText(error)
        self._cancel_btn.setText(t("btn.later"))

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait()
        event.accept()
