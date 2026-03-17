"""PlaybackPosition: 再生位置の永続化（US5）。"""
import json
from pathlib import Path

_PATH = Path.home() / ".looplayer" / "positions.json"
_MAX_ENTRIES = 10


class PlaybackPosition:
    """~/.looplayer/positions.json に {filepath: position_ms} を保存・読み込みする。"""

    def __init__(self):
        self._data: dict[str, int] = self._load()

    def _load(self) -> dict:
        try:
            data = json.loads(_PATH.read_text(encoding="utf-8"))
            return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, int)}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PATH.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(_PATH)
        except OSError:
            tmp.unlink(missing_ok=True)

    def save(self, filepath: str, position_ms: int, duration_ms: int) -> None:
        """再生位置を保存する。5秒未満・95%以上は保存しない（または削除する）。"""
        if duration_ms <= 0:
            return
        if position_ms < 5000:
            return
        if position_ms / duration_ms >= 0.95:
            self._data.pop(filepath, None)
            self._save()
            return
        # 上限管理: 先頭（最古）エントリを削除
        if filepath in self._data:
            del self._data[filepath]
        while len(self._data) >= _MAX_ENTRIES:
            oldest_key = next(iter(self._data))
            del self._data[oldest_key]
        self._data[filepath] = position_ms
        self._save()

    def load(self, filepath: str) -> int | None:
        """保存済みの再生位置を返す。ファイルが存在しない場合は None。"""
        if not Path(filepath).exists():
            return None
        return self._data.get(filepath)
