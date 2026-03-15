"""US6: bookmark_io ユニットテスト。"""
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

from looplayer.bookmark_store import LoopBookmark
from looplayer.bookmark_io import export_bookmarks, import_bookmarks


@pytest.fixture
def bookmarks():
    return [
        LoopBookmark(point_a_ms=1000, point_b_ms=5000, name="サビ部分", repeat_count=3, order=0),
        LoopBookmark(point_a_ms=6000, point_b_ms=10000, name="イントロ", repeat_count=1, order=1),
    ]


class TestExportBookmarks:
    """export_bookmarks(): JSON 出力・スキーマ確認。"""

    def test_export_creates_file(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        assert dest.exists()

    def test_export_version_is_1(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        data = json.loads(dest.read_text())
        assert data["version"] == 1

    def test_export_has_exported_at(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        data = json.loads(dest.read_text())
        assert "exported_at" in data
        # ISO 8601 形式であること（パース可能）
        datetime.fromisoformat(data["exported_at"])

    def test_export_no_id_field(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        data = json.loads(dest.read_text())
        for bm_dict in data["bookmarks"]:
            assert "id" not in bm_dict

    def test_export_bookmark_fields(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        data = json.loads(dest.read_text())
        bm = data["bookmarks"][0]
        assert bm["name"] == "サビ部分"
        assert bm["point_a_ms"] == 1000
        assert bm["point_b_ms"] == 5000
        assert bm["repeat_count"] == 3
        assert bm["order"] == 0

    def test_export_all_bookmarks_present(self, bookmarks, tmp_path):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        data = json.loads(dest.read_text())
        assert len(data["bookmarks"]) == 2


class TestImportBookmarks:
    """import_bookmarks(): パース・バリデーション。"""

    def test_import_returns_list_of_dicts(self, tmp_path, bookmarks):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        result = import_bookmarks(str(dest))
        assert isinstance(result, list)
        assert len(result) == 2

    def test_import_has_required_fields(self, tmp_path, bookmarks):
        dest = tmp_path / "export.json"
        export_bookmarks(bookmarks, str(dest))
        result = import_bookmarks(str(dest))
        for bm in result:
            assert "point_a_ms" in bm
            assert "point_b_ms" in bm
            assert "name" in bm
            assert "repeat_count" in bm

    def test_import_casts_float_to_int(self, tmp_path):
        """JSON に float が混入していても int にキャストされる。"""
        data = {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "bookmarks": [
                {"name": "test", "point_a_ms": 1000.5, "point_b_ms": 5000.0,
                 "repeat_count": 1.0, "order": 0.0}
            ]
        }
        dest = tmp_path / "import_float.json"
        dest.write_text(json.dumps(data))
        result = import_bookmarks(str(dest))
        assert isinstance(result[0]["point_a_ms"], int)
        assert isinstance(result[0]["point_b_ms"], int)
        assert isinstance(result[0]["repeat_count"], int)

    def test_import_invalid_json_raises_value_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}")
        with pytest.raises(ValueError):
            import_bookmarks(str(bad))

    def test_import_missing_bookmarks_key_raises_value_error(self, tmp_path):
        data = {"version": 1, "exported_at": "2026-01-01T00:00:00+00:00"}
        dest = tmp_path / "no_bookmarks.json"
        dest.write_text(json.dumps(data))
        with pytest.raises(ValueError):
            import_bookmarks(str(dest))
