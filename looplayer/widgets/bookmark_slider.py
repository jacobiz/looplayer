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
_AB_LINE_COLOR = QColor(255, 255, 255, 200)  # US2: AB 点縦線（白・高不透明）
_AB_BAR_COLOR  = QColor(255, 255, 255, 120)  # US2: AB 点バー（白・半透明）


class BookmarkSlider(QSlider):
    """ブックマーク区間バーを重ね描きするシークスライダー（FR-001〜FR-005）。"""

    bookmark_bar_clicked = pyqtSignal(str)   # クリックされたブックマークの ID
    seek_requested = pyqtSignal(int)         # トラッククリック/ドラッグ時のシーク位置（ms）
    ab_point_drag_finished = pyqtSignal(str, int)  # US3: "a"/"b" と確定 ms 値

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._bookmarks: list[LoopBookmark] = []
        self._duration_ms: int = 0
        self._current_id: str | None = None  # 連続再生中の強調対象 ID
        self._dragging: bool = False          # トラッククリック起点のドラッグ中フラグ
        # US2: 設定中 AB 点プレビュー（保存前の一時状態）
        self._ab_preview_a: int | None = None
        self._ab_preview_b: int | None = None
        # US3: AB 点ドラッグターゲット
        self._ab_drag_target: str | None = None
        # F-105: ズームモード
        self._zoom_enabled: bool = False
        self._zoom_start_ms: int = 0
        self._zoom_end_ms: int = 0

    # ── ズームモード ──────────────────────────────────────────

    @property
    def zoom_enabled(self) -> bool:
        """ズームモードが有効かどうかを返す。"""
        return self._zoom_enabled

    def set_zoom(self, start_ms: int, end_ms: int) -> None:
        """ズームモードを有効化して表示範囲を設定する。start_ms < end_ms が必要。"""
        if start_ms >= end_ms:
            raise ValueError(f"start_ms ({start_ms}) must be less than end_ms ({end_ms})")
        self._zoom_start_ms = start_ms
        self._zoom_end_ms = end_ms
        self._zoom_enabled = True
        self.update()

    def clear_zoom(self) -> None:
        """ズームモードを無効化して通常表示に戻す。"""
        self._zoom_enabled = False
        self._zoom_start_ms = 0
        self._zoom_end_ms = 0
        self.update()

    # ── 外部インターフェース ──────────────────────────────────

    @property
    def is_track_dragging(self) -> bool:
        """トラッククリック起点のドラッグ中かどうかを返す。"""
        return self._dragging

    def set_ab_preview(self, a_ms: int | None, b_ms: int | None) -> None:
        """US2: 設定中 AB 点プレビューを更新して再描画する。None = 未設定/消去。"""
        self._ab_preview_a = a_ms
        self._ab_preview_b = b_ms
        self.update()

    def set_position_ms(self, current_ms: int) -> None:
        """現在の再生位置（ms）をズームモードに応じた QSlider value に変換してセットする。
        ズーム有効時は zoom_start〜zoom_end の相対割合に変換し、
        範囲外は Qt の setValue クリップにより自動的に端固定となる（FR-004）。"""
        if self._zoom_enabled and self._zoom_end_ms > self._zoom_start_ms:
            zoom_range = self._zoom_end_ms - self._zoom_start_ms
            value = int((current_ms - self._zoom_start_ms) / zoom_range * self.maximum())
        elif self._duration_ms > 0:
            value = int(current_ms / self._duration_ms * self.maximum())
        else:
            value = 0
        self.setValue(value)

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
        """ミリ秒をグルーブ内 X 座標に変換する（動画長外はクリップ）。
        ズームモード有効時は zoom_start_ms〜zoom_end_ms がグルーブ全幅にマップされる。"""
        if self._zoom_enabled and duration_ms is None:
            zoom_range = self._zoom_end_ms - self._zoom_start_ms
            if zoom_range <= 0:
                return groove.left()
            ratio = max(0.0, min(1.0, (ms - self._zoom_start_ms) / zoom_range))
            return groove.left() + int(ratio * groove.width())
        dur = duration_ms if duration_ms is not None else self._duration_ms
        if dur <= 0:
            return groove.left()
        ratio = max(0.0, min(1.0, ms / dur))
        return groove.left() + int(ratio * groove.width())

    def _x_to_ms(self, x: int, groove: QRect) -> int:
        """グルーブ内 X 座標をミリ秒に変換する（[0, _duration_ms] にクリップ）。
        ズームモード有効時は zoom_start_ms〜zoom_end_ms の範囲に変換する。"""
        if groove.width() <= 0:
            return 0
        ratio = max(0.0, min(1.0, (x - groove.left()) / groove.width()))
        if self._zoom_enabled:
            zoom_range = self._zoom_end_ms - self._zoom_start_ms
            return int(self._zoom_start_ms + ratio * zoom_range)
        return int(ratio * self._duration_ms)

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
            # ズームモード中はズーム範囲と重なるブックマークのみ描画する
            if self._zoom_enabled:
                if bm.point_b_ms < self._zoom_start_ms or bm.point_a_ms > self._zoom_end_ms:
                    continue
            is_current = (bm.id == self._current_id)
            color = _CURRENT_COLOR if is_current else _COLORS[i % len(_COLORS)]
            x1, x2 = self._bar_x_range(bm.point_a_ms, bm.point_b_ms, groove)
            rect = QRect(x1, groove.top(), x2 - x1, groove.height())
            painter.fillRect(rect, color)

        # US2: 設定中 AB 点プレビューを描画（保存済みブックマークバーの上に重ねる）
        self._paint_ab_preview(painter, groove)

        painter.end()

    def _paint_ab_preview(self, painter: QPainter, groove: QRect) -> None:
        """US2: 設定中 AB 点プレビューを描画する。"""
        a_ms = self._ab_preview_a
        b_ms = self._ab_preview_b
        if a_ms is None and b_ms is None:
            return
        if self._duration_ms <= 0:
            return

        if a_ms is not None and b_ms is not None:
            # A・B 両方設定済み：半透明バー + 両端縦線
            xa = self._ms_to_x(a_ms, groove)
            xb = self._ms_to_x(b_ms, groove)
            if xb > xa:
                bar_rect = QRect(xa, groove.top(), xb - xa, groove.height())
                painter.fillRect(bar_rect, _AB_BAR_COLOR)
            # 両端縦線
            painter.fillRect(QRect(xa, groove.top(), 3, groove.height()), _AB_LINE_COLOR)
            painter.fillRect(QRect(xb - 2, groove.top(), 3, groove.height()), _AB_LINE_COLOR)
        elif a_ms is not None:
            # A 点のみ：縦線マーカー
            xa = self._ms_to_x(a_ms, groove)
            painter.fillRect(QRect(xa - 1, groove.top(), 3, groove.height()), _AB_LINE_COLOR)
        elif b_ms is not None:
            # B 点のみ：縦線マーカー
            xb = self._ms_to_x(b_ms, groove)
            painter.fillRect(QRect(xb - 1, groove.top(), 3, groove.height()), _AB_LINE_COLOR)

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

    def _find_ab_drag_target(self, x: int) -> str | None:
        """US3: X 座標が AB 点マーカーの ±6px 以内かを判定し 'a'/'b'/None を返す。"""
        if self._duration_ms <= 0:
            return None
        groove = self._groove_rect()
        if groove.width() <= 0:
            return None
        _HIT_PX = 6
        if self._ab_preview_a is not None:
            xa = self._ms_to_x(self._ab_preview_a, groove)
            if abs(x - xa) <= _HIT_PX:
                return "a"
        if self._ab_preview_b is not None:
            xb = self._ms_to_x(self._ab_preview_b, groove)
            if abs(x - xb) <= _HIT_PX:
                return "b"
        return None

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """バーのクリックを検出して bookmark_bar_clicked を emit するか、トラッククリックシークを行う。
        US3: AB 点マーカー付近のクリックは AB ドラッグモードを開始する（最高優先度）。"""
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().toPoint().x()
            # US3: AB マーカードラッグ判定（ブックマーク・シークより優先）
            ab_target = self._find_ab_drag_target(x)
            if ab_target is not None:
                self._ab_drag_target = ab_target
                event.accept()
                return
            bm_id = self._find_bookmark_at_x(x)
            if bm_id is not None:
                self.bookmark_bar_clicked.emit(bm_id)
                event.accept()  # super() を呼ばず明示的に処理済みとする
                return
            if self._duration_ms > 0:
                groove = self._groove_rect()
                ms = self._x_to_ms(x, groove)
                self.seek_requested.emit(ms)
                self._dragging = True
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        """ドラッグ中に seek_requested をリアルタイムで emit する。
        US3: AB ドラッグ中はプレビュー位置を更新して再描画する。"""
        if self._ab_drag_target is not None and event.buttons() & Qt.MouseButton.LeftButton:
            # US3: AB 点ドラッグ中 — プレビュー位置を更新（A < B 制約を適用）
            groove = self._groove_rect()
            ms = self._x_to_ms(event.position().toPoint().x(), groove)
            if self._ab_drag_target == "a":
                if self._ab_preview_b is not None:
                    ms = min(ms, self._ab_preview_b - 1)
                ms = max(ms, 0)
                self._ab_preview_a = ms
            else:  # "b"
                if self._ab_preview_a is not None:
                    ms = max(ms, self._ab_preview_a + 1)
                ms = min(ms, self._duration_ms)
                self._ab_preview_b = ms
            self.update()
        elif self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            groove = self._groove_rect()
            ms = self._x_to_ms(event.position().toPoint().x(), groove)
            self.seek_requested.emit(ms)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        """ドラッグ終了時に _dragging フラグをクリアする。
        US3: AB ドラッグ中はリリース時に ab_point_drag_finished を emit する。"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._ab_drag_target is not None:
                # US3: ドラッグ終了 → 確定 ms 値を emit
                target = self._ab_drag_target
                ms = self._ab_preview_a if target == "a" else self._ab_preview_b
                if ms is not None:
                    self.ab_point_drag_finished.emit(target, ms)
                self._ab_drag_target = None
                event.accept()
                return
            self._dragging = False
        super().mouseReleaseEvent(event)
