"""data_backup.py のユニットテスト。"""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

_is_root = os.getuid() == 0
skip_if_root = pytest.mark.skipif(_is_root, reason="root はファイルシステム権限の制限を受けない")

from looplayer.data_backup import BackupError, create_backup, generate_backup_filename, restore_backup


# ── generate_backup_filename ──────────────────────────────────

class TestGenerateBackupFilename:
    def test_format(self):
        name = generate_backup_filename()
        assert name.startswith("looplayer-backup-")
        assert name.endswith(".zip")
        # YYYYMMDD-HHMMSS 部分が存在する
        parts = name.removeprefix("looplayer-backup-").removesuffix(".zip").split("-")
        assert len(parts) == 2
        date_part, time_part = parts
        assert len(date_part) == 8 and date_part.isdigit()
        assert len(time_part) == 6 and time_part.isdigit()


# ── create_backup ─────────────────────────────────────────────

def _make_data_dir(tmp_path: Path, files: dict[str, str]) -> Path:
    data_dir = tmp_path / "looplayer"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (data_dir / name).write_text(content, encoding="utf-8")
    return data_dir


class TestCreateBackup:
    def test_creates_zip_with_all_files(self, tmp_path):
        data_dir = _make_data_dir(tmp_path, {
            "bookmarks.json": '{"v":1}',
            "settings.json": '{"v":1}',
            "positions.json": '{"v":1}',
            "recent_files.json": '{"v":1}',
        })
        zip_path = tmp_path / "backup.zip"
        create_backup(zip_path, data_dir=data_dir)

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
        assert "bookmarks.json" in names
        assert "settings.json" in names
        assert "positions.json" in names
        assert "recent_files.json" in names
        assert "looplayer-backup.json" in names

    def test_manifest_content(self, tmp_path):
        data_dir = _make_data_dir(tmp_path, {"bookmarks.json": "{}"})
        zip_path = tmp_path / "backup.zip"
        create_backup(zip_path, data_dir=data_dir)

        with zipfile.ZipFile(zip_path) as z:
            manifest = json.loads(z.read("looplayer-backup.json"))

        assert manifest["app_name"] == "looplay!"
        assert "app_version" in manifest
        assert "created_at" in manifest
        assert "bookmarks.json" in manifest["files"]

    def test_partial_files_ok(self, tmp_path):
        """存在するファイルのみ ZIP に含める。"""
        data_dir = _make_data_dir(tmp_path, {"bookmarks.json": "{}"})
        zip_path = tmp_path / "backup.zip"
        create_backup(zip_path, data_dir=data_dir)

        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
        assert "bookmarks.json" in names
        assert "settings.json" not in names

    def test_no_files_raises_backup_error(self, tmp_path):
        """データファイルが 1 件も存在しない場合は BackupError（EC-004）。"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        zip_path = tmp_path / "backup.zip"
        with pytest.raises(BackupError):
            create_backup(zip_path, data_dir=empty_dir)
        assert not zip_path.exists()

    @skip_if_root
    def test_write_error_propagates_oserror(self, tmp_path):
        """書き込み権限なしは OSError を伝播（US2 AS3）。"""
        data_dir = _make_data_dir(tmp_path, {"bookmarks.json": "{}"})
        # 書き込み不可ディレクトリ
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir(mode=0o555)
        zip_path = readonly_dir / "backup.zip"
        with pytest.raises(OSError):
            create_backup(zip_path, data_dir=data_dir)


# ── restore_backup ────────────────────────────────────────────

def _create_valid_zip(tmp_path: Path, files: dict[str, str]) -> Path:
    """テスト用の正常な looplay! バックアップ ZIP を作成する。"""
    data_dir = _make_data_dir(tmp_path / "src", files)
    zip_path = tmp_path / "backup.zip"
    create_backup(zip_path, data_dir=data_dir)
    return zip_path


class TestRestoreBackup:
    def test_restore_cycle(self, tmp_path):
        """バックアップ→復元サイクルでデータが完全に復元される（SC-004）。"""
        original = '{"items": [{"id": "test-123"}]}'
        zip_path = _create_valid_zip(tmp_path, {"bookmarks.json": original})

        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        restore_backup(zip_path, data_dir=restore_dir)

        assert (restore_dir / "bookmarks.json").read_text(encoding="utf-8") == original

    def test_invalid_zip_raises_backup_error_invalid(self, tmp_path):
        """looplay! バックアップでない ZIP は BackupError(reason='invalid')（FR-014）。"""
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as z:
            z.writestr("random.txt", "data")
        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        with pytest.raises(BackupError) as exc_info:
            restore_backup(bad_zip, data_dir=restore_dir)
        assert exc_info.value.reason == "invalid"

    def test_corrupt_zip_raises_backup_error_corrupt(self, tmp_path):
        """破損 ZIP は BackupError(reason='corrupt')（EC-005）。"""
        corrupt_zip = tmp_path / "corrupt.zip"
        corrupt_zip.write_bytes(b"PK\x03\x04this is not a valid zip file")
        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        with pytest.raises(BackupError) as exc_info:
            restore_backup(corrupt_zip, data_dir=restore_dir)
        assert exc_info.value.reason == "corrupt"

    def test_existing_data_unchanged_on_invalid(self, tmp_path):
        """非対応ファイル時に既存データが変更されない（SC-005）。"""
        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        original = '{"preserved": true}'
        (restore_dir / "bookmarks.json").write_text(original, encoding="utf-8")

        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as z:
            z.writestr("random.txt", "data")

        with pytest.raises(BackupError):
            restore_backup(bad_zip, data_dir=restore_dir)

        assert (restore_dir / "bookmarks.json").read_text(encoding="utf-8") == original

    @skip_if_root
    def test_existing_data_unchanged_on_oserror(self, tmp_path):
        """OSError（書き込み権限なし）時に既存データが変更されない（US3 AS4）。"""
        zip_path = _create_valid_zip(tmp_path, {"bookmarks.json": '{"v":1}'})

        restore_dir = tmp_path / "restore"
        restore_dir.mkdir(mode=0o555)

        with pytest.raises(OSError):
            restore_backup(zip_path, data_dir=restore_dir)
        # restore_dir は空のまま（書き込まれていない）
        assert list(restore_dir.iterdir()) == []
