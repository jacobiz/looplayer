# Quickstart: シークバークリックによる任意位置再生（ループ中）

**Branch**: `026-seekbar-click-seek` | **Date**: 2026-03-24

---

## 実装の全体像

変更ファイル: **`looplayer/player.py` のみ**（4 箇所の局所変更）

変更の核心: `_on_timer()` の B点判定を「絶対値比較」から「クロッシング検出」に変える。

---

## Step 1: テストを書く（Constitution: テストファースト必須）

### 新規テストファイル

**`tests/unit/test_seekbar_click_loop.py`** — B点クロッシング検出のユニットテスト

```python
# 検証する主なケース
# 1. B点以降をクリックした後、タイマーで A点に飛ばない
# 2. B点前をクリック → 自然にB点到達でループトリガー
# 3. ループOFF後に位置ジャンプしない
# 4. A点のみ設定（B点なし）→ ループ動作なし
```

**`tests/integration/test_seekbar_click_during_loop.py`** — Qt イベントを使う統合テスト

```python
# 検証する主なケース
# 1. ループ内クリック → クリック位置から再生継続
# 2. ループ外クリック → クリック位置から再生、ループ維持
# 3. 一時停止中クリック → 一時停止維持
# 4. ズームモード中クリック → 正しい位置にシーク
```

---

## Step 2: 実装（テスト失敗を確認後）

### 変更箇所 1: `__init__()` にフィールド追加

```python
# player.py の __init__() 内、_b_handled_cooldown の近くに追加
self._prev_timer_ms: int | None = None  # B点クロッシング検出用
```

### 変更箇所 2: `_on_seek_ms()` にリセット追加

```python
def _on_seek_ms(self, ms: int) -> None:
    self.media_player.set_time(ms)
    self._prev_timer_ms = ms  # シーク後は新しい位置を基点にする ← 追加
    # ... 既存コード続く
```

### 変更箇所 3: `_on_timer()` の B点判定を変更

```python
# 変更前:
if current_ms >= self.ab_point_b and self._b_handled_cooldown == 0:

# 変更後:
if (
    self._prev_timer_ms is not None
    and self._prev_timer_ms < self.ab_point_b
    and current_ms >= self.ab_point_b
    and self._b_handled_cooldown == 0
):
```

また、タイマー処理の末尾で毎回更新:

```python
# _on_timer() の最後に追加（既存の return の前）
self._prev_timer_ms = current_ms
```

### 変更箇所 4: `_resume_after_pause()` にリセット追加

```python
def _resume_after_pause(self) -> None:
    self.media_player.set_time(self.ab_point_a)
    self._prev_timer_ms = self.ab_point_a  # A点バウンス後のクロッシング基点 ← 追加
    # ... 既存コード続く
```

---

## Step 3: テスト実行

```bash
# ユニットテストのみ（高速）
pytest tests/unit/test_seekbar_click_loop.py -v

# 統合テスト
pytest tests/integration/test_seekbar_click_during_loop.py -v

# 全テスト（既存テストの回帰確認）
pytest tests/ -v
```

---

## 注意事項

- `_prev_timer_ms` は `_on_timer()` の**実行後**に更新する（実行前の値でクロッシング判定するため）
- `_b_handled_cooldown` は変更しない（二重トリガー防止として引き続き機能する）
- `BookmarkSlider`（`bookmark_slider.py`）は変更不要
- B点クロッシング検出: `_prev_timer_ms is not None` のチェックが必要（初回タイマー実行時は None）

---

## 検証手順（手動）

1. 動画を開き、A点=10秒、B点=20秒を設定してループONにする
2. シークバーの 5秒位置をクリック → 5秒から再生開始、20秒でA点（10秒）に戻ることを確認
3. シークバーの 25秒位置（B点以降）をクリック → 25秒から再生開始、A点に即ジャンプしないことを確認
4. ズームモードで同じ操作を繰り返す
5. 一時停止中にクリック → 位置移動のみ、再生開始しないことを確認
