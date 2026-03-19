"""
データバックアップ・復元: ~/.looplayer/ 以下のデータを ZIP アーカイブで保存・復元する。
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from looplayer.version import VERSION

_DATA_DIR = Path.home() / ".looplayer"
_BACKUP_FILES = [
    "bookmarks.json",
    "settings.json",
    "positions.json",
    "recent_files.json",
]
_MANIFEST_NAME = "looplayer-backup.json"
_APP_NAME = "looplay!"  # バックアップ識別子（アプリの正式名称。変更すると既存バックアップが復元不能になる）


class BackupError(Exception):
    """バックアップ・復元の業務エラー（データなし・マニフェスト不正・ZIP 破損）。"""

    def __init__(self, message: str, reason: str = "unknown") -> None:
        super().__init__(message)
        self.reason = reason  # "invalid" | "corrupt" | "no_data" | "unknown"


def generate_backup_filename() -> str:
    """現在時刻から ZIP ファイル名を生成する（FR-010）。"""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"looplayer-backup-{ts}.zip"


def create_backup(dest_path: Path, data_dir: Path | None = None) -> None:
    """~/.looplayer/ 以下のデータを ZIP ファイルとして保存する（FR-010・FR-011）。

    Args:
        dest_path: 保存先の ZIP ファイルパス。
        data_dir: データディレクトリ（省略時は ~/.looplayer/）。

    Raises:
        BackupError: データファイルが 1 件も存在しない場合（EC-004）。
        OSError: 書き込み権限なし・ディスクフルなどの IO エラー（US2 AS3）。
    """
    base = data_dir or _DATA_DIR
    existing = [base / name for name in _BACKUP_FILES if (base / name).exists()]
    if not existing:
        raise BackupError("バックアップ対象のデータファイルが見つかりませんでした。", reason="no_data")

    manifest = {
        "app_name": _APP_NAME,
        "app_version": VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": [f.name for f in existing],
    }
    # OSError は呼び出し元に伝播させる
    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        for file_path in existing:
            zf.write(file_path, arcname=file_path.name)


def restore_backup(zip_path: Path, data_dir: Path | None = None) -> None:
    """ZIP ファイルからデータを復元する（FR-013・FR-014・FR-015）。

    Args:
        zip_path: 復元元の ZIP ファイルパス。
        data_dir: 復元先ディレクトリ（省略時は ~/.looplayer/）。

    Raises:
        BackupError(reason='corrupt'): ZIP が破損している場合。既存データを変更しない。
        BackupError(reason='invalid'): looplay! バックアップでない場合。既存データを変更しない。
        OSError: 書き込み権限なし（US3 AS4）。既存データを変更しない。
    """
    dest = data_dir or _DATA_DIR
    # 破損チェック（検証前に既存データを変更しない）
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # マニフェスト検証
            if _MANIFEST_NAME not in zf.namelist():
                raise BackupError(
                    "このファイルは looplay! バックアップではありません。", reason="invalid"
                )
            try:
                manifest = json.loads(zf.read(_MANIFEST_NAME))
            except (json.JSONDecodeError, KeyError):
                raise BackupError(
                    "このファイルは looplay! バックアップではありません。", reason="invalid"
                )
            if manifest.get("app_name") != _APP_NAME:
                raise BackupError(
                    "このファイルは looplay! バックアップではありません。", reason="invalid"
                )
            # 検証成功後に展開（OSError は呼び出し元に伝播）
            # 許可リスト外のファイルは展開しない（ZIPスリップ防止）
            allowed = set(_BACKUP_FILES)
            dest.mkdir(parents=True, exist_ok=True)
            for name in manifest.get("files", []):
                if name not in allowed:
                    continue
                if name in zf.namelist():
                    dest_file = dest / name
                    dest_file.write_bytes(zf.read(name))
    except zipfile.BadZipFile:
        raise BackupError("バックアップファイルが破損しています。", reason="corrupt")
