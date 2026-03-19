# Quickstart: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Phase 1 output** | **Date**: 2026-03-19 | **Branch**: `019-subtitle-bookmark-backup`

---

## F-202: 字幕からブックマーク生成の動作確認シナリオ

### シナリオ 1: SRT ファイルから正常生成

```python
# テスト用 SRT テキスト（3 エントリ）
srt_text = """\
1
00:00:01,000 --> 00:00:03,000
Hello, world!

2
00:00:04,000 --> 00:00:06,500
This is a subtitle.

3
00:00:07,000 --> 00:00:07,000
無効エントリ (A=B)
"""

entries = parse_srt(srt_text)
# → [SubtitleEntry(1000, 3000, "Hello, world!"),
#    SubtitleEntry(4000, 6500, "This is a subtitle."),
#    SubtitleEntry(7000, 7000, "無効エントリ (A=B)")]

result = entries_to_bookmarks(entries, start_order=0)
# result.added == 2
# result.skipped == 1
# result.bookmarks[0].point_a_ms == 1000
# result.bookmarks[0].point_b_ms == 3000
# result.bookmarks[0].name == "Hello, world!"
```

### シナリオ 2: ASS ファイルのタグ除去

```python
ass_text = """\
[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, ...
Style: Default,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\an8}{\\b1}こんにちは{\\b0}
Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,普通のテキスト
"""

entries = parse_ass(ass_text)
# entries[0].text == "こんにちは"  （タグ除去済み）
# entries[1].text == "普通のテキスト"
```

### シナリオ 3: テキスト 80 文字切り詰め

```python
long_text = "あ" * 90  # 90 文字
entry = SubtitleEntry(start_ms=0, end_ms=1000, text=long_text)
result = entries_to_bookmarks([entry])
# result.bookmarks[0].name == "あ" * 80 + "..."  （83 文字）
```

### シナリオ 4: Undo（一括生成取り消し）

```python
# 生成後
panel.set_last_bulk_add(result.bookmarks)
store.bookmarks_count == 5  # 既存 2 + 生成 3

# Ctrl+Z
panel.undo_bulk_add()
store.bookmarks_count == 2  # 生成分が削除される
```

---

## F-402: バックアップ・復元の動作確認シナリオ

### シナリオ 5: バックアップ作成

```python
# tmp_path を ~/.looplayer/ の代わりに使用（テスト）
data_dir = tmp_path / "looplayer"
data_dir.mkdir()
(data_dir / "bookmarks.json").write_text('{"v":1}')
(data_dir / "settings.json").write_text('{"v":1}')

zip_path = tmp_path / "backup.zip"
create_backup(zip_path, data_dir=data_dir)

import zipfile
with zipfile.ZipFile(zip_path) as z:
    names = z.namelist()
    assert "looplayer-backup.json" in names
    assert "bookmarks.json" in names
    assert "settings.json" in names

    manifest = json.loads(z.read("looplayer-backup.json"))
    assert manifest["app_name"] == "looplay!"
```

### シナリオ 6: 非対応 ZIP の検出

```python
# 通常の ZIP（マニフェストなし）
bad_zip = tmp_path / "bad.zip"
with zipfile.ZipFile(bad_zip, "w") as z:
    z.writestr("some_file.txt", "data")

with pytest.raises(BackupError):
    restore_backup(bad_zip, data_dir=data_dir)
# 既存データは変更されない
```

### シナリオ 7: バックアップ → 復元サイクル

```python
original_bookmarks = '{"version": 1, "items": [{"id": "abc"}]}'
(data_dir / "bookmarks.json").write_text(original_bookmarks)

# バックアップ作成
zip_path = tmp_path / "backup.zip"
create_backup(zip_path, data_dir=data_dir)

# データを破壊
(data_dir / "bookmarks.json").write_text("{}")

# 復元
restore_backup(zip_path, data_dir=data_dir)

# 元に戻っている
assert (data_dir / "bookmarks.json").read_text() == original_bookmarks
```

### シナリオ 8: データファイルなし

```python
empty_dir = tmp_path / "empty"
empty_dir.mkdir()

with pytest.raises(BackupError):
    create_backup(tmp_path / "out.zip", data_dir=empty_dir)
# ZIP ファイルは作成されない
```

---

## ファイルの役割まとめ

| ファイル | 役割 | 変更種別 |
|----------|------|----------|
| `looplayer/subtitle_parser.py` | SRT/ASS パース・`SubtitleEntry`/`BulkAddResult` 定義 | 新規 |
| `looplayer/data_backup.py` | ZIP バックアップ・復元・`BackupError` 定義 | 新規 |
| `looplayer/i18n.py` | F-202・F-402 用 UI 文字列追加 | 変更 |
| `looplayer/player.py` | メニュー項目追加・3 ハンドラ実装 | 変更 |
| `looplayer/widgets/bookmark_panel.py` | `set_last_bulk_add()` / `undo_bulk_add()` 追加 | 変更 |
| `looplayer/bookmark_store.py` | `add_many()` メソッド追加（または既存 `add()` を繰り返し呼び出し） | 変更（最小限） |
| `tests/unit/test_subtitle_parser.py` | `subtitle_parser.py` の全関数テスト | 新規 |
| `tests/unit/test_data_backup.py` | `data_backup.py` の全関数テスト | 新規 |
| `tests/integration/test_subtitle_bookmark_integration.py` | 字幕→ブックマーク統合テスト | 新規 |

