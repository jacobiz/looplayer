# Data Model: ビデオプレイヤーコア機能

**Date**: 2026-03-15
**Branch**: 001-video-player-core

## エンティティ一覧

このアプリはファイル永続化を持たないため、すべての状態はメモリ上のインスタンス変数として管理される。

---

### PlaybackSession（再生セッション）

`VideoPlayer` インスタンス内の状態として保持される。

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `media_player` | vlc.MediaPlayer | 起動時生成 | VLC メディアプレイヤー本体 |
| `instance` | vlc.Instance | 起動時生成 | VLC インスタンス |

**状態遷移**:

```
[未読込] --open_file()--> [再生中]
[再生中] --toggle_play()--> [一時停止]
[一時停止] --toggle_play()--> [再生中]
[再生中|一時停止] --stop()--> [停止]
[停止] --toggle_play()--> [再生中]
[再生中] --終端到達--> [停止]
[再生中] --open_file(エラー)--> [再生中]（状態維持）
```

**バリデーション**:
- ファイルが未読込の状態でのシーク・A点B点セットは無効操作（何も起こらない）
- ファイルが開けない場合（エラーイベント発火）は直前状態を維持する

---

### ABSegment（AB区間）

`VideoPlayer` インスタンス内の状態として保持される。

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `ab_point_a` | int \| None | None | A点の時刻（ミリ秒）|
| `ab_point_b` | int \| None | None | B点の時刻（ミリ秒）|
| `ab_loop_active` | bool | False | ABループ有効フラグ |

**ループ発動条件**（全て満たす場合のみ）:
1. `ab_loop_active is True`
2. `ab_point_a is not None`
3. `ab_point_b is not None`
4. `current_ms >= ab_point_b`

**リセット条件**:
- 新しいファイルを開いたとき（`open_file()` 呼び出し時）
- ユーザーが「ABリセット」ボタンを押したとき

**状態遷移**:

```
[未設定: a=None, b=None, active=False]
  --set_point_a()--> [A設定: a=t, b=None, active=False]
  --set_point_b()--> [B設定: a=None, b=t, active=False]
  --set_point_a() + set_point_b()--> [AB設定: a=t1, b=t2, active=False]
  --toggle_ab_loop(True)--> [AB設定: a=t1, b=t2, active=True]
  --reset_ab() | open_file()--> [未設定]
```

---

## 補足: 時刻表現

- すべての時刻はミリ秒 (`int`) で内部管理する
- 表示用フォーマット: `_ms_to_str(ms: int) -> str`
  - `< 3600000ms` → `"MM:SS"`
  - `>= 3600000ms` → `"HH:MM:SS"`
  - `None` または `< 0` → `"00:00"`
