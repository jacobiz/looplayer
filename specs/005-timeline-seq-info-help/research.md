# Research: タイムライン強化・連続再生選択・動画情報・ショートカット一覧

**Branch**: `005-timeline-seq-info-help` | **Date**: 2026-03-16

---

## 1. タイムライン上のABループ区間表示

### Decision: QSlider サブクラス化 + `paintEvent` オーバーライド

**Rationale**:
- `super().paintEvent(event)` でスライダー本来の描画を完了させてから、`QPainter` で半透明矩形を重ね描きする
- マウス操作（ドラッグシーク）はすべて `QSlider` の元実装が処理するため、既存機能を壊さない
- 追加ライブラリなし、コード量最小、既存 `player.py` の変更は `self.seek_slider` の型を変えるだけ

**Alternatives considered**:
- QWidget ラッパー（QSlider を子ウィジェットとして持つ）: 座標空間の差異で計算が複雑になり不要なコード量が増える
- QProxyStyle で `drawComplexControl` をオーバーライド: 実装が重厚でこの規模には過剰

### グルーブ座標の取得方法

```python
opt = QStyleOptionSlider()
slider.initStyleOption(opt)   # 現在値・向き・状態を正確に反映するために必須
groove = slider.style().subControlRect(
    QStyle.ComplexControl.CC_Slider,
    opt,
    QStyle.SubControl.SC_SliderGroove,
    slider,
)
# ミリ秒 → X座標変換
x = groove.left() + int((ms / duration_ms) * groove.width())
```

`initStyleOption` を呼ばないと向き・範囲が反映されず座標がずれるため必須。

### 色割り当てと重複描画

- 各ブックマークに固有色をインデックス循環で割り当て（最大4色パレット、拡張可）
- 重複区間は同一高さで半透明重ね描き（アルファ約120/255）
- 区間の最小幅: `max(x2 - x1, 4)` で4px以下にならないようにクランプ

### クリック時のブックマーク特定

- 重複時は最後に登録された（最前面の）ブックマークを選択
- `mousePressEvent` をオーバーライドし、X 座標が `[x1, x2]` に含まれるブックマークを後ろから探索
- クリック判定はシーク動作を妨げないよう、クリック解放時ではなく `mousePressEvent` で発火

---

## 2. 連続再生対象のチェックボックス選択

### Decision: `LoopBookmark` に `enabled: bool = True` フィールドを追加

**Rationale**:
- 既存 `bookmarks.json` の同一スキーマに `"enabled": true/false` を追加するのが最小変更
- `from_dict` で `enabled` キーが存在しない（旧JSON）場合は `True` にフォールバック → 後方互換性を維持
- `BookmarkRow` にチェックボックスを追加し、変更時に `BookmarkStore.update_enabled()` を呼ぶ
- `BookmarkPanel._on_seq_btn` で `[bm for bm in bms if bm.enabled]` でフィルタリング

**Alternatives considered**:
- 別ファイルにチェック状態を保存: 既存 `bookmarks.json` との同期問題が生じるため却下

### 連続再生ボタンの有効/無効管理

- `_refresh_list` の末尾で `seq_btn.setEnabled(any(bm.enabled for bm in bms))` に変更
- チェックボックスのトグル時も同様に再計算

---

## 3. 動画情報の取得

### Decision: 再生中の Media オブジェクトから `tracks_get()` で取得

**Rationale**:
- `media_player.get_media()` で現在の Media を取得
- 再生済みなので `parse()` 不要。`tracks_get()` でトラック情報を取得
- `VideoTrack.width/height/frame_rate_num/frame_rate_den` で解像度・FPS
- `libvlc_media_get_codec_description(track_type, codec)` で人間可読なコーデック名
- ファイルサイズは `os.path.getsize()` で取得

**FPS 計算**:
```python
fps = frame_rate_num / frame_rate_den  # frame_rate_den != 0 のガード必須
```

**コーデック名取得**:
```python
codec_desc = vlc.libvlc_media_get_codec_description(vlc.TrackType.video, track.codec)
```

**ファイルサイズ表示**:
- 1GB以上: `{n:.1f} GB`
- 1MB以上: `{n:.1f} MB`
- それ以外: `{n} KB`

**動画の長さ**: `media_player.get_length()` (ms) → `ms_to_str()` で `mm:ss` 形式

### 取得タイミング

- 動画情報ダイアログは再生中（または停止後でも `get_media()` が有効な間）に呼ばれる
- `video_get_size(0)` は再生中のみ有効（parse後の停止状態では (0,0) を返す）ため非推奨
- `tracks_get()` は再生後に必ず有効なため採用

---

## 4. キーボードショートカット一覧

### Decision: 静的テキストテーブルのダイアログ（QLabelとQGridLayout）

**Rationale**:
- ショートカットは仕様変更がない限り静的データ → ハードコードが最小実装
- `QLabel`（テキスト選択不要）+ カテゴリ見出しのシンプルなダイアログ
- `?` キーは `QShortcut` で登録（ApplicationShortcut コンテキスト）
- ヘルプメニュー: `menuBar().addMenu("ヘルプ(&H)")` を追加

**Alternatives considered**:
- 設定ファイルからショートカット一覧を動的生成: 現状ショートカットは変更不可能なため過剰

### ダイアログ設計

- `QDialog` サブクラスとして実装（モーダルでなく非モーダル: `show()` 利用可。シンプルに `exec()` でも可）
- カテゴリ: 再生操作 / 音量操作 / ABループ操作 / ブックマーク操作 / 表示操作
- 各行: キー名（右寄せ太字） + 機能説明（左寄せ）の2列レイアウト
- `Escape` で閉じる（`QDialog` のデフォルト動作）

---

## 未解決事項（なし）

すべての技術的不明点が解消されました。
