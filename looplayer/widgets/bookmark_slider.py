"""BookmarkSlider: ABループ区間をシークバー上に半透明バーで表示するスライダー。"""
from PyQt6.QtWidgets import QSlider, QStyleOptionSlider, QStyle
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRect, pyqtSignal

from looplayer.bookmark_store import LoopBookmark

# ブックマーク区間バーの色パレット（アルファ = 120 ≈ 47% 不透明）
_COLORS = [
    QColor(255, 165,   0, 120),  # オレンジ
    QColor(  0, 200, 255, 120),  # シアン
    QColor(200,   0, 255, 120),  # パープル
    QColor(  0, 255, 100, 120),  # グリーン
]
_CURRENT_COLOR = QColor(255, 255,   0, 180)  # 強調表示用（黄色・高不透明）
_MIN_BAR_WIDTH = 4  # 最小クリック可能幅（px）


class BookmarkSlider(QSlider):
    """ブックマーク区間バーを重ね描きするシークスライダー（FR-001〜FR-005）。"""

    bookmark_bar_clicked = pyqtSignal(str)  # クリックされたブックマークの ID

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._bookmarks: list[LoopBookmark] = []
        self._duration_ms: int = 0
        self._current_id: str | None = None  # 連続再生中の強調対象 ID

    # ── 外部インターフェース ──────────────────────────────────

    def set_bookmarks(
        self,
        bookmarks: list[LoopBookmark],
        duration_ms: int,
        current_id: str | None = None,
    ) -> None:
        """ブックマーク一覧・動画尺・現在区間 ID を更新して再描画する。"""
        self._bookmarks = list(bookmarks)
        self._duration_ms = duration_ms
        self._current_id = current_id
        self.update()

    # ── 描画 ─────────────────────────────────────────────────

    def _groove_rect(self) -> QRect:
        """プラットフォームスタイルに従ったグルーブ（トラック）領域を返す。"""
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        return self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            opt,
            QStyle.SubControl.SC_SliderGroove,
            self,
        )

    def _ms_to_x(self, ms: int, groove: QRect, duration_ms: int | None = None) -> int:
        """ミリ秒をグルーブ内 X 座標に変換する（動画長外はクリップ）。"""
        dur = duration_ms if duration_ms is not None else self._duration_ms
        if dur <= 0:
            return groove.left()
        ratio = max(0.0, min(1.0, ms / dur))
        return groove.left() + int(ratio * groove.width())

    def _bar_x_range(
        self, a_ms: int, b_ms: int, groove: QRect, duration_ms: int | None = None
    ) -> tuple[int, int]:
        """A〜B点の X 座標ペアを返す。最小幅 _MIN_BAR_WIDTH を保証する。"""
        x1 = self._ms_to_x(a_ms, groove, duration_ms)
        x2 = self._ms_to_x(b_ms, groove, duration_ms)
        if x2 - x1 < _MIN_BAR_WIDTH:
            x2 = x1 + _MIN_BAR_WIDTH
        return x1, x2

    def paintEvent(self, event) -> None:  # type: ignore[override]
        # ① QSlider 本来の描画（グルーブ・ハンドル）を先に完成させる
        super().paintEvent(event)

        if self._duration_ms <= 0 or not self._bookmarks:
            return

        groove = self._groove_rect()
        if groove.width() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        for i, bm in enumerate(self._bookmarks):
            is_current = (bm.id == self._current_id)
            color = _CURRENT_COLOR if is_current else _COLORS[i % len(_COLORS)]
            x1, x2 = self._bar_x_range(bm.point_a_ms, bm.point_b_ms, groove)
            rect = QRect(x1, groove.top(), x2 - x1, groove.height())
            painter.fillRect(rect, color)

        painter.end()

    # ── クリック判定 ──────────────────────────────────────────

    def _find_bookmark_at_x(self, x: int) -> str | None:
        """X 座標に対応するブックマーク ID を返す。重複時は後ろ（最前面）優先。"""
        if self._duration_ms <= 0:
            return None
        groove = self._groove_rect()
        if groove.width() <= 0:
            return None
        result = None
        for bm in self._bookmarks:
            x1, x2 = self._bar_x_range(bm.point_a_ms, bm.point_b_ms, groove)
            if x1 <= x <= x2:
                result = bm.id  # 後勝ちで上書き → 最後に登録したものが選択される
        return result

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """バーのクリックを検出して bookmark_bar_clicked シグナルを emit する。"""
        if event.button() == Qt.MouseButton.LeftButton:
            bm_id = self._find_bookmark_at_x(event.position().toPoint().x())
            if bm_id is not None:
                self.bookmark_bar_clicked.emit(bm_id)
                return  # シークは行わず、ブックマーク選択のみ
        super().mousePressEvent(event)
