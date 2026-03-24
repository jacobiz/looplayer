# Data Model: シークバークリックによる任意位置再生（ループ中）

**Branch**: `026-seekbar-click-seek` | **Date**: 2026-03-24

---

## 概要

本機能は新しいデータエンティティを追加しない。既存の `VideoPlayer` クラスに状態フィールドを 1 つ追加するのみ。

---

## 変更される状態（VideoPlayer クラス）

### 追加フィールド

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|-------|------|
| `_prev_timer_ms` | `int \| None` | `None` | 直前の `_on_timer()` 実行時の再生位置（ms）。B点クロッシング検出に使用 |

### 既存フィールド（変更なし・参照のみ）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `ab_point_a` | `int \| None` | A点位置（ms） |
| `ab_point_b` | `int \| None` | B点位置（ms） |
| `ab_loop_active` | `bool` | ループトグルのON/OFF |
| `_b_handled_cooldown` | `int` | B点二重トリガー防止カウンター（0になるまでスキップ）|

---

## 状態遷移

### `_prev_timer_ms` の更新タイミング

```text
[アプリ起動] → _prev_timer_ms = None

[_on_timer() 実行] → 毎回: _prev_timer_ms = current_ms（実行後に更新）

[ユーザーがシークバーをクリック]
  → _on_seek_ms(ms) → _prev_timer_ms = ms
  （次のタイマーサイクルのクロッシング検出がシーク位置を基点とする）

[ABループによる自動 A点シーク（_resume_after_pause）]
  → _prev_timer_ms = ab_point_a
  （A点バウンス後、A点を基点として次のクロッシングを検出）
```

### B点クロッシング検出ロジック（新）

```text
【旧条件】
current_ms >= ab_point_b AND _b_handled_cooldown == 0

【新条件】
_prev_timer_ms is not None
AND _prev_timer_ms < ab_point_b
AND current_ms >= ab_point_b
AND _b_handled_cooldown == 0
```

### シナリオ別の状態変化

| シナリオ | クリック前 | クリック後 | 次タイマー | 結果 |
|---------|-----------|-----------|-----------|------|
| ループ内クリック（A < click < B） | prev=any | prev=click | prev=click, curr=click+200ms | B点まで通常再生 |
| ループ前クリック（click < A） | prev=any | prev=click | prev=click, curr=click+200ms | B点まで通常再生→ループ |
| B点以降クリック（click > B） | prev=any | prev=click(>B) | prev=click(>B), curr>B: `prev < B` 不成立 | A点へ飛ばない |
| 自然なB点到達 | prev<B | — | prev<B, curr>=B: クロス成立 | A点へ戻る（正常ループ） |

---

## 永続化

本機能で永続化されるデータは追加なし。`_prev_timer_ms` はメモリ内のみ。

---

## 外部インターフェース

デスクトップアプリ（内部専用）のため、外部 API 契約は存在しない。`contracts/` ディレクトリは不要。
