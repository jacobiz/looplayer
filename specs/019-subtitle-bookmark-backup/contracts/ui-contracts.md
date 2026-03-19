# UI Contracts: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Phase 1 output** | **Date**: 2026-03-19 | **Branch**: `019-subtitle-bookmark-backup`

---

## F-202: subtitle_parser.py パブリック API

### `parse_srt(text: str) -> list[SubtitleEntry]`

SRT 形式の字幕テキストをパースして `SubtitleEntry` のリストを返す。

| 入力 | 型 | 説明 |
|------|----|------|
| `text` | `str` | SRT ファイルの全文（デコード済み） |

| 出力 | 型 | 説明 |
|------|----|------|
| 戻り値 | `list[SubtitleEntry]` | パース結果（空ファイルの場合は空リスト） |

**契約**:
- タイムスタンプ形式 `HH:MM:SS,mmm --> HH:MM:SS,mmm` を ms 変換して返す
- 複数行テキストは改行を空白で結合する
- ASS タグは除去しない（SRT に含まれる場合でも除去しない）
- パースエラーは無視してスキップ（例外を上位に伝播しない）

---

### `parse_ass(text: str) -> list[SubtitleEntry]`

ASS/SSA 形式の字幕テキストをパースして `SubtitleEntry` のリストを返す。

| 入力 | 型 | 説明 |
|------|----|------|
| `text` | `str` | ASS ファイルの全文（デコード済み） |

| 出力 | 型 | 説明 |
|------|----|------|
| 戻り値 | `list[SubtitleEntry]` | パース結果（`Dialogue:` 行のみ対象） |

**契約**:
- タイムスタンプ形式 `H:MM:SS.cc`（センチ秒）を ms 変換して返す
- `{...}` 形式の装飾タグをすべて除去してテキストを返す（FR-003）
- `Comment:` 行は無視する
- パースエラーは無視してスキップ

---

### `parse_subtitle_file(path: Path) -> list[SubtitleEntry]`

ファイルパスから字幕をパースする統合関数。エンコーディング自動検出付き。

| 入力 | 型 | 説明 |
|------|----|------|
| `path` | `Path` | 字幕ファイルパス（`.srt` / `.ass` / `.ssa`） |

| 出力 | 型 | 説明 |
|------|----|------|
| 戻り値 | `list[SubtitleEntry]` | パース結果 |
| 例外 | `ValueError` | エンコーディング非対応（UTF-8・cp932 ともに失敗） |
| 例外 | `ValueError` | 非対応の拡張子 |

**契約**:
- まず UTF-8 でデコードを試み、`UnicodeDecodeError` なら cp932 で再試行
- 両方失敗した場合は `ValueError("encoding")` を raise
- 拡張子が `.srt` → `parse_srt()`、`.ass` / `.ssa` → `parse_ass()` を呼ぶ

---

### `entries_to_bookmarks(entries: list[SubtitleEntry], start_order: int = 0) -> BulkAddResult`

`SubtitleEntry` のリストを `LoopBookmark` のリストに変換する。

| 入力 | 型 | 説明 |
|------|----|------|
| `entries` | `list[SubtitleEntry]` | パース済み字幕エントリ |
| `start_order` | `int` | 最初のブックマークに付与する `order` 値 |

| 出力 | 型 | 説明 |
|------|----|------|
| 戻り値 | `BulkAddResult` | 追加ブックマーク一覧・件数・スキップ件数 |

**契約**:
- `start_ms >= end_ms` のエントリをスキップし `skipped` カウントをインクリメント
- `text` が 80 文字超の場合は `text[:80] + "..."` に切り詰め（FR-005）
- 結果の `LoopBookmark` はすべて `enabled=True`, `repeat_count=1`, `pause_ms=0`

---

## F-402: data_backup.py パブリック API

### `create_backup(dest_path: Path, data_dir: Path | None = None) -> None`

`~/.looplayer/` 以下のデータを ZIP ファイルとして保存する。

| 入力 | 型 | 説明 |
|------|----|------|
| `dest_path` | `Path` | 保存先の ZIP ファイルパス（フルパス） |
| `data_dir` | `Path \| None` | データディレクトリ（テスト時に差し替え用; デフォルト `~/.looplayer/`） |

| 出力 | 型 | 説明 |
|------|----|------|
| 例外 | `BackupError` | データファイルが 1 件も存在しない |
| 例外 | `OSError` | 書き込み権限なし・ディスクフル等 |

**契約**:
- 対象ファイル: `bookmarks.json`, `settings.json`, `positions.json`, `recent_files.json`
- 各ファイルの存在確認後、存在するもののみを ZIP に含める
- `looplayer-backup.json`（マニフェスト）を最初に書き込む
- 全ファイルが存在しない場合は `BackupError` を raise して ZIP を作成しない

---

### `restore_backup(zip_path: Path, data_dir: Path | None = None) -> None`

ZIP ファイルからデータを `~/.looplayer/` に復元する。

| 入力 | 型 | 説明 |
|------|----|------|
| `zip_path` | `Path` | 復元元の ZIP ファイルパス |
| `data_dir` | `Path \| None` | 復元先ディレクトリ（テスト時差し替え用; デフォルト `~/.looplayer/`） |

| 出力 | 型 | 説明 |
|------|----|------|
| 例外 | `BackupError` | looplay! バックアップでない（マニフェスト不正） |
| 例外 | `BackupError` | ZIP が破損している |
| 例外 | `OSError` | 書き込み権限なし |

**契約**:
- ZIP を開いた直後にマニフェストを読み込み `app_name == "looplay!"` を検証（FR-014）
- 検証失敗または ZIP 破損（`BadZipFile`）は既存データを変更せず `BackupError` を raise
- 検証成功後に `data_dir` へ各ファイルを上書き展開（復元操作は atomic でなくてよい）
- `OSError` は呼び出し元に伝播（player.py でキャッチしてエラーメッセージ表示）

---

### `generate_backup_filename() -> str`

現在時刻から ZIP ファイル名を生成する。

| 出力 | 説明 |
|------|----|
| `str` | `"looplayer-backup-YYYYMMDD-HHMMSS.zip"` 形式の文字列 |

---

### `BackupError`

バックアップ・復元の業務エラー用例外クラス。

```python
class BackupError(Exception):
    pass
```

**使用箇所**: データなし・マニフェスト不正・ZIP 破損など、業務上の「想定エラー」に使う。
`OSError` は IO 系の「システムエラー」として区別して伝播する。

---

## player.py に追加するハンドラ（メニューアクション）

### `_generate_bookmarks_from_subtitles() -> None`

「字幕からブックマーク生成」メニューアクション。

**処理フロー**:
1. `self._external_subtitle_path` が `None` → エラーメッセージ表示して終了（FR-001）
2. `parse_subtitle_file(path)` でパース（エンコーディングエラー → エラーメッセージ表示）
3. `entries_to_bookmarks()` でブックマーク変換
4. `self.store.add_many(video_path, bookmarks)` で追加
5. `self.bookmark_panel.refresh()` で UI 更新
6. `self.bookmark_panel.set_last_bulk_add(result.bookmarks)` で Undo 用に保持
7. 完了メッセージ表示（FR-007）

### `_backup_data() -> None`

「データをバックアップ...」メニューアクション。

**処理フロー**:
1. ファイル保存ダイアログでパスを取得
2. `create_backup(dest_path)` を呼び出す
3. 成功 → 完了メッセージ表示
4. `BackupError` → データなしメッセージ表示
5. `OSError` → 書き込みエラーメッセージ表示

### `_restore_data() -> None`

「データを復元...」メニューアクション。

**処理フロー**:
1. ファイル選択ダイアログで ZIP パスを取得
2. 確認ダイアログ表示（FR-013）
3. ユーザーが「いいえ」→ 中断
4. `restore_backup(zip_path)` を呼び出す
5. `BackupError` → エラーメッセージ表示（非対応ファイル or 破損）
6. `OSError` → 書き込みエラーメッセージ表示
7. 成功 → 完了メッセージ表示後 `QApplication.quit()`（FR-015）

