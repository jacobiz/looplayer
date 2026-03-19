# Data Model: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Phase 1 output** | **Date**: 2026-03-19 | **Branch**: `019-subtitle-bookmark-backup`

---

## F-202: 字幕エントリ

### SubtitleEntry

字幕ファイルの 1 行エントリ。パーサーの出力単位。`LoopBookmark` への変換入力。

| フィールド | 型 | 説明 | バリデーション |
|------------|-----|------|----------------|
| `start_ms` | `int` | 字幕開始時刻（ミリ秒） | 0 以上 |
| `end_ms` | `int` | 字幕終了時刻（ミリ秒） | 0 以上 |
| `text` | `str` | 字幕テキスト（タグ除去済み） | 空文字でも可（スキップ対象にはならない） |

**バリデーション規則**:
- `start_ms >= end_ms` の場合は無効エントリ → スキップ（FR-004）
- `text` が 80 文字超の場合は先頭 80 文字 + `...` に切り詰め（FR-005）
- `text` が空文字列の場合は名前なしブックマークとして登録する

**状態遷移**: パーサー入力 → SubtitleEntry（検証前） → 有効 or スキップ

---

## F-202: ブックマーク一括生成操作

### BulkAddResult

一括生成操作の結果を保持する。完了メッセージの生成に使用。

| フィールド | 型 | 説明 |
|------------|-----|------|
| `added` | `int` | 登録されたブックマーク件数 |
| `skipped` | `int` | スキップされたエントリ件数（`start_ms >= end_ms`） |
| `bookmarks` | `list[LoopBookmark]` | 追加されたブックマーク一覧（Undo 用に保持） |

---

## F-402: バックアップアーカイブ

### BackupManifest

ZIP ファイル内の `looplayer-backup.json` に格納されるメタデータ。

| フィールド | 型 | 説明 | 例 |
|------------|-----|------|-----|
| `app_name` | `str` | アプリ識別子（固定値） | `"looplay!"` |
| `app_version` | `str` | バックアップ作成時のアプリバージョン | `"1.8.1"` |
| `created_at` | `str` | ISO 8601 形式の作成日時（UTC） | `"2026-03-19T12:34:56"` |
| `files` | `list[str]` | ZIP に含まれるデータファイル名一覧 | `["bookmarks.json", "settings.json"]` |

**識別規則**: `app_name == "looplay!"` でなければ非対応ファイルと判定（FR-014）

**JSON スキーマ例**:
```json
{
  "app_name": "looplay!",
  "app_version": "1.8.1",
  "created_at": "2026-03-19T12:34:56",
  "files": ["bookmarks.json", "settings.json", "positions.json", "recent_files.json"]
}
```

### BackupArchive（論理エンティティ）

ZIP ファイル全体を表す論理エンティティ。コードでは `zipfile.ZipFile` として扱う。

| 構成要素 | 内容 |
|----------|------|
| マニフェスト | `looplayer-backup.json`（必須） |
| データファイル | `bookmarks.json`, `settings.json`, `positions.json`, `recent_files.json`（存在するもののみ） |

**ファイル名形式**: `looplayer-backup-YYYYMMDD-HHMMSS.zip`

---

## 既存エンティティとの関係

```
SubtitleEntry ──(変換)──► LoopBookmark (既存)
                               │
                               ▼
                         BookmarkStore (既存: bookmarks.json)

BackupManifest ──(含む)──► BackupArchive (ZIP)
                               │
                        ┌──────┴──────┐
                        ▼             ▼
                  bookmarks.json   settings.json
                  positions.json   recent_files.json
```

---

## `LoopBookmark` への変換ルール（F-202）

| SubtitleEntry フィールド | → LoopBookmark フィールド | 変換ルール |
|--------------------------|---------------------------|------------|
| `start_ms` | `point_a_ms` | そのまま |
| `end_ms` | `point_b_ms` | そのまま |
| `text`（切り詰め済み） | `name` | 先頭 80 文字 + `...`（超過時） |
| — | `repeat_count` | デフォルト値 `1` |
| — | `enabled` | `True` |
| — | `order` | 既存最大 `order + 1` から連番 |
| — その他 | デフォルト値 | `notes=""`, `pause_ms=0`, `play_count=0`, `tags=[]` |

