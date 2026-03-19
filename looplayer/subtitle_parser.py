"""
字幕パーサー: SRT/ASS 形式の字幕ファイルを解析して SubtitleEntry のリストを返す。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from looplayer.bookmark_store import LoopBookmark

# 字幕テキストの最大文字数（FR-005）
_MAX_TEXT_LEN = 80


# ── データクラス ──────────────────────────────────────────────

@dataclass
class SubtitleEntry:
    """字幕の 1 エントリ。パーサーの出力単位。"""
    start_ms: int
    end_ms: int
    text: str


@dataclass
class BulkAddResult:
    """一括生成操作の結果。"""
    added: int
    skipped: int
    bookmarks: list[LoopBookmark] = field(default_factory=list)


# ── SRT パーサー ──────────────────────────────────────────────

_SRT_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def _ts_to_ms(h: str, m: str, s: str, ms: str) -> int:
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)


def parse_srt(text: str) -> list[SubtitleEntry]:
    """SRT 形式のテキストをパースして SubtitleEntry のリストを返す。"""
    entries: list[SubtitleEntry] = []
    # 空行でブロックを分割
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        # タイムスタンプ行を探す（連番行の次とは限らないため全行スキャン）
        ts_match: re.Match | None = None
        ts_line_idx = -1
        for i, line in enumerate(lines):
            m = _SRT_TIMESTAMP_RE.search(line)
            if m:
                ts_match = m
                ts_line_idx = i
                break
        if ts_match is None or ts_line_idx < 0:
            continue
        start_ms = _ts_to_ms(*ts_match.group(1, 2, 3, 4))
        end_ms = _ts_to_ms(*ts_match.group(5, 6, 7, 8))
        text_lines = lines[ts_line_idx + 1:]
        entry_text = " ".join(l.strip() for l in text_lines if l.strip())
        entries.append(SubtitleEntry(start_ms=start_ms, end_ms=end_ms, text=entry_text))
    return entries


# ── ASS パーサー ──────────────────────────────────────────────

_ASS_TS_RE = re.compile(
    r"(\d+):(\d{2}):(\d{2})\.(\d{2})"
)
_ASS_TAG_RE = re.compile(r"\{[^}]*\}")


def _ass_ts_to_ms(h: str, m: str, s: str, cs: str) -> int:
    """ASS タイムスタンプ（センチ秒）を ms に変換。"""
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(cs) * 10


def parse_ass(text: str) -> list[SubtitleEntry]:
    """ASS/SSA 形式のテキストをパースして SubtitleEntry のリストを返す。"""
    entries: list[SubtitleEntry] = []
    in_events = False
    format_map: dict[str, int] = {}

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[Events]":
            in_events = True
            continue
        if not in_events:
            continue
        if stripped.startswith("[") and stripped != "[Events]":
            in_events = False
            continue
        if stripped.startswith("Format:"):
            cols = [c.strip() for c in stripped[len("Format:"):].split(",")]
            format_map = {name: idx for idx, name in enumerate(cols)}
            continue
        if not stripped.startswith("Dialogue:"):
            continue
        # Format: 行がない異常 ASS は Dialogue: をスキップ
        if not format_map:
            continue
        # Dialogue: 行をパース
        parts = stripped[len("Dialogue:"):].split(",", maxsplit=len(format_map) - 1)
        if len(parts) < len(format_map):
            continue
        try:
            start_str = parts[format_map["Start"]].strip()
            end_str = parts[format_map["End"]].strip()
            text_val = parts[format_map["Text"]] if "Text" in format_map else parts[-1]
        except (KeyError, IndexError):
            continue
        m_start = _ASS_TS_RE.match(start_str)
        m_end = _ASS_TS_RE.match(end_str)
        if not m_start or not m_end:
            continue
        start_ms = _ass_ts_to_ms(*m_start.group(1, 2, 3, 4))
        end_ms = _ass_ts_to_ms(*m_end.group(1, 2, 3, 4))
        # 装飾タグ除去（FR-003）
        clean_text = _ASS_TAG_RE.sub("", text_val).strip()
        entries.append(SubtitleEntry(start_ms=start_ms, end_ms=end_ms, text=clean_text))
    return entries


# ── ファイル読み込み ───────────────────────────────────────────

def parse_subtitle_file(path: Path) -> list[SubtitleEntry]:
    """ファイルパスから字幕をパースする。エンコーディングを自動検出する。

    Raises:
        ValueError: エンコーディング非対応またはサポート外の拡張子。
    """
    ext = path.suffix.lower()
    if ext not in (".srt", ".ass", ".ssa"):
        raise ValueError(f"サポートされていない字幕形式: {ext}")

    raw: str | None = None
    for encoding in ("utf-8", "cp932"):
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raise ValueError(f"encoding: {path} のエンコーディングを認識できませんでした")

    if ext == ".srt":
        return parse_srt(raw)
    return parse_ass(raw)


# ── 変換 ─────────────────────────────────────────────────────

def entries_to_bookmarks(
    entries: list[SubtitleEntry],
    start_order: int = 0,
) -> BulkAddResult:
    """SubtitleEntry のリストを LoopBookmark のリストに変換する。

    start_ms >= end_ms のエントリはスキップする（FR-004）。
    テキストは 80 文字を超える場合は切り詰める（FR-005）。
    """
    bookmarks: list[LoopBookmark] = []
    skipped = 0
    for i, entry in enumerate(entries):
        if entry.start_ms >= entry.end_ms:
            skipped += 1
            continue
        name = entry.text
        if len(name) > _MAX_TEXT_LEN:
            # 結果は _MAX_TEXT_LEN + 3 = 83 文字になる（FR-005: 80文字超を切り詰め + "..." を付加）
            name = name[:_MAX_TEXT_LEN] + "..."
        bookmarks.append(
            LoopBookmark(
                point_a_ms=entry.start_ms,
                point_b_ms=entry.end_ms,
                name=name,
                order=start_order + len(bookmarks),
            )
        )
    return BulkAddResult(added=len(bookmarks), skipped=skipped, bookmarks=bookmarks)
