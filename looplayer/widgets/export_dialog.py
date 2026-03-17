"""export_dialog.py — クリップ書き出し進捗ダイアログ。"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QRadioButton, QGroupBox,
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

        # US10: エンコードモード選択ラジオボタン
        mode_group = QGroupBox()
        mode_layout = QVBoxLayout(mode_group)
        self._copy_radio = QRadioButton(t("dialog.export.mode_copy"))
        self._transcode_radio = QRadioButton(t("dialog.export.mode_transcode"))
        # 初期値を job.encode_mode から読み込む
        if self._job.encode_mode == "transcode":
            self._transcode_radio.setChecked(True)
        else:
            self._copy_radio.setChecked(True)
        mode_layout.addWidget(self._copy_radio)
        mode_layout.addWidget(self._transcode_radio)
        layout.addWidget(mode_group)

        self._label = QLabel(t("dialog.export.title"))
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # 不確定（往復アニメーション）
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton(t("btn.export_start"))
        self._start_btn.clicked.connect(self._on_start_clicked)
        self._cancel_btn = QPushButton(t("btn.later"))
        self._cancel_btn.clicked.connect(self._cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def _on_start_clicked(self) -> None:
        """書き出し開始ボタン: encode_mode を job にセットして export 開始。"""
        mode = "transcode" if self._transcode_radio.isChecked() else "copy"
        self._job.encode_mode = mode
        # AppSettings に保存
        try:
            from looplayer.app_settings import AppSettings
            AppSettings().export_encode_mode = mode
        except Exception:
            pass
        self._start_btn.setEnabled(False)
        self._copy_radio.setEnabled(False)
        self._transcode_radio.setEnabled(False)
        self._start_export()

    def exec(self) -> int:
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
