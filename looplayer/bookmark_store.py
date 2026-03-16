"""
ブックマークストア: ABループ区間のブックマーク管理と JSON 永続化
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── データクラス ──────────────────────────────────────────────

@dataclass
class LoopBookmark:
    """1つの AB ループ区間を表すブックマーク。"""
    point_a_ms: int
    point_b_ms: int
    name: str = ""
    repeat_count: int = 1
    order: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True  # 連続再生の対象かどうか（FR-006）
    notes: str = ""  # ブックマークメモ（US6）

    def __post_init__(self) -> None:
        if self.repeat_count < 1:
            raise ValueError(f"repeat_count は 1 以上でなければなりません: {self.repeat_count}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "point_a_ms": self.point_a_ms,
            "point_b_ms": self.point_b_ms,
            "repeat_count": self.repeat_count,
            "order": self.order,
            "enabled": self.enabled,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LoopBookmark":
        return cls(
            point_a_ms=d["point_a_ms"],
            point_b_ms=d["point_b_ms"],
            name=d.get("name", ""),
            repeat_count=d.get("repeat_count", 1),
            order=d.get("order", 0),
            id=d["id"],
            enabled=d.get("enabled", True),  # 旧 JSON には enabled キーがないため True にフォールバック
            notes=d.get("notes", ""),  # 旧 JSON には notes キーがないため "" にフォールバック
        )


# ── ストア ────────────────────────────────────────────────────

_STORAGE_PATH = Path.home() / ".looplayer" / "bookmarks.json"


class BookmarkStore:
    """動画ファイルパスをキーとして LoopBookmark を管理し JSON に永続化する。"""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._path = storage_path or _STORAGE_PATH
        # { video_path_str: [LoopBookmark, ...] }
        self._data: dict[str, list[LoopBookmark]] = {}
        self._load_all()

    # ── 永続化 ──────────────────────────────────────────────

    def _load_all(self) -> None:
        """JSON ファイルから全データを読み込む。ファイルが存在しない場合は空で初期化。"""
        if not self._path.exists():
            self._data = {}
            return
        try:
            with self._path.open(encoding="utf-8") as f:
                raw: dict = json.load(f)
            self._data = {
                k: [LoopBookmark.from_dict(item) for item in v]
                for k, v in raw.items()
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            self._data = {}

    def _save_all(self) -> None:
        """全データを JSON ファイルにアトミックに書き込む。

        一時ファイルへ書き込み後に rename することで、
        書き込み中断によるファイル破損を防ぐ。
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {
            k: [bm.to_dict() for bm in v]
            for k, v in self._data.items()
        }
        tmp = self._path.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)
            tmp.replace(self._path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    # ── CRUD ────────────────────────────────────────────────

    def get_bookmarks(self, video_path: str) -> list[LoopBookmark]:
        """指定動画のブックマーク一覧を order 順で返す。"""
        bms = self._data.get(video_path, [])
        return sorted(bms, key=lambda b: b.order)

    def add(self, video_path: str, bookmark: LoopBookmark, video_length_ms: int = 0) -> None:
        """ブックマークを追加して永続化する。

        Args:
            video_path: 動画ファイルの絶対パス
            bookmark: 追加するブックマーク
            video_length_ms: 動画の総長（ミリ秒）。0 の場合は動画長チェックをスキップ。

        Raises:
            ValueError: A点 >= B点、または B点が動画長を超える場合（FR-011）
        """
        if bookmark.point_a_ms >= bookmark.point_b_ms:
            raise ValueError(
                f"A点（{bookmark.point_a_ms}ms）は B点（{bookmark.point_b_ms}ms）より前でなければなりません"
            )
        if video_length_ms > 0 and bookmark.point_b_ms > video_length_ms:
            raise ValueError(
                f"B点（{bookmark.point_b_ms}ms）が動画長（{video_length_ms}ms）を超えています"
            )

        bms = self._data.setdefault(video_path, [])
        # デフォルト名の設定
        if not bookmark.name:
            bookmark.name = f"ブックマーク {len(bms) + 1}"
        # order の自動設定
        bookmark.order = len(bms)
        bms.append(bookmark)
        self._save_all()

    def delete(self, video_path: str, bookmark_id: str) -> None:
        """ID でブックマークを削除して永続化する。"""
        bms = self._data.get(video_path, [])
        self._data[video_path] = [b for b in bms if b.id != bookmark_id]
        # order を再採番
        for i, b in enumerate(self._data[video_path]):
            b.order = i
        self._save_all()

    def update_name(self, video_path: str, bookmark_id: str, new_name: str) -> None:
        """ブックマーク名を更新して永続化する。"""
        for b in self._data.get(video_path, []):
            if b.id == bookmark_id:
                b.name = new_name
                break
        self._save_all()

    def update_repeat_count(self, video_path: str, bookmark_id: str, count: int) -> None:
        """繰り返し回数を更新して永続化する。"""
        if count < 1:
            raise ValueError(f"repeat_count は 1 以上でなければなりません: {count}")
        for b in self._data.get(video_path, []):
            if b.id == bookmark_id:
                b.repeat_count = count
                break
        self._save_all()

    def update_notes(self, video_path: str, bookmark_id: str, notes: str) -> None:
        """ブックマークのメモを更新して永続化する（US6）。"""
        for b in self._data.get(video_path, []):
            if b.id == bookmark_id:
                b.notes = notes
                break
        self._save_all()

    def update_enabled(self, video_path: str, bookmark_id: str, enabled: bool) -> None:
        """ブックマークの enabled フラグを更新して永続化する（FR-006/FR-009）。"""
        for b in self._data.get(video_path, []):
            if b.id == bookmark_id:
                b.enabled = enabled
                break
        self._save_all()

    def update_order(self, video_path: str, ordered_ids: list[str]) -> None:
        """ID 順リストで並び順を更新して永続化する。"""
        bms_by_id = {b.id: b for b in self._data.get(video_path, [])}
        reordered = []
        for i, bid in enumerate(ordered_ids):
            if bid in bms_by_id:
                bms_by_id[bid].order = i
                reordered.append(bms_by_id[bid])
        # ordered_ids に含まれなかったブックマークを末尾に追加（消失防止）
        included = set(ordered_ids)
        for tail, bm in enumerate(
            b for b in self._data.get(video_path, []) if b.id not in included
        ):
            bm.order = len(reordered) + tail
            reordered.append(bm)
        self._data[video_path] = reordered
        self._save_all()
