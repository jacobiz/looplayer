"""US2: RecentFiles クラス ユニットテスト。"""
import json
from pathlib import Path

import pytest

from looplayer.recent_files import RecentFiles


@pytest.fixture
def rf(tmp_path: Path) -> RecentFiles:
    return RecentFiles(storage_path=tmp_path / "recent_files.json")


class TestAdd:
    """add(): 先頭挿入・重複排除・MAX10件。"""

    def test_add_single_file(self, rf):
        rf.add("/video/a.mp4")
        assert rf.files == ["/video/a.mp4"]

    def test_add_inserts_at_front(self, rf):
        rf.add("/video/a.mp4")
        rf.add("/video/b.mp4")
        assert rf.files[0] == "/video/b.mp4"
        assert rf.files[1] == "/video/a.mp4"

    def test_duplicate_moved_to_front(self, rf):
        rf.add("/video/a.mp4")
        rf.add("/video/b.mp4")
        rf.add("/video/a.mp4")
        assert rf.files[0] == "/video/a.mp4"
        assert len(rf.files) == 2

    def test_max_10_entries(self, rf):
        for i in range(12):
            rf.add(f"/video/{i}.mp4")
        assert len(rf.files) == 10

    def test_max_10_newest_kept(self, rf):
        for i in range(12):
            rf.add(f"/video/{i}.mp4")
        # 最新の10件が残る（最後に追加した11, 10が先頭）
        assert "/video/11.mp4" in rf.files
        assert "/video/0.mp4" not in rf.files
        assert "/video/1.mp4" not in rf.files


class TestRemove:
    """remove(): 存在するパスを削除する。"""

    def test_remove_existing(self, rf):
        rf.add("/video/a.mp4")
        rf.add("/video/b.mp4")
        rf.remove("/video/a.mp4")
        assert "/video/a.mp4" not in rf.files

    def test_remove_nonexistent_is_noop(self, rf):
        rf.add("/video/a.mp4")
        rf.remove("/video/notexist.mp4")
        assert rf.files == ["/video/a.mp4"]


class TestPersistence:
    """永続化: add/remove 後に JSON ファイルが書き込まれ、再ロードで復元できる。"""

    def test_persists_after_add(self, tmp_path):
        storage = tmp_path / "recent_files.json"
        rf = RecentFiles(storage_path=storage)
        rf.add("/video/a.mp4")
        assert storage.exists()
        data = json.loads(storage.read_text())
        assert "/video/a.mp4" in data["files"]

    def test_load_from_existing_file(self, tmp_path):
        storage = tmp_path / "recent_files.json"
        storage.write_text(json.dumps({"files": ["/video/c.mp4", "/video/d.mp4"]}))
        rf = RecentFiles(storage_path=storage)
        assert rf.files == ["/video/c.mp4", "/video/d.mp4"]

    def test_atomic_write_uses_tmp_then_replace(self, tmp_path):
        """書き込みは tmp ファイル経由で行われること（既存ファイルを汚染しない）。"""
        storage = tmp_path / "recent_files.json"
        rf = RecentFiles(storage_path=storage)
        rf.add("/video/e.mp4")
        # 直接書き込みの場合は .tmp ファイルが残らない
        tmp_file = storage.with_suffix(".json.tmp")
        assert not tmp_file.exists()
        assert storage.exists()

    def test_missing_file_returns_empty(self, tmp_path):
        storage = tmp_path / "nonexistent.json"
        rf = RecentFiles(storage_path=storage)
        assert rf.files == []

    def test_files_property_returns_copy(self, rf):
        rf.add("/video/a.mp4")
        files = rf.files
        files.append("/video/fake.mp4")
        assert "/video/fake.mp4" not in rf.files
