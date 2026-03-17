"""T040: エンコードモードのユニットテスト。"""
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

from looplayer.clip_export import ClipExportJob, ExportWorker


class TestClipExportJobEncodeMode:
    def test_default_encode_mode_is_copy(self, tmp_path):
        job = ClipExportJob(
            source_path=tmp_path / "src.mp4",
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
        )
        assert job.encode_mode == "copy"

    def test_transcode_mode_stored(self, tmp_path):
        job = ClipExportJob(
            source_path=tmp_path / "src.mp4",
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
            encode_mode="transcode",
        )
        assert job.encode_mode == "transcode"


class TestExportWorkerCommand:
    def _run_worker(self, tmp_path, encode_mode):
        src = tmp_path / "src.mp4"
        src.write_bytes(b"")
        job = ClipExportJob(
            source_path=src,
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
            encode_mode=encode_mode,
        )
        worker = ExportWorker(job)
        captured_cmd = []

        def fake_popen(cmd, **kwargs):
            captured_cmd.extend(cmd)
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"", b"")
            return mock_proc

        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.Popen", side_effect=fake_popen):
                worker.run()

        return captured_cmd

    def test_copy_mode_uses_c_copy(self, tmp_path):
        cmd = self._run_worker(tmp_path, "copy")
        assert "-c" in cmd
        idx = cmd.index("-c")
        assert cmd[idx + 1] == "copy"

    def test_transcode_mode_uses_libx264(self, tmp_path):
        cmd = self._run_worker(tmp_path, "transcode")
        assert "-c:v" in cmd
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "libx264"
        assert "-c:a" in cmd
        assert "aac" in cmd

    def test_worker_emits_finished_on_success(self, tmp_path):
        src = tmp_path / "src.mp4"
        src.write_bytes(b"")
        job = ClipExportJob(
            source_path=src,
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
        )
        worker = ExportWorker(job)
        finished_results = []
        worker.finished.connect(lambda p: finished_results.append(p))

        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.Popen", return_value=mock_proc):
                worker.run()

        assert len(finished_results) == 1

    def test_worker_emits_failed_on_error(self, tmp_path):
        src = tmp_path / "src.mp4"
        src.write_bytes(b"")
        job = ClipExportJob(
            source_path=src,
            start_ms=0,
            end_ms=5000,
            output_path=tmp_path / "out.mp4",
        )
        worker = ExportWorker(job)
        failed_results = []
        worker.failed.connect(lambda msg: failed_results.append(msg))

        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"error msg")

        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.Popen", return_value=mock_proc):
                worker.run()

        assert len(failed_results) == 1
