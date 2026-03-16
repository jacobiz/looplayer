"""Playlist: フォルダドロップによる動画自動順再生（US7）。"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Playlist:
    """動画ファイルのプレイリスト。files はファイル名昇順で渡すこと。"""
    files: list[Path]
    index: int = 0

    def current(self) -> Path:
        return self.files[self.index]

    def has_next(self) -> bool:
        return self.index + 1 < len(self.files)

    def advance(self) -> bool:
        if self.has_next():
            self.index += 1
            return True
        return False

    def __len__(self) -> int:
        return len(self.files)
