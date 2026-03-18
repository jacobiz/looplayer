"""PreferencesDialog: アプリ設定をカテゴリ別タブで編集する QDialog（F-401）。"""
from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QComboBox, QCheckBox, QDialogButtonBox, QLabel,
)
from PyQt6.QtCore import Qt

from looplayer.app_settings import AppSettings
from looplayer.i18n import t


class PreferencesDialog(QDialog):
    """アプリ設定ダイアログ。OK で保存、Cancel で破棄。"""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(t("dialog.prefs.title"))
        self.setMinimumWidth(400)
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # タブウィジェット
        self._tabs = QTabWidget(self)
        layout.addWidget(self._tabs)

        # ── 再生タブ ──
        playback_tab = QWidget()
        playback_form = QFormLayout(playback_tab)

        self._end_action_combo = QComboBox()
        self._end_action_combo.addItem(t("dialog.prefs.end_action.stop"), "stop")
        self._end_action_combo.addItem(t("dialog.prefs.end_action.rewind"), "rewind")
        self._end_action_combo.addItem(t("dialog.prefs.end_action.loop"), "loop")
        playback_form.addRow(t("dialog.prefs.end_action.label"), self._end_action_combo)

        self._seq_mode_combo = QComboBox()
        self._seq_mode_combo.addItem(t("seq.infinite"), "infinite")
        self._seq_mode_combo.addItem(t("seq.one_round"), "one_round")
        playback_form.addRow(t("dialog.prefs.seq_mode.label"), self._seq_mode_combo)

        self._encode_mode_combo = QComboBox()
        self._encode_mode_combo.addItem(t("dialog.export.mode_copy"), "copy")
        self._encode_mode_combo.addItem(t("dialog.export.mode_transcode"), "transcode")
        playback_form.addRow(t("dialog.prefs.encode_mode.label"), self._encode_mode_combo)

        self._tabs.addTab(playback_tab, t("dialog.prefs.tab.playback"))

        # ── 表示タブ ──
        view_tab = QWidget()
        view_form = QFormLayout(view_tab)
        self._always_on_top_label = QLabel(t("dialog.prefs.always_on_top.label"))
        self._always_on_top_label.setWordWrap(True)
        view_form.addRow(self._always_on_top_label)
        self._tabs.addTab(view_tab, t("dialog.prefs.tab.view"))

        # ── アップデートタブ ──
        updates_tab = QWidget()
        updates_form = QFormLayout(updates_tab)
        self._check_update_checkbox = QCheckBox()
        updates_form.addRow(t("dialog.prefs.check_update.label"), self._check_update_checkbox)
        self._tabs.addTab(updates_tab, t("dialog.prefs.tab.updates"))

        # ── OK / Cancel ボタン ──
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self) -> None:
        """AppSettings の現在値を各ウィジェットに反映する。"""
        idx = self._end_action_combo.findData(self._settings.end_of_playback_action)
        if idx >= 0:
            self._end_action_combo.setCurrentIndex(idx)

        idx = self._seq_mode_combo.findData(self._settings.sequential_play_mode)
        if idx >= 0:
            self._seq_mode_combo.setCurrentIndex(idx)

        idx = self._encode_mode_combo.findData(self._settings.export_encode_mode)
        if idx >= 0:
            self._encode_mode_combo.setCurrentIndex(idx)

        self._check_update_checkbox.setChecked(self._settings.check_update_on_startup)

    def accept(self) -> None:
        """OK: ウィジェット値を AppSettings に書き込んでダイアログを閉じる。"""
        self._settings.end_of_playback_action = self._end_action_combo.currentData()
        self._settings.sequential_play_mode = self._seq_mode_combo.currentData()
        self._settings.export_encode_mode = self._encode_mode_combo.currentData()
        self._settings.check_update_on_startup = self._check_update_checkbox.isChecked()
        super().accept()
