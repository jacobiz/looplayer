# Data Model: プレイヤー UX 改善

**Branch**: `004-player-ux` | **Date**: 2026-03-15

---

## 既存エンティティ（変更なし）

### LoopBookmark (`looplayer/bookmark_store.py`)

| フィールド | 型 | 制約 |
|-----------|-----|------|
| `id` | `str` (UUID4) | 必須・一意 |
| `name` | `str` | デフォルト `"ブックマーク N"` |
| `point_a_ms` | `int` | `point_a_ms < point_b_ms` |
| `point_b_ms` | `int` | `<= video_length_ms` (0 の場合スキップ) |
| `repeat_count` | `int` | `>= 1` |
| `order` | `int` | `0` 始まり; `add()` 時に自動採番 |

---

## 新規エンティティ

### RecentFiles

**保存先**: `~/.looplayer/recent_files.json`
**実装クラス**: `looplayer/recent_files.py` に `RecentFiles` クラスを追加

#### JSON スキーマ

```json
{
  "files": [
    "/path/to/video.mp4",
    "/path/to/other.mkv"
  ]
}
```

#### フィールド定義

| フィールド | 型 | 制約 |
|-----------|-----|------|
| `files` | `list[str]` | 最大 10 件。先頭が最新。重複なし |

#### 状態遷移

1. **ファイルを開く** → 先頭に追加（同パスが既存の場合は既存を削除してから先頭挿入）→ 11件目以降は末尾削除
2. **ファイルを選択（存在しない）** → 選択エントリを削除 → エラーメッセージ表示
3. **アトミック書き込み**: `tmp → replace()` パターン（`BookmarkStore._save_all` と同一）

---

### DeletedBookmark（一時エンティティ）

**保存先**: メモリのみ（`BookmarkPanel._pending_delete`）
**永続化**: なし（アプリ終了で消滅 = 削除確定）

#### フィールド定義

| フィールド | 型 | 用途 |
|-----------|-----|------|
| `bookmark` | `LoopBookmark` | 削除されたブックマーク本体 |
| `original_index` | `int` | 削除前の `order` インデックス |

#### 状態遷移

```
[削除ボタン押下]
    │
    ▼
 _pending_delete に保存
 BookmarkStore.delete() 呼び出し
 _undo_timer.start(5000ms)
    │
    ├─[Ctrl+Z / 5秒以内]─▶ _undo_delete(): store.add() → update_order() で元位置復元 → タイマー停止
    │
    ├─[5秒経過]──────────▶ _commit_delete(): _pending_delete = None
    │
    └─[次の削除 / 動画切替]─▶ _commit_delete() → 新しい _pending_delete セット
```

---

### BookmarkExport（エクスポートスキーマ）

**実装**: `looplayer/bookmark_io.py`（新規ファイル）

#### JSON スキーマ

```json
{
  "version": 1,
  "exported_at": "2026-03-15T12:00:00+00:00",
  "bookmarks": [
    {
      "name": "サビ部分",
      "point_a_ms": 1000,
      "point_b_ms": 5000,
      "repeat_count": 3,
      "order": 0
    }
  ]
}
```

#### フィールド定義

| フィールド | 型 | 制約 |
|-----------|-----|------|
| `version` | `int` | 固定値 `1` |
| `exported_at` | `str` (ISO 8601) | `datetime.now(timezone.utc).isoformat()` |
| `bookmarks[].name` | `str` | — |
| `bookmarks[].point_a_ms` | `int` | `> 0` |
| `bookmarks[].point_b_ms` | `int` | `> point_a_ms` |
| `bookmarks[].repeat_count` | `int` | `>= 1` |
| `bookmarks[].order` | `int` | `>= 0` |

#### 設計上の決定

- `id` フィールドはエクスポートに含めない（インポート先で新規 UUID を発行）
- 動画ファイルパスもスキーマに含めない（インポート先の「現在の動画」に追加）
- 重複チェック: `(point_a_ms, point_b_ms)` ペアの set を使用
- バリデーション: `int()` キャストで型を明示（JSON の `float` 混入対策）

---

## ファイル永続化サマリー

| ファイル | 管理クラス | 書き込みパターン |
|---------|-----------|----------------|
| `~/.looplayer/bookmarks.json` | `BookmarkStore` | `tmp → replace()` アトミック |
| `~/.looplayer/recent_files.json` | `RecentFiles` | `tmp → replace()` アトミック（同一パターン） |
| エクスポート先（任意パス） | `bookmark_io.export_bookmarks()` | `open("w")` 直書き（上書き確認はダイアログで実施） |
