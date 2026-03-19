"""RecentFiles: 最近開いたファイルの永続管理クラス。"""
import json
import os
from pathlib import Path


class RecentFiles:
    """最近開いたファイルパスを最大 MAX 件、永続化して管理する。"""

    MAX = 10

    def __init__(self, storage_path=None):
        if storage_path is None:
            storage_path = Path.home() / ".looplayer" / "recent_files.json"
        self._path = Path(storage_path)
        self._files: list[str] = self._load()

    def add(self, path: str) -> None:
        """パスを先頭に挿入する（重複排除・MAX超過削除）。"""
        if path in self._files:
            self._files.remove(path)
        self._files.insert(0, path)
        if len(self._files) > self.MAX:
            self._files = self._files[:self.MAX]
        self._save()

    def remove(self, path: str) -> None:
        """パスをリストから削除する（存在しない場合は無視）。"""
        if path in self._files:
            self._files.remove(path)
            self._save()

    @property
    def files(self) -> list[str]:
        """最新順のパスリストのコピーを返す。"""
        return list(self._files)

    def _load(self) -> list[str]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data.get("files", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError, TypeError):
            return []

    def _save(self) -> None:
        """tmp ファイル経由でアトミックに書き込む。"""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                json.dumps({"files": self._files}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self._path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise
