# UI Contracts: 再生速度拡張・ミラー表示（F-101 / F-203）

## US1: 速度連続微調整（Shift+[/Shift+]）

### VideoPlayer._speed_fine_up()

| 項目 | 内容 |
|---|---|
| トリガー | `Shift+]` ショートカット |
| 事前条件 | なし（動画未再生でも設定可能） |
| 処理 | `round(self._playback_rate + 0.05, 2)` を計算し、`min(3.0, ...)` でクリップして `_set_playback_rate()` を呼ぶ |
| 上限到達時 | `status.max_speed` メッセージをステータスバーに 2000ms 表示 |
| 事後条件 | `self._playback_rate` が更新され、速度メニューのチェック状態が最近接の固定段階に更新される（完全一致なければチェックなし） |

### VideoPlayer._speed_fine_down()

| 項目 | 内容 |
|---|---|
| トリガー | `Shift+[` ショートカット |
| 処理 | `round(self._playback_rate - 0.05, 2)` を計算し、`max(0.25, ...)` でクリップして `_set_playback_rate()` を呼ぶ |
| 下限到達時 | `status.min_speed` メッセージをステータスバーに 2000ms 表示 |

---

## US2: 速度段階メニュー（10段階）

### 速度メニュー構成

| 項目 | 内容 |
|---|---|
| 段階数 | 10（0.25 / 0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 1.75 / 2.0 / 2.5 / 3.0） |
| チェック状態 | `_set_playback_rate()` 呼び出し時に `action.data() == rate` で更新 |
| 初期チェック | 1.0x |

---

## US3: ミラー表示トグル

### VideoPlayer._toggle_mirror_display()

| 項目 | 内容 |
|---|---|
| トリガー | 「表示 > 左右反転」メニューアクション |
| 処理 | `self._app_settings.mirror_display` を反転 → `mirror_action.setChecked(...)` → 再生中なら現在位置を保持して `_open_path` 相当でメディア再生成 |
| 事後条件 | 映像が即座に反転/復元される。設定が `settings.json` に永続化される |

### AppSettings.mirror_display プロパティ

| 項目 | 内容 |
|---|---|
| getter | `bool(self._data.get("mirror_display", False))` |
| setter | `self._data["mirror_display"] = value` → `self.save()` |

### _open_path() 内のミラー適用

| 条件 | 処理 |
|---|---|
| `mirror_display == True` | `media.add_option(':video-filter=transform')` + `media.add_option(':transform-type=hflip')` をメディア生成直後に呼ぶ |
| `mirror_display == False` | オプション付加なし（通常通り） |

---

## テスト境界条件

| シナリオ | 期待値 |
|---|---|
| 速度 3.0x で `_speed_fine_up()` | 速度は 3.0x のまま。ステータスバーに max_speed メッセージ |
| 速度 0.25x で `_speed_fine_down()` | 速度は 0.25x のまま。ステータスバーに min_speed メッセージ |
| 速度 0.28x で `_speed_fine_up()` | 速度は `round(0.28+0.05, 2)` = 0.33x |
| ミラー OFF → ファイル変更 | ミラー OFF のまま次の動画を開く |
| ミラー ON → ファイル変更 | ミラー ON のまま次の動画を開く |
| ミラー ON → アプリ再起動 | 起動時 `mirror_display=True` を読み込みミラー有効で動作 |
