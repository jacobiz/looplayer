"""bookmark_io: ブックマークのエクスポート/インポート。"""
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from looplayer.bookmark_store import LoopBookmark


def export_bookmarks(bookmarks: list, dest_path: str) -> None:
    """ブックマーク一覧を JSON ファイルにエクスポートする。

    スキーマ: version:1, exported_at (ISO 8601), bookmarks[] (id 含まず)
    """
    data = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "bookmarks": [
            {
                "name": bm.name,
                "point_a_ms": bm.point_a_ms,
                "point_b_ms": bm.point_b_ms,
                "repeat_count": bm.repeat_count,
                "order": bm.order,
            }
            for bm in bookmarks
        ],
    }
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def import_bookmarks(src_path: str) -> list[dict]:
    """JSON ファイルからブックマークをインポートする。

    Returns:
        検証済みの dict リスト（LoopBookmark 生成は caller 側）

    Raises:
        ValueError: 無効な JSON またはフォーマット不正
    """
    try:
        with open(src_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"ブックマークファイルの読み込みに失敗しました: {e}") from e

    if "bookmarks" not in data:
        raise ValueError("bookmarks キーがありません")

    result = []
    for raw in data["bookmarks"]:
        try:
            bm = {
                "name": str(raw.get("name", "")),
                "point_a_ms": int(raw["point_a_ms"]),
                "point_b_ms": int(raw["point_b_ms"]),
                "repeat_count": int(raw.get("repeat_count", 1)),
                "order": int(raw.get("order", 0)),
            }
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"ブックマークデータが不正です: {e}") from e
        result.append(bm)
    return result
