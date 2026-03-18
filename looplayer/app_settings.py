"""AppSettings: アプリケーション設定の永続化（US4）。"""
import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".looplayer" / "settings.json"
_VALID_ACTIONS = ("stop", "rewind", "loop")


class AppSettings:
    """~/.looplayer/settings.json にアプリ設定を保存・読み込みする。"""

    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def save(self) -> None:
        """設定をアトミックに保存する。"""
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SETTINGS_PATH.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(_SETTINGS_PATH)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    @property
    def end_of_playback_action(self) -> str:
        val = self._data.get("end_of_playback_action", "stop")
        return val if val in _VALID_ACTIONS else "stop"

    @end_of_playback_action.setter
    def end_of_playback_action(self, value: str) -> None:
        if value not in _VALID_ACTIONS:
            raise ValueError(f"Invalid action: {value!r}。有効値: {_VALID_ACTIONS}")
        self._data["end_of_playback_action"] = value
        self.save()

    @property
    def check_update_on_startup(self) -> bool:
        return bool(self._data.get("check_update_on_startup", True))

    @check_update_on_startup.setter
    def check_update_on_startup(self, value: bool) -> None:
        self._data["check_update_on_startup"] = value
        self.save()

    @property
    def sequential_play_mode(self) -> str:
        val = self._data.get("sequential_play_mode", "infinite")
        return val if val in ("infinite", "one_round") else "infinite"

    @sequential_play_mode.setter
    def sequential_play_mode(self, value: str) -> None:
        if value not in ("infinite", "one_round"):
            raise ValueError(f"Invalid sequential_play_mode: {value!r}")
        self._data["sequential_play_mode"] = value
        self.save()

    @property
    def export_encode_mode(self) -> str:
        val = self._data.get("export_encode_mode", "copy")
        return val if val in ("copy", "transcode") else "copy"

    @export_encode_mode.setter
    def export_encode_mode(self, value: str) -> None:
        if value not in ("copy", "transcode"):
            raise ValueError(f"Invalid export_encode_mode: {value!r}")
        self._data["export_encode_mode"] = value
        self.save()

    @property
    def last_update_check_ts(self) -> float:
        """前回の更新チェック時刻（Unix タイムスタンプ）。未チェックは 0.0。"""
        return float(self._data.get("last_update_check_ts", 0.0))

    @last_update_check_ts.setter
    def last_update_check_ts(self, value: float) -> None:
        self._data["last_update_check_ts"] = value
        self.save()

    @property
    def update_check_etag(self) -> str:
        """GitHub API の前回レスポンス ETag。未取得は空文字列。"""
        return str(self._data.get("update_check_etag", ""))

    @update_check_etag.setter
    def update_check_etag(self, value: str) -> None:
        self._data["update_check_etag"] = value
        self.save()

    @property
    def window_geometry(self) -> dict | None:
        """ウィンドウ位置・サイズ（x, y, width, height）。未設定は None。"""
        geo = self._data.get("window_geometry")
        if geo is None:
            return None
        if not all(k in geo for k in ("x", "y", "width", "height")):
            return None
        return geo

    @window_geometry.setter
    def window_geometry(self, value: dict | None) -> None:
        if value is None:
            self._data.pop("window_geometry", None)
        else:
            self._data["window_geometry"] = value
        self.save()
