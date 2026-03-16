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
