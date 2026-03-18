"""updater.py — 自動更新機能。バージョン確認・ダウンロード・インストーラー起動。"""
import json
import sys
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar,
    QHBoxLayout, QPushButton, QMessageBox,
)

from looplayer.version import VERSION
from looplayer.i18n import t

_API_URL = "https://api.github.com/repos/jacobiz/looplayer/releases/latest"
_TIMEOUT = 5  # 秒
_CHECK_INTERVAL_SECS = 86400  # 24時間キャッシュ


# ── バージョン比較 ────────────────────────────────────────────────────────────


def _parse_version(ver: str) -> tuple[int, ...]:
    """'v1.2.3' または '1.2.3' をタプルに変換する。"""
    return tuple(int(x) for x in ver.lstrip("v").split("."))


def _is_newer(current: str, latest: str) -> bool:
    """latest が current より新しい場合 True を返す。"""
    return _parse_version(latest) > _parse_version(current)


# ── UpdateChecker ─────────────────────────────────────────────────────────────


class UpdateChecker(QThread):
    """バックグラウンドで GitHub Releases から最新バージョンを確認するスレッド。"""

    update_available = pyqtSignal(str, str)  # (latest_version, download_url)
    up_to_date = pyqtSignal()
    check_failed = pyqtSignal(str)           # error_message

    def __init__(self, current_version: str = VERSION, settings=None, parent=None):
        super().__init__(parent)
        self._current_version = current_version
        self._settings = settings  # AppSettings | None

    def run(self) -> None:
        # 24h キャッシュ: 前回チェックから _CHECK_INTERVAL_SECS 未満なら API を叩かない
        if self._settings is not None:
            elapsed = time.time() - self._settings.last_update_check_ts
            if elapsed < _CHECK_INTERVAL_SECS:
                self.up_to_date.emit()
                return

        headers = {"User-Agent": f"looplay!/{self._current_version}"}
        if self._settings is not None and self._settings.update_check_etag:
            headers["If-None-Match"] = self._settings.update_check_etag

        try:
            req = urllib.request.Request(_API_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                etag = resp.headers.get("ETag", "")
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 304:
                # 304 Not Modified: データ未変更 → タイムスタンプのみ更新
                if self._settings is not None:
                    self._settings.last_update_check_ts = time.time()
                self.up_to_date.emit()
                return
            self.check_failed.emit(str(e))
            return
        except Exception as e:
            self.check_failed.emit(str(e))
            return

        # ETag とタイムスタンプを保存
        if self._settings is not None:
            if etag:
                self._settings.update_check_etag = etag
            self._settings.last_update_check_ts = time.time()

        tag = data.get("tag_name", "")
        if not tag:
            self.check_failed.emit("API から tag_name が取得できませんでした")
            return
        latest = tag.lstrip("v")

        try:
            if not _is_newer(self._current_version, latest):
                self.up_to_date.emit()
                return
        except (ValueError, AttributeError):
            self.check_failed.emit(f"バージョン解析エラー: {tag!r}")
            return

        download_url = _select_asset(data.get("assets", []), latest)
        self.update_available.emit(latest, download_url)


def _select_asset(assets: list, version: str) -> str:
    """プラットフォームに対応するインストーラー URL を返す。対応外は空文字列。"""
    if sys.platform == "win32":
        pattern = f"looplay-Setup-{version}.exe"
    elif sys.platform == "darwin":
        pattern = f"looplay-{version}.dmg"
    else:
        # Linux 等: ダウンロードをスキップ（通知のみ）
        return ""

    for asset in assets:
        if asset.get("name") == pattern:
            url = asset.get("browser_download_url", "")
            if url.startswith("https://github.com/"):
                return url
            return ""
    return ""


# ── DownloadThread ────────────────────────────────────────────────────────────


class DownloadThread(QThread):
    """インストーラーをバックグラウンドでダウンロードするスレッド。"""

    progress = pyqtSignal(int)   # 0-100
    finished = pyqtSignal(str)   # 保存先絶対パス
    failed = pyqtSignal(str)     # エラーメッセージ

    def __init__(self, url: str, dest: Path, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest = dest

    def run(self) -> None:
        def reporthook(block_num: int, block_size: int, total_size: int) -> None:
            if self.isInterruptionRequested():
                raise InterruptedError("ダウンロードがキャンセルされました")
            if total_size > 0:
                percent = min(int(block_num * block_size * 100 / total_size), 100)
                self.progress.emit(percent)

        try:
            urllib.request.urlretrieve(self._url, self._dest, reporthook)
            self.finished.emit(str(self._dest))
        except InterruptedError:
            self._dest.unlink(missing_ok=True)
        except Exception as e:
            self._dest.unlink(missing_ok=True)
            self.failed.emit(str(e))


# ── DownloadDialog ────────────────────────────────────────────────────────────


class DownloadDialog(QDialog):
    """インストーラーダウンロードの進捗を表示するモーダルダイアログ。"""

    def __init__(self, url: str, version: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._version = version
        self._thread: DownloadThread | None = None
        self._dest: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(t("dialog.download.title"))
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        self._label = QLabel(t("dialog.download.title"))
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        self._cancel_btn = QPushButton(t("btn.later"))
        self._cancel_btn.clicked.connect(self._cancel)
        self._retry_btn = QPushButton(t("btn.retry"))
        self._retry_btn.clicked.connect(self._start_download)
        self._retry_btn.setVisible(False)
        btn_layout.addStretch()
        btn_layout.addWidget(self._retry_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def exec(self) -> int:
        self._start_download()
        return super().exec()

    def _start_download(self) -> None:
        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.requestInterruption()
                self._thread.wait()
            self._thread.deleteLater()
            self._thread = None

        filename = self._url.split("/")[-1]
        self._dest = Path(tempfile.gettempdir()) / filename

        self._progress.setValue(0)
        self._retry_btn.setVisible(False)
        self._cancel_btn.setText(t("btn.later"))
        self._label.setText(t("dialog.download.title"))

        self._thread = DownloadThread(self._url, self._dest, parent=self)
        self._thread.progress.connect(self._progress.setValue)
        self._thread.finished.connect(self._on_finished)
        self._thread.failed.connect(self._on_failed)
        self._thread.start()

    def _cancel(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.wait()
        self.reject()

    def _on_finished(self, path: str) -> None:
        self._launch_installer(path)
        self.accept()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(500, app.quit)

    def _launch_installer(self, path: str) -> None:
        if sys.platform == "win32":
            subprocess.Popen([path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])

    def _on_failed(self, error: str) -> None:
        self._label.setText(f"{t('msg.update_download_failed.title')}: {error}")
        self._retry_btn.setVisible(True)
        self._cancel_btn.setText(t("btn.later"))

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.wait()
        event.accept()
