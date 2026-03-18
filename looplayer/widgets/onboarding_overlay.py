"""OnboardingOverlay: 初回起動チュートリアルの非モーダルオーバーレイ（F-501）。"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

from looplayer.app_settings import AppSettings
from looplayer.i18n import t

_TOTAL_STEPS = 4

_STEP_KEYS = [
    ("onboarding.step0.title", "onboarding.step0.body"),
    ("onboarding.step1.title", "onboarding.step1.body"),
    ("onboarding.step2.title", "onboarding.step2.body"),
    ("onboarding.step3.title", "onboarding.step3.body"),
]


class OnboardingOverlay(QWidget):
    """4ステップのチュートリアルオーバーレイ。完了/スキップ時のみフラグを保存する。"""

    def __init__(self, settings: AppSettings, parent: QWidget) -> None:
        super().__init__(parent)
        self._settings = settings
        self._step = 0
        self._completed = False
        self._build_ui()
        self._show_step(0)
        self._reposition(parent)

    def _build_ui(self) -> None:
        """UI を構築する。"""
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30, 220))
        self.setPalette(palette)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "OnboardingOverlay { background: rgba(30,30,30,210); border-radius: 12px; }"
            "QLabel { color: white; }"
            "QPushButton { color: white; background: rgba(80,80,80,200); border: 1px solid #888; "
            "  border-radius: 4px; padding: 6px 16px; }"
            "QPushButton:hover { background: rgba(120,120,120,220); }"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        # 進捗ラベル
        self._progress_label = QLabel()
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        outer.addWidget(self._progress_label)

        # タイトル
        self._title_label = QLabel()
        font = self._title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self._title_label.setFont(font)
        self._title_label.setWordWrap(True)
        outer.addWidget(self._title_label)

        # 本文
        self._body_label = QLabel()
        self._body_label.setWordWrap(True)
        outer.addWidget(self._body_label)

        outer.addStretch()

        # ボタン行
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._skip_btn = QPushButton(t("onboarding.btn.skip"))
        self._skip_btn.clicked.connect(self._on_skip)
        btn_row.addWidget(self._skip_btn)

        self._next_btn = QPushButton(t("onboarding.btn.next"))
        self._next_btn.clicked.connect(self._on_next)
        btn_row.addWidget(self._next_btn)

        outer.addLayout(btn_row)

    def _show_step(self, step: int) -> None:
        """指定ステップの内容を表示する。"""
        self._step = step
        title_key, body_key = _STEP_KEYS[step]
        self._title_label.setText(t(title_key))
        self._body_label.setText(t(body_key))
        self._progress_label.setText(
            t("onboarding.progress").format(step=step + 1, total=_TOTAL_STEPS)
        )
        if step == _TOTAL_STEPS - 1:
            self._next_btn.setText(t("onboarding.btn.finish"))
        else:
            self._next_btn.setText(t("onboarding.btn.next"))

    def _on_next(self) -> None:
        """「次へ」/「完了」ボタンのクリックハンドラ。"""
        if self._step < _TOTAL_STEPS - 1:
            self._show_step(self._step + 1)
        else:
            # 最終ステップ → 完了
            self._completed = True
            self._settings.onboarding_shown = True
            self.hide()

    def _on_skip(self) -> None:
        """「スキップ」ボタンのクリックハンドラ。フラグを保存して閉じる（FR-304/305）。"""
        self._completed = True
        self._settings.onboarding_shown = True
        self.hide()

    def _reposition(self, parent: QWidget) -> None:
        """親ウィジェット中央に配置する。"""
        w, h = 480, 280
        px = max(0, (parent.width() - w) // 2)
        py = max(0, (parent.height() - h) // 2)
        self.setGeometry(px, py, w, h)
        self.raise_()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """親がリサイズされた際に自動的に中央へ追従する。"""
        super().resizeEvent(event)
        if self.parent() is not None:
            self._reposition(self.parent())
