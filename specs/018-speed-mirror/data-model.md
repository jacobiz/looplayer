# Data Model: 再生速度拡張・ミラー表示（F-101 / F-203）

## 変更エンティティ

### AppSettings（既存、拡張）

`~/.looplayer/settings.json` に新規フィールドを追加する。

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `mirror_display` | `bool` | `False` | 左右反転表示の永続化状態 |

**変更なし**: `end_of_playback_action`, `check_update_on_startup`, `sequential_play_mode`, `export_encode_mode`, `window_geometry`, `onboarding_shown`

**注意**: 再生速度（`_playback_rate`）は AppSettings に保存しない。起動時は常に 1.0x。

---

### _PLAYBACK_RATES（定数、変更）

`looplayer/player.py` のモジュール定数。

| 変更前（6段階） | 変更後（10段階） |
|---|---|
| `[0.5, 0.75, 1.0, 1.25, 1.5, 2.0]` | `[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]` |

`_speed_up()`/`_speed_down()` はこのリストのインデックス操作で動作するため、リスト変更だけで `[`/`]` キーおよび速度メニューの両方に反映される。

---

## 新規追加（ランタイム状態、永続化なし）

| 項目 | 型 | 場所 | 説明 |
|---|---|---|---|
| `_playback_rate` | `float` | `VideoPlayer` インスタンス変数（既存） | 0.25〜3.0 の範囲に拡張。初期値 1.0、永続化なし |

---

## i18n キー（新規追加）

| キー | 日本語 | 英語 |
|---|---|---|
| `menu.view.mirror_display` | 左右反転 | Mirror Display |
| `status.speed_fine_up` | 速度 +0.05x | Speed +0.05x |
| `status.speed_fine_down` | 速度 -0.05x | Speed -0.05x |
