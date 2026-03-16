# Data Model: プレイヤー機能強化

**Branch**: `007-player-enhancements` | **Date**: 2026-03-16

---

## 既存エンティティの変更

### LoopBookmark（変更）

`looplayer/bookmark_store.py` の `LoopBookmark` データクラスに `notes` フィールドを追加する。

```python
@dataclass
class LoopBookmark:
    point_a_ms: int
    point_b_ms: int
    name: str = ""
    repeat_count: int = 1
    order: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    notes: str = ""          # ← 新規追加
```

**制約**:
- `notes` は任意のテキスト文字列。長さ制限なし（UIはダイアログの入力フォームで自然に制限される）
- デフォルト `""` で後方互換性を維持（旧 `bookmarks.json` に `notes` キーがなくても正常読み込み）

**bookmarks.json への影響**:
```json
{
  "/path/to/video.mp4": [
    {
      "id": "uuid",
      "name": "重要フレーズ",
      "point_a_ms": 12000,
      "point_b_ms": 15000,
      "repeat_count": 3,
      "order": 0,
      "enabled": true,
      "notes": "「ありがとう」のイントネーション確認"
    }
  ]
}
```

### bookmark_io.py エクスポートスキーマ（変更）

エクスポート JSON の `bookmarks` リスト各エントリに `notes` フィールドを追加する。インポート時は `notes` がないエントリは `""` にフォールバック。

---

## 新規エンティティ

### PlaybackPosition

**モジュール**: `looplayer/playback_position.py`（新規）
**永続化**: `~/.looplayer/positions.json`

```python
# 論理モデル: ファイルパス → 再生位置(ms) の辞書
# Python 3.7+ の dict は挿入順を保持するため「最近アクセス順」として使える

# positions.json の形式
{
    "/path/to/video1.mp4": 12300,
    "/path/to/video2.mkv": 45600
}
```

**フィールド**（辞書の各エントリ）:
- **key** (`str`): 動画ファイルの絶対パス
- **value** (`int`): 再生位置（ミリ秒）

**制約・ルール**:
- 最大 10 件保持。11 件目を追加する際は最も古いエントリを削除する
- 保存しない条件（FR-023）:
  - 再生位置が総再生時間の 95% 以上（見終わった）
  - 再生開始から 5 秒未満（先頭とほぼ同じ）
- ファイルが存在しない場合はエントリを無視する

**PublicAPI**:
```python
class PlaybackPosition:
    def save(self, filepath: str, position_ms: int, duration_ms: int) -> None: ...
    def load(self, filepath: str) -> int | None: ...  # 記録なし → None
```

---

### Playlist

**モジュール**: `looplayer/playlist.py`（新規）
**永続化**: なし（セッション中のみ）

```python
@dataclass
class Playlist:
    files: list[Path]   # ファイル名順でソート済みの動画ファイルリスト
    index: int = 0      # 現在再生中のインデックス
```

**フィールド**:
- **files** (`list[Path]`): フォルダドロップで生成される動画ファイルパスのリスト（ファイル名昇順）
- **index** (`int`): 現在再生中ファイルのインデックス（0-based）

**状態遷移**:
```
初期生成（フォルダドロップ）
    ↓
current() → files[index] を再生
    ↓
advance() → index += 1
    ↓ [index < len(files)]     ↓ [index >= len(files)]
current() で次ファイル      has_next() = False → 再生停止
```

**PublicAPI**:
```python
class Playlist:
    def current(self) -> Path: ...
    def advance(self) -> bool: ...    # 次がある → True、なければ False
    def has_next(self) -> bool: ...
    def __len__(self) -> int: ...
```

---

### AppSettings

**モジュール**: `looplayer/app_settings.py`（新規）
**永続化**: `~/.looplayer/settings.json`

```json
{
    "end_of_playback_action": "stop"
}
```

**フィールド**:
- **end_of_playback_action** (`str`): `"stop"` / `"rewind"` / `"loop"` のいずれか。デフォルト `"stop"`

**制約**:
- 不正値が含まれる場合はデフォルト `"stop"` にフォールバック
- 書き込みは既存のアトミックパターン（`.tmp` → `rename`）を使用

**PublicAPI**:
```python
class AppSettings:
    @property
    def end_of_playback_action(self) -> str: ...
    @end_of_playback_action.setter
    def end_of_playback_action(self, value: str) -> None: ...
    def save(self) -> None: ...

    # デフォルト値
    END_OF_PLAYBACK_ACTIONS = ("stop", "rewind", "loop")
    DEFAULT_END_OF_PLAYBACK_ACTION = "stop"
```

---

## ファイル一覧（永続化）

| ファイル | 内容 | 管理 |
|---------|------|------|
| `~/.looplayer/bookmarks.json` | ブックマーク（`notes` フィールド追加） | 既存・変更 |
| `~/.looplayer/recent_files.json` | 最近開いたファイル | 既存・変更なし |
| `~/.looplayer/positions.json` | 再生位置の記憶 | **新規** |
| `~/.looplayer/settings.json` | アプリ設定（再生終了動作等） | **新規** |
