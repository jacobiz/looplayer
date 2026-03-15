"""ユーティリティ関数。"""


def _ms_to_str(ms) -> str:
    if ms is None or ms < 0:
        return "00:00"
    s = ms // 1000
    minutes, seconds = divmod(s, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
