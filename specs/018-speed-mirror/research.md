# Research: 再生速度拡張・ミラー表示（F-101 / F-203）

## F-101: 再生速度拡張

### Decision: `_PLAYBACK_RATES` リストを 10 段階に置き換える

- **Decision**: `_PLAYBACK_RATES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]`（6段階）を `[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]`（10段階）に変更する
- **Rationale**: `_speed_up`/`_speed_down` は `_PLAYBACK_RATES` リストを参照してインデックス操作するため、リスト変更だけで `[`/`]` キー・速度メニューの両方に反映される。変更箇所が1箇所で最もシンプル
- **Alternatives considered**: 固定段階を廃止して `Shift+[`/`Shift+]` に統合する案は `[`/`]` キーの使い勝手を損なうため却下

### Decision: `Shift+[`/`Shift+]` は 0.05x 刻みの微調整専用ショートカット

- **Decision**: `QShortcut(QKeySequence("Shift+["), self)` と `QKeySequence("Shift+]")` を追加。`_speed_fine_down()` / `_speed_fine_up()` メソッドで `round(rate ± 0.05, 2)` を計算してクリップ
- **Rationale**: 浮動小数点誤差を回避するために `round(..., 2)` を適用する。0.05 刻みの加算を繰り返すと `0.9999999...` のような誤差が蓄積するため必須
- **Alternatives considered**: 固定ステップテーブルを別途持つ案は管理コストが増えるため却下。`round(..., 2)` による計算の方がシンプル

### Decision: 速度はセッション間で永続化しない（起動時 1.0x）

- **Decision**: `self._playback_rate: float = 1.0` は `__init__` 時の初期値のまま。`AppSettings` への保存なし
- **Rationale**: 仕様クラリファイで確認済み。練習動画ごとに速度が異なるため前回値の引き継ぎは有害

---

## F-203: ミラー表示（左右反転）

### Decision: VLC `media.add_option(':video-filter=transform{type=hflip}')` によるミラー実装

- **Decision**: ミラー有効時は `_open_path` でメディアに `:video-filter=transform{type=hflip}` オプションを付加する。無効時はオプションなし。`media_player.set_media(media)` 前に適用する
- **Rationale**: python-vlc の API (`video_set_adjust_int` など) にはミラー/変形フィルタが存在しない。VLC のメディアオプション経由が唯一の公式手段であり、実際に動作確認済み（`media.add_option(':video-filter=transform')` + `':transform-type=hflip'` で OK）
- **Alternatives considered**:
  - `QGraphicsView` + `QTransform` で Qt 描画レイヤーで反転する案: VLC の映像が直接 `winId` に描画されるため、Qt のウィジェット変形は映像に適用されない。却下
  - `--video-filter` をインスタンス起動オプションにする案: 動的なトグルができないため却下

### Decision: ミラー状態の設定保存方法

- **Decision**: `AppSettings.mirror_display: bool` プロパティを新規追加（`settings.json` に `mirror_display` キー、デフォルト `False`）
- **Rationale**: `always_on_top` と同じパターン。`toggle_` メソッドで状態を切り替え、`_app_settings.mirror_display = value` で即時保存

### Decision: 動画切り替え時のミラー継続

- **Decision**: `_open_path` 内でメディア生成時に `if self._app_settings.mirror_display:` で分岐してオプション付加。動画切り替えのたびに判定するためミラー状態が自動継続される
- **Rationale**: VLC のメディアオプションはメディアインスタンスに紐づく。新しいメディアを生成するたびに再適用が必要なため、`_open_path` への実装が自然

---

## 既存コードへの影響

| 変更箇所 | 変更内容 | リスク |
|---|---|---|
| `player.py:L40` `_PLAYBACK_RATES` | 6要素 → 10要素に置き換え | 既存 `_speed_up`/`_speed_down` は自動対応（インデックス操作） |
| `player.py` `_build_shortcuts` | `Shift+[`/`Shift+]` ショートカット追加 | 既存ショートカットとの競合なし |
| `player.py` `_build_menus` | 速度メニュー生成ループの元データが `_PLAYBACK_RATES` なので自動対応 | 低 |
| `player.py` `_build_menus` | 表示メニューに「左右反転」トグル追加 | `always_on_top` と同パターン |
| `player.py` `_open_path` | ミラーオプション付加ロジック追加 | 既存メディア生成フローへの最小追加 |
| `app_settings.py` | `mirror_display` プロパティ追加 | パターン踏襲、低リスク |
| `i18n.py` | 新規キー追加（ミラー・速度微調整ステータス） | 追加のみ |
