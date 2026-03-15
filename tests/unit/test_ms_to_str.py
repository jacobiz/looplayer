"""_ms_to_str ヘルパー関数のユニットテスト。"""
import pytest
from looplayer.utils import ms_to_str


@pytest.mark.parametrize("ms, expected", [
    (None,    "00:00"),   # None は 00:00
    (-1,      "00:00"),   # 負の値は 00:00
    (0,       "00:00"),   # 0ms
    (1000,    "00:01"),   # 1秒
    (60000,   "01:00"),   # 1分
    (61000,   "01:01"),   # 1分1秒
    (3599000, "59:59"),   # 59分59秒（1時間未満の境界）
    (3600000, "01:00:00"), # ちょうど1時間
    (3661000, "01:01:01"), # 1時間1分1秒
])
def test_ms_to_str(ms, expected):
    assert ms_to_str(ms) == expected
