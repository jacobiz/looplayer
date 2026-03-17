"""clip_export.py — AB ループ区間のクリップ書き出し機能。

ClipExportJob: 書き出しジョブのデータクラス
ExportWorker:  ffmpeg subprocess を QThread で実行するバックグラウンドスレッド
"""
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from looplayer.i18n import t


@dataclass
class ClipExportJob:
    """書き出し1件を表す不変データクラス。"""
    source_path: Path
    start_ms: int
    end_ms: int
    output_path: Path
    encode_mode: str = "copy"  # "copy" | "transcode"（US10）

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def default_filename(self) -> str:
        """デフォルト出力ファイル名を生成する。例: lecture_00m15s-01m30s.mp4"""
        start_label = self._ms_to_label(self.start_ms)
        end_label = self._ms_to_label(self.end_ms)
        stem = self.source_path.stem
        suffix = self.source_path.suffix
        return f"{stem}_{start_label}-{end_label}{suffix}"

    def default_filename_for_bookmark(self, bookmark_name: str) -> str:
        """ブックマーク名ベースのデフォルト出力ファイル名を生成する。"""
        start_label = self._ms_to_label(self.start_ms)
        end_label = self._ms_to_label(self.end_ms)
        safe_name = self._sanitize(bookmark_name)
        suffix = self.source_path.suffix
        return f"{safe_name}_{start_label}-{end_label}{suffix}"

    @staticmethod
    def _ms_to_label(ms: int) -> str:
        """ミリ秒を mm'm'ss's' 形式に変換する。例: 15000 → '00m15s'"""
        total_s = ms // 1000
        m = total_s // 60
        s = total_s % 60
        return f"{m:02d}m{s:02d}s"

    @staticmethod
    def _ms_to_ffmpeg_time(ms: int) -> str:
        """ミリ秒を HH:MM:SS.mmm 形式に変換する。例: 15250 → '00:00:15.250'"""
        total_ms = ms
        h = total_ms // 3_600_000
        total_ms %= 3_600_000
        m = total_ms // 60_000
        total_ms %= 60_000
        s = total_ms // 1000
        ms_rem = total_ms % 1000
        return f"{h:02d}:{m:02d}:{s:02d}.{ms_rem:03d}"

    @staticmethod
    def _sanitize(name: str) -> str:
        """ファイル名に使えない文字をアンダースコアに置換する。"""
        return re.sub(r'[\\/:*?"<>|]', '_', name)


class ExportWorker(QThread):
    """ffmpeg subprocess を QThread で実行するバックグラウンドスレッド。"""

    finished = pyqtSignal(str)  # 出力ファイルの絶対パス
    failed = pyqtSignal(str)    # エラーメッセージ

    def __init__(self, job: ClipExportJob, parent=None):
        super().__init__(parent)
        self._job = job
        self._process: subprocess.Popen | None = None

    def run(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.failed.emit(t("error.ffmpeg_not_found"))
            return

        start_time = ClipExportJob._ms_to_ffmpeg_time(self._job.start_ms)
        end_time = ClipExportJob._ms_to_ffmpeg_time(self._job.end_ms)
        # US10: encode_mode に応じてコーデック引数を切り替える
        if self._job.encode_mode == "transcode":
            codec_args = ["-c:v", "libx264", "-c:a", "aac", "-crf", "23"]
        else:
            codec_args = ["-c", "copy"]
        cmd = [
            "ffmpeg",
            "-ss", start_time,
            "-to", end_time,
            "-i", str(self._job.source_path),
            *codec_args,
            str(self._job.output_path),
            "-y",
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            self.failed.emit(t("error.source_not_found").format(path=self._job.source_path))
            return
        except OSError as e:
            self.failed.emit(str(e))
            return

        # stderr をバックグラウンドスレッドで読み続け、パイプバッファ溢れによる
        # デッドロック（プロセスが stderr 書き込みでブロックし poll() が戻らない）を防ぐ。
        stderr_chunks: list[bytes] = []

        def _drain_stderr() -> None:
            assert self._process is not None
            for line in self._process.stderr:
                stderr_chunks.append(line)

        drain = threading.Thread(target=_drain_stderr, daemon=True)
        drain.start()

        while self._process.poll() is None:
            if self.isInterruptionRequested():
                self._terminate()
                drain.join(timeout=5)
                self._job.output_path.unlink(missing_ok=True)
                return
            self.msleep(100)

        drain.join(timeout=5)
        returncode = self._process.returncode
        if returncode == 0:
            self.finished.emit(str(self._job.output_path))
        else:
            err_text = b"".join(stderr_chunks).decode(errors="replace").strip()
            self._job.output_path.unlink(missing_ok=True)
            self.failed.emit(t("error.ffmpeg_error").format(code=returncode, detail=err_text))

    def _terminate(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
