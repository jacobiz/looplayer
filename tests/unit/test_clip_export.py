"""tests/unit/test_clip_export.py — ClipExportJob と ExportWorker のユニットテスト。"""
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from looplayer.clip_export import ClipExportJob, ExportWorker


# ── T002: ClipExportJob テスト ──────────────────────────────────────────────


def test_default_filename_format(tmp_path):
    """デフォルトファイル名が {stem}_00m15s-01m30s.mp4 形式になる。"""
    source = tmp_path / "lecture.mp4"
    out = tmp_path / "out.mp4"
    job = ClipExportJob(source_path=source, start_ms=15000, end_ms=90000, output_path=out)
    assert job.default_filename() == "lecture_00m15s-01m30s.mp4"


def test_default_filename_minutes_and_seconds(tmp_path):
    """60秒以上の時刻が分・秒に正しく変換される。"""
    source = tmp_path / "video.mp4"
    out = tmp_path / "out.mp4"
    job = ClipExportJob(source_path=source, start_ms=65000, end_ms=125000, output_path=out)
    assert job.default_filename() == "video_01m05s-02m05s.mp4"


def test_default_filename_preserves_extension(tmp_path):
    """元の拡張子（.mkv など）が保持される。"""
    source = tmp_path / "clip.mkv"
    out = tmp_path / "out.mkv"
    job = ClipExportJob(source_path=source, start_ms=0, end_ms=5000, output_path=out)
    assert job.default_filename().endswith(".mkv")


def test_ms_to_ffmpeg_time_conversion(tmp_path):
    """ミリ秒を HH:MM:SS.mmm 形式に変換する。"""
    source = tmp_path / "v.mp4"
    out = tmp_path / "o.mp4"
    job = ClipExportJob(source_path=source, start_ms=15250, end_ms=90000, output_path=out)
    assert job._ms_to_ffmpeg_time(15250) == "00:00:15.250"
    assert job._ms_to_ffmpeg_time(0) == "00:00:00.000"
    assert job._ms_to_ffmpeg_time(3661500) == "01:01:01.500"


def test_sanitize_filename_replaces_invalid_chars(tmp_path):
    """ファイル名に使えない文字がアンダースコアに置換される。"""
    source = tmp_path / "v.mp4"
    out = tmp_path / "o.mp4"
    job = ClipExportJob(source_path=source, start_ms=0, end_ms=1000, output_path=out)
    assert job._sanitize('abc\\/:*?"<>|def') == "abc_________def"


def test_duration_ms_property(tmp_path):
    """duration_ms が end_ms - start_ms を返す。"""
    source = tmp_path / "v.mp4"
    out = tmp_path / "o.mp4"
    job = ClipExportJob(source_path=source, start_ms=1000, end_ms=5000, output_path=out)
    assert job.duration_ms == 4000


# ── T003: ExportWorker テスト ──────────────────────────────────────────────


def _make_popen_mock(returncode: int = 0):
    """subprocess.Popen のモックを作成する。"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = returncode
    mock_proc.returncode = returncode
    mock_proc.communicate.return_value = ("", "")
    return mock_proc


def test_export_worker_emits_finished_on_success(qtbot, tmp_path):
    """returncode=0 のとき finished シグナルが出力パスとともに発行される。"""
    source = tmp_path / "v.mp4"
    source.touch()
    out = tmp_path / "out.mp4"
    job = ClipExportJob(source_path=source, start_ms=1000, end_ms=5000, output_path=out)

    mock_proc = _make_popen_mock(returncode=0)

    with patch("looplayer.clip_export.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("looplayer.clip_export.subprocess.Popen", return_value=mock_proc):
        worker = ExportWorker(job)
        received = []
        worker.finished.connect(received.append)
        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()
        worker.wait()

    assert len(received) == 1
    assert received[0] == str(out)


def test_export_worker_emits_failed_on_ffmpeg_error(qtbot, tmp_path):
    """ffmpeg が returncode=1 で終了したとき failed シグナルが発行される。"""
    source = tmp_path / "v.mp4"
    source.touch()
    out = tmp_path / "out.mp4"
    job = ClipExportJob(source_path=source, start_ms=1000, end_ms=5000, output_path=out)

    mock_proc = _make_popen_mock(returncode=1)
    mock_proc.communicate.return_value = ("", "codec error")

    with patch("looplayer.clip_export.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("looplayer.clip_export.subprocess.Popen", return_value=mock_proc):
        worker = ExportWorker(job)
        received = []
        worker.failed.connect(received.append)
        with qtbot.waitSignal(worker.failed, timeout=5000):
            worker.start()
        worker.wait()

    assert len(received) == 1


def test_export_worker_emits_failed_when_ffmpeg_not_found(qtbot, tmp_path):
    """shutil.which が None を返すとき failed シグナルが発行される。"""
    source = tmp_path / "v.mp4"
    out = tmp_path / "out.mp4"
    job = ClipExportJob(source_path=source, start_ms=1000, end_ms=5000, output_path=out)

    with patch("looplayer.clip_export.shutil.which", return_value=None):
        worker = ExportWorker(job)
        received = []
        worker.failed.connect(received.append)
        with qtbot.waitSignal(worker.failed, timeout=5000):
            worker.start()
        worker.wait()

    assert len(received) == 1
    assert "ffmpeg" in received[0].lower()


def test_export_worker_deletes_file_on_cancel(qtbot, tmp_path):
    """キャンセル時に出力ファイルが削除される。"""
    source = tmp_path / "v.mp4"
    source.touch()
    out = tmp_path / "out.mp4"
    out.touch()  # 中途半端なファイルをシミュレート
    job = ClipExportJob(source_path=source, start_ms=1000, end_ms=5000, output_path=out)

    # poll が None を返し続けることで「実行中」を模倣
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("looplayer.clip_export.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("looplayer.clip_export.subprocess.Popen", return_value=mock_proc):
        worker = ExportWorker(job)
        worker.start()
        # 開始後すぐにキャンセル要求
        import time
        time.sleep(0.05)
        worker.requestInterruption()
        worker.wait(3000)

    assert not out.exists()


def test_export_worker_builds_correct_ffmpeg_command(qtbot, tmp_path):
    """ffmpeg コマンドが copy モードで -y -ss START -i INPUT -t DURATION -c copy OUTPUT の順で組み立てられる。"""
    source = tmp_path / "video.mp4"
    source.touch()
    out = tmp_path / "clip.mp4"
    job = ClipExportJob(source_path=source, start_ms=15000, end_ms=45000, output_path=out)

    mock_proc = _make_popen_mock(returncode=0)
    captured_cmd = []

    def fake_popen(cmd, **kwargs):
        captured_cmd.extend(cmd)
        return mock_proc

    with patch("looplayer.clip_export.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("looplayer.clip_export.subprocess.Popen", side_effect=fake_popen):
        worker = ExportWorker(job)
        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()
        worker.wait()

    # copy モード: ffmpeg -y -ss START -i INPUT -t DURATION -c copy OUTPUT
    assert captured_cmd[0] == "ffmpeg"
    assert captured_cmd[1] == "-y"
    assert captured_cmd[2] == "-ss"
    assert captured_cmd[4] == "-i"
    assert captured_cmd[5] == str(source)
    assert captured_cmd[6] == "-t"
    assert captured_cmd[8] == "-c"
    assert captured_cmd[9] == "copy"
    assert captured_cmd[10] == str(out)
