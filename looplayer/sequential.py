"""連続再生の進行状態管理。"""
from __future__ import annotations

from dataclasses import dataclass, field

from looplayer.bookmark_store import LoopBookmark


@dataclass
class SequentialPlayState:
    """連続再生の進行状態を管理する。"""
    bookmarks: list[LoopBookmark]
    current_index: int = 0
    active: bool = True
    one_round_mode: bool = False  # True のとき1周で停止（US5）
    remaining_repeats: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.bookmarks:
            raise ValueError("bookmarks は1件以上必要です")
        self.remaining_repeats = self.bookmarks[self.current_index].repeat_count

    @property
    def current_bookmark(self) -> LoopBookmark:
        return self.bookmarks[self.current_index]

    @property
    def next_bookmark_name(self) -> str:
        next_idx = (self.current_index + 1) % len(self.bookmarks)
        return self.bookmarks[next_idx].name

    def on_b_reached(self) -> int | None:
        """B点到達時に呼び出す。次に移動すべき A点タイムスタンプ（ms）を返す。
        1周停止モードで全ブックマーク完走時は None を返す。"""
        self.remaining_repeats -= 1
        if self.remaining_repeats > 0:
            # 同じ区間を繰り返す
            return self.current_bookmark.point_a_ms

        # 最後のブックマークかどうか確認
        is_last = self.current_index == len(self.bookmarks) - 1
        if is_last and self.one_round_mode:
            # 1周停止モード: None を返して player.py 側で停止させる
            return None

        # 次の区間へ（最後なら先頭へ）
        self.current_index = (self.current_index + 1) % len(self.bookmarks)
        self.remaining_repeats = self.current_bookmark.repeat_count
        return self.current_bookmark.point_a_ms

    def stop(self) -> None:
        self.active = False
