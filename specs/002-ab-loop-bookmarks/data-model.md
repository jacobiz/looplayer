# Data Model: AB Loop Bookmarks & Sequential Playback

**Feature**: 002-ab-loop-bookmarks
**Date**: 2026-03-15

---

## エンティティ

### LoopBookmark

1つの AB ループ区間を表すデータクラス。

| フィールド | 型 | 制約 | 説明 |
|-----------|-----|------|------|
| `id` | `str` | UUID、不変、一意 | ブックマームの識別子 |
| `name` | `str` | 空の場合はデフォルト名を使用 | 表示名（ユーザー設定） |
| `point_a_ms` | `int` | >= 0、< point_b_ms | A点のタイムスタンプ（ミリ秒） |
| `point_b_ms` | `int` | > point_a_ms、<= 動画長 | B点のタイムスタンプ（ミリ秒） |
| `repeat_count` | `int` | >= 1、デフォルト 1 | 連続再生時の繰り返し回数 |
| `order` | `int` | >= 0、一覧内で一意 | 表示・再生順序のインデックス |

**バリデーションルール**:
- `point_a_ms < point_b_ms` でなければ保存を拒否（FR-011）
- `point_b_ms` が動画長を超える場合は保存を拒否（FR-011）
- `name` が空文字列の場合、`"ブックマーク {n}"` を自動設定（n = 1始まりの連番）

---

### BookmarkStore

動画ファイルパスをキーとして `LoopBookmark` のリストを管理し、JSONファイルへの永続化を担う。

**ストレージ**:
- ファイルパス: `~/.looplayer/bookmarks.json`
- フォーマット: `{ "絶対ファイルパス": [ LoopBookmark, ... ] }`
- キー: 動画ファイルの絶対パス文字列（ファイル移動・リネームで孤立）

**操作**:
| 操作 | 説明 |
|------|------|
| `load(video_path)` | 指定動画のブックマーク一覧をJSONから読み込む |
| `save(video_path, bookmarks)` | 指定動画のブックマーク一覧を永続化する |
| `add(video_path, bookmark)` | ブックマークを追加して永続化 |
| `delete(video_path, bookmark_id)` | IDでブックマークを削除して永続化 |
| `update_order(video_path, ordered_ids)` | 並び順をID列で更新して永続化 |

---

### SequentialPlayState

連続再生の進行状態を表す一時オブジェクト（メモリ上のみ、永続化不要）。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `bookmarks` | `list[LoopBookmark]` | 再生対象のブックマームリスト（順序付き） |
| `current_index` | `int` | 現在再生中のブックマークのインデックス |
| `remaining_repeats` | `int` | 現在区間の残り繰り返し回数 |
| `active` | `bool` | 連続再生中かどうか |

**状態遷移**:
```
初期化: current_index=0, remaining_repeats=bookmarks[0].repeat_count, active=True
B点到達時:
  remaining_repeats -= 1
  if remaining_repeats > 0:
    → A点に戻る（同区間を繰り返す）
  else:
    current_index += 1
    if current_index >= len(bookmarks):
      current_index = 0  # 先頭に戻る
    remaining_repeats = bookmarks[current_index].repeat_count
    → 新しい区間のA点に移動
停止時:
  active = False
  → 通常再生モードに戻る
```

---

## ストレージスキーマ（JSON）

```json
{
  "/home/user/videos/lesson.mp4": [
    {
      "id": "a1b2c3d4-e5f6-...",
      "name": "サビ部分",
      "point_a_ms": 62000,
      "point_b_ms": 78000,
      "repeat_count": 3,
      "order": 0
    },
    {
      "id": "b2c3d4e5-f6a7-...",
      "name": "Aメロ",
      "point_a_ms": 10000,
      "point_b_ms": 30000,
      "repeat_count": 1,
      "order": 1
    }
  ]
}
```
