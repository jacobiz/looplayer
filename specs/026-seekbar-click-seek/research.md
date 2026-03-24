# Research: シークバークリックによる任意位置再生（ループ中）

**Branch**: `026-seekbar-click-seek` | **Date**: 2026-03-24

---

## 調査項目 1: バグの根本原因

**Decision**: `_on_timer()` の B点判定が「位置 >= B点」という絶対値比較になっており、クリック後に A点へ戻す原因となっている。

**Rationale**:
- `_on_timer()` は 200ms 毎に実行される
- 現在の判定: `current_ms >= ab_point_b and _b_handled_cooldown == 0`
- ユーザーが B点以降をクリックすると `current_ms >= ab_point_b` が真になり即座にA点へジャンプ
- ループ範囲内でも、クリック直後のタイマーで VLC の再生位置がスライダーを上書きする前に B点判定が先に走ることがある

**Alternatives considered**:
- `_b_handled_cooldown` を延長する → 既存の通常ループ操作にも影響し副作用大
- クリック後に一定時間 B点判定を完全スキップする → B点付近でのクリックで通常ループが 600ms 遅延する

---

## 調査項目 2: 修正アプローチの選定

**Decision**: B点判定を「絶対値比較」から「B点をまたぐ遷移（前回 < B点 ≤ 今回）」の**クロッシング検出**に変更する。

**Rationale**:
- クロッシング検出により「B点以降をクリック → prev >= B になる → 次回も prev >= B → クロス不成立 → A点へ飛ばない」という動作が自然に実現
- B点より前をクリック → 自然に B点に到達 → prev < B ≤ current → 正常にループトリガー
- 既存の `_b_handled_cooldown` との組み合わせで二重トリガーも防止
- コード変更が最小（`_on_timer()` 内の条件式 1 行 + フィールド 1 個 + シーク時のリセット 1 行）

**Alternatives considered**:
- 方式A（クールダウンフラグ追加）: `_seek_cooldown = 3` を追加し、タイマー内でスキップ
  - 問題: B点以降にシークした場合、600ms 後に `current_ms >= B` がまだ真のままで再びトリガーされる
- 方式B（ドラッグフラグ流用）: クリック時も `is_track_dragging = True` にする
  - 問題: ドラッグとクリックは別シグナル経路であり、フラグ誤用になる
  - 問題: スライダーの位置自動更新は抑制できても、B点判定には無関係

---

## 調査項目 3: 変更ファイルの特定

**Decision**: 変更は `looplayer/player.py` のみ。`bookmark_slider.py` は変更不要。

**Rationale**:
- `BookmarkSlider.seek_requested` シグナルは既に正しい ms 位置を emit している
- ズームモードの座標変換も `BookmarkSlider` 内で完結しており、シグナルの値は常に正しい絶対 ms 位置
- バグは player 側の `_on_timer()` にあるため、slider 側は変更不要

**Affected lines in player.py**:
| 場所 | 変更内容 |
|------|---------|
| `__init__()` 行 ~108 | `self._prev_timer_ms: int \| None = None` フィールド追加 |
| `_on_timer()` 行 ~1119 | `_prev_timer_ms` 更新、B点判定をクロッシング検出に変更 |
| `_on_seek_ms()` 行 ~1117 | `self._prev_timer_ms = ms` でシーク後の基点をリセット |
| `_resume_after_pause()` 行 ~1995 | 自動 A点シーク後も `_prev_timer_ms = ab_point_a` でリセット |

---

## 調査項目 4: ズームモードへの影響

**Decision**: ズームモードは変更なしで対応済み。追加対応不要。

**Rationale**:
- `BookmarkSlider._ms_to_x()` でズーム範囲をウィジェット幅にマップ
- クリック時の `_x_to_ms()` でズーム座標を絶対 ms に逆変換して `seek_requested.emit(ms)`
- Player の `_on_seek_ms(ms)` は絶対 ms を受け取るため、ズームの有無に無関係
- 修正は `_on_timer()` の B点判定ロジックのみであり、ズームモードに依存しない

---

## 調査項目 5: テスト戦略

**Decision**: ユニットテスト（タイマーモック）＋ 統合テスト（Qt イベントループ）の 2 層で網羅。

**Rationale**:
- 既存パターンに合わせ `player._on_timer()` を直接呼び出すユニットテストで高速検証
- `qtbot` 経由のシークバークリックシミュレーションで統合テストも追加
- Constitution: モックではなく実際の依存を使う統合テスト必須

**Test cases required**:

| テストケース | 種別 | 検証内容 |
|------------|------|---------|
| `test_click_within_loop_starts_from_click_position` | 統合 | ループ内クリック → クリック位置から再生 |
| `test_click_outside_loop_starts_from_click_position` | 統合 | ループ外クリック → クリック位置から再生 |
| `test_click_past_b_does_not_jump_to_a` | ユニット | B点以降クリック後のタイマーで A点に飛ばない |
| `test_loop_resumes_after_seek_before_b` | ユニット | B点前にシーク → 自然に B点到達でA点へ戻る |
| `test_pause_state_preserved_on_click` | 統合 | 一時停止中クリック → 一時停止維持 |
| `test_loop_toggle_off_preserves_position` | ユニット | ループOFF後に位置ジャンプしない |
| `test_a_only_no_loop_behavior` | ユニット | A点のみ設定（B点なし）→ ループ動作なし |
| `test_zoom_mode_click_seeks_correctly` | 統合 | ズームモード中クリック → 正しい ms へシーク |

---

## 調査項目 6: ループ有効条件の確認

**Decision**: `ab_loop_active == True` かつ `ab_point_a is not None` かつ `ab_point_b is not None` の 3 条件すべてが必要。

**Rationale**:
- `toggle_ab_loop()` で `ab_loop_active` を制御（ユーザーのトグルON/OFF）
- A点B点の両方設定は既存コードで `a < b` のバリデーションあり
- この 3 条件は既存の `_on_timer()` B点判定でも使われており、変更不要

---

## 未解決事項

なし。全 NEEDS CLARIFICATION 解消済み。
