# Quickstart: タイムライン強化・連続再生選択・動画情報・ショートカット一覧

**Branch**: `005-timeline-seq-info-help` | **Date**: 2026-03-16

---

## 機能の概要と実装の切り口

この機能は4つの独立したユーザーストーリーで構成され、それぞれ単独で実装・テスト・リリース可能。

---

## US1: タイムライン上のABループ区間表示

### 変更ファイル

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `looplayer/widgets/bookmark_slider.py` | **新規作成** | `BookmarkSlider` ウィジェット |
| `looplayer/player.py` | **変更** | `seek_slider` の型変更・シグナル接続・更新呼び出し |
| `tests/unit/test_bookmark_slider.py` | **新規作成** | 区間計算・描画・クリック判定のユニットテスト |
| `tests/integration/test_timeline_display.py` | **新規作成** | 統合テスト（ブックマーク追加後の表示確認） |

### 実装手順

1. **テスト先行**: `test_bookmark_slider.py` でグルーブ座標計算・ms→X変換・クリック判定を検証するテストを書く
2. `BookmarkSlider(QSlider)` を実装
   - `set_bookmarks(bookmarks, duration_ms)` で描画データを保持し `update()` を呼ぶ
   - `paintEvent`: `super().paintEvent(event)` → QPainter で半透明矩形を重ね描き
   - `mousePressEvent`: クリック位置が `[x1, x2]` に含まれるブックマークを後ろから探索 → `bookmark_bar_clicked` シグナルを emit
3. `player.py` の `_build_ui` で `self.seek_slider = BookmarkSlider(...)` に変更
4. `bookmark_bar_clicked` シグナルを `_on_bookmark_selected` に接続
5. ブックマーク変更・動画切替のタイミングで `_sync_slider_bookmarks()` を呼ぶ

### `_sync_slider_bookmarks()` の呼び出しタイミング

- `_save_bookmark()` 後
- `_on_bookmark_selected()` 後（連続再生中の強調表示更新）
- `open_file()` 後
- `_on_timer()` 内（連続再生中の強調表示リアルタイム更新）
- ブックマーク削除・Undo 後（`_refresh_list` 後）

---

## US2: 連続再生対象のチェックボックス選択

### 変更ファイル

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `looplayer/bookmark_store.py` | **変更** | `LoopBookmark` に `enabled: bool = True` を追加 |
| `looplayer/widgets/bookmark_row.py` | **変更** | チェックボックスを追加、`enabled_changed` シグナルを追加 |
| `looplayer/widgets/bookmark_panel.py` | **変更** | `seq_btn` 有効判定を `enabled` フィルタで変更、連続再生開始時にフィルタリング |
| `tests/unit/test_bookmark_enabled.py` | **新規作成** | enabled フィールドの永続化・後方互換性テスト |
| `tests/integration/test_sequential_filter.py` | **新規作成** | チェックされたブックマークのみ連続再生されることを検証 |

### 実装手順

1. **テスト先行**: enabled フィールドの `to_dict`/`from_dict` 動作と、古いJSON（enabledなし）の後方互換性テストを書く
2. `LoopBookmark` に `enabled: bool = True` を追加し `to_dict`/`from_dict` を更新
3. `BookmarkStore.update_enabled()` メソッドを追加
4. `BookmarkRow` にチェックボックス（`QCheckBox`）を追加
   - 初期値: `bm.enabled` の値でチェック状態をセット
   - `stateChanged` → `enabled_changed = pyqtSignal(str, bool)` を emit
5. `BookmarkPanel`:
   - `_refresh_list` の末尾: `seq_btn.setEnabled(any(bm.enabled for bm in bms))`
   - `_on_seq_btn` 内: `bms = [bm for bm in all_bms if bm.enabled]` でフィルタリング
   - `_on_enabled_changed` ハンドラを追加し `update_enabled` を呼んで `seq_btn` 有効状態を再計算

---

## US3: 動画情報の表示

### 変更ファイル

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `looplayer/player.py` | **変更** | `_show_video_info()` メソッド・「ファイル」メニューへの追加 |
| `tests/unit/test_video_info.py` | **新規作成** | VLC 取得値のフォーマット変換テスト（ファイルサイズ表示など） |
| `tests/integration/test_video_info_dialog.py` | **新規作成** | ダイアログの表示・項目確認 |

### 実装手順

1. **テスト先行**: ファイルサイズのフォーマット変換（bytes→MB表示）をユニットテストで検証
2. `player.py` に `_show_video_info()` を追加
   - `media_player.get_media()` → `tracks_get()` で VideoTrack と AudioTrack を取得
   - `VideoInfo` を構築し `QDialog` で表示
3. ダイアログレイアウト: `QGridLayout` で キー（右寄せ）/ 値（左寄せ）の2列
4. `_build_menus()` の「ファイル」メニューに「動画情報...」を追加
   - `self._export_action` と同様に `self._video_info_action` として管理
   - 動画が開かれていない時は `setEnabled(False)`、動画オープン時に `setEnabled(True)` にする

### 表示フォーマット

```
ファイル名:   example.mp4
ファイルサイズ: 123.4 MB
動画の長さ:   01:23:45
解像度:       1920 × 1080
フレームレート: 29.97 fps
映像コーデック: H264 - MPEG-4 AVC
音声コーデック: MPEG AAC Audio
```

---

## US4: キーボードショートカット一覧画面

### 変更ファイル

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `looplayer/player.py` | **変更** | `_show_shortcut_dialog()` メソッド・ヘルプメニュー追加・`?` キー登録 |
| `tests/integration/test_shortcut_dialog.py` | **新規作成** | ダイアログ表示・全カテゴリの存在確認 |

### 実装手順

1. **テスト先行**: ダイアログが開き、5カテゴリが全て含まれることを検証するテストを書く
2. `player.py` に `_show_shortcut_dialog()` を追加
   - `QDialog` サブクラスとしてインラインで実装（1箇所だけ使用するため別ファイル化しない）
   - ショートカットデータは `player.py` 内の定数リストとしてハードコード
3. `_build_menus()` にヘルプメニューを追加
4. `?` キーを `QShortcut` で `ApplicationShortcut` コンテキストに登録

### ショートカット一覧（静的データ）

```python
SHORTCUTS = [
    ("再生操作", [
        ("Space",   "再生 / 一時停止"),
        ("←",      "5秒戻る"),
        ("→",      "5秒進む"),
    ]),
    ("音量操作", [
        ("↑",      "音量を上げる (+10%)"),
        ("↓",      "音量を下げる (-10%)"),
        ("M",      "ミュート / ミュート解除"),
    ]),
    ("ABループ操作", [
        ("A",      "A点セット"),
        ("B",      "B点セット"),
    ]),
    ("ブックマーク操作", [
        ("Ctrl+Z", "ブックマーク削除を取り消す"),
    ]),
    ("表示操作", [
        ("F",      "フルスクリーン切替"),
        ("Escape", "フルスクリーン解除"),
        ("?",      "ショートカット一覧を表示"),
    ]),
    ("ファイル操作", [
        ("Ctrl+O", "ファイルを開く"),
        ("Ctrl+Q", "終了"),
    ]),
]
```

---

## テスト実行

```bash
# ユニットテストのみ（高速）
pytest tests/unit/ -v

# 統合テストを含む全テスト
pytest tests/ -v

# この機能に関連するテストのみ
pytest tests/ -k "slider or enabled or video_info or shortcut" -v
```

---

## 実装優先順位

1. **US2**（チェックボックス）: データモデル変更が含まれるため最初に完成させると後続に影響しない
2. **US1**（タイムライン）: 最もユーザー価値が高い
3. **US3**（動画情報）: 独立しているため任意の順序で可
4. **US4**（ショートカット一覧）: 独立、かつ最もシンプル
