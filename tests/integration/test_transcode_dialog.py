"""T041: トランスコードダイアログ UI の統合テスト。"""
from looplayer.app_settings import AppSettings
from looplayer.widgets.export_dialog import ExportProgressDialog
from looplayer.clip_export import ClipExportJob
from pathlib import Path


class TestExportDialog:
    def _make_job(self, tmp_path, encode_mode="copy") -> ClipExportJob:
        src = tmp_path / "src.mp4"
        src.write_bytes(b"")
        return ClipExportJob(
            source_path=src,
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
            encode_mode=encode_mode,
        )

    def test_dialog_has_radio_buttons(self, qtbot, tmp_path):
        """エクスポートダイアログにラジオボタンが存在する。"""
        from PyQt6.QtWidgets import QRadioButton
        job = self._make_job(tmp_path)
        dialog = ExportProgressDialog(job)
        qtbot.addWidget(dialog)
        radios = dialog.findChildren(QRadioButton)
        assert len(radios) >= 2

    def test_default_mode_is_copy(self, qtbot, tmp_path):
        """デフォルトで copy モードが選択されている。"""
        from PyQt6.QtWidgets import QRadioButton
        job = self._make_job(tmp_path, "copy")
        dialog = ExportProgressDialog(job)
        qtbot.addWidget(dialog)
        radios = dialog.findChildren(QRadioButton)
        copy_radios = [r for r in radios if "copy" in r.text().lower() or "高速" in r.text() or "fast" in r.text().lower()]
        assert any(r.isChecked() for r in copy_radios)

    def test_app_settings_encode_mode_properties(self, tmp_path):
        """AppSettings の export_encode_mode が正しく動作する。"""
        import os, json
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({}))

        from unittest.mock import patch
        with patch("looplayer.app_settings._SETTINGS_PATH", settings_path):
            settings = AppSettings()
            assert settings.export_encode_mode == "copy"
            settings.export_encode_mode = "transcode"
            assert settings.export_encode_mode == "transcode"
