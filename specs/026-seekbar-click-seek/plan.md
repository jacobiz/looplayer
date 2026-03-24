# Implementation Plan: シークバークリックによる任意位置再生（ループ中）

**Branch**: `026-seekbar-click-seek` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/026-seekbar-click-seek/spec.md`

## Summary

ABループ有効中にシークバーをクリックしてもクリック位置から再生できない問題を修正する。原因は `_on_timer()` の B点判定が「絶対値比較（`current_ms >= B`）」であるため、B点以降をクリックした直後に A点へジャンプしてしまうこと。修正方針は B点判定を「クロッシング検出（`prev < B ≤ current`）」に変更し、`looplayer/player.py` のみ 4 箇所の局所変更で対応する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A（新規データ永続化なし）
**Testing**: pytest + pytest-qt
**Target Platform**: Linux / Windows / macOS デスクトップ
**Project Type**: desktop-app
**Performance Goals**: シーク応答は既存シーク操作と同等（追加遅延なし）
**Constraints**: `_on_timer()` の 200ms サイクル内で完結する変更のみ
**Scale/Scope**: 単一ユーザー・デスクトップアプリ・変更対象ファイル 1 本

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 状態 | 根拠 |
|------|------|------|
| **I. テストファースト** | ✅ PASS | `tests/unit/test_seekbar_click_loop.py` と `tests/integration/test_seekbar_click_during_loop.py` を実装前に作成する。既存テストパターン（`player._on_timer()` 直接呼び出し + `qtbot`）を踏襲。統合テストは実際の Qt イベントループを使用（モックなし） |
| **II. シンプルさ重視** | ✅ PASS | フィールド 1 個追加 + 4 箇所の局所変更のみ。新クラス・新メソッドは作らない |
| **III. 過度な抽象化の禁止** | ✅ PASS | ヘルパー・ユーティリティ・ラッパー追加なし。既存の `_b_handled_cooldown` パターンを模倣した最小変更 |
| **IV. 日本語コミュニケーション** | ✅ PASS | コメント・コミットメッセージは日本語で記述する |

*Post-design re-check*: Phase 1 設計後も全原則 PASS。新しいパターン・抽象層は導入していない。

## Project Structure

### Documentation (this feature)

```text
specs/026-seekbar-click-seek/
├── plan.md              # このファイル
├── spec.md              # 機能仕様
├── research.md          # Phase 0 調査結果
├── data-model.md        # Phase 1 データモデル・状態遷移
├── quickstart.md        # Phase 1 実装クイックスタート
└── tasks.md             # Phase 2 output (/speckit.tasks で生成)
```

### Source Code (repository root)

```text
looplayer/
└── player.py            # 変更: _prev_timer_ms 追加、_on_timer() B点判定変更、
                         #        _on_seek_ms() / _resume_after_pause() にリセット追加

tests/
├── unit/
│   └── test_seekbar_click_loop.py      # 新規: B点クロッシング検出ユニットテスト
└── integration/
    └── test_seekbar_click_during_loop.py  # 新規: シークバークリック統合テスト
```

**Structure Decision**: 単一プロジェクト構成（Option 1）。変更対象ファイルは `player.py` のみで、テストは既存の `tests/unit/` と `tests/integration/` に追加する。

## Complexity Tracking

> 今回の変更に Constitution 違反はなし。

---

## 実装方針詳細

### 変更の核心

**旧ロジック（B点判定）**:
```python
# current_ms が B点以上にいる間ずっとトリガー可能
# → B点以降にシークすると即 A点ジャンプ
if current_ms >= self.ab_point_b and self._b_handled_cooldown == 0:
    self._b_handled_cooldown = 3
    self._start_pause_or_seek(self.ab_point_a, pause_ms)
```

**新ロジック（クロッシング検出）**:
```python
# prev < B ≤ current の「またぎ」でのみトリガー
# → B点以降にシークすると prev >= B → クロス不成立 → A点に飛ばない
if (
    self._prev_timer_ms is not None
    and self._prev_timer_ms < self.ab_point_b
    and current_ms >= self.ab_point_b
    and self._b_handled_cooldown == 0
):
    self._b_handled_cooldown = 3
    self._start_pause_or_seek(self.ab_point_a, pause_ms)

# タイマーの末尾で毎回更新
self._prev_timer_ms = current_ms
```

### シーク時のリセット

```python
def _on_seek_ms(self, ms: int) -> None:
    self.media_player.set_time(ms)
    self._prev_timer_ms = ms   # ← 追加: 新しい位置を基点にする

def _resume_after_pause(self) -> None:
    self.media_player.set_time(self.ab_point_a)
    self._prev_timer_ms = self.ab_point_a  # ← 追加: A点バウンス後の基点
```

### シナリオ別の動作確認

| シナリオ | prev（クリック後） | 次タイマー | B点判定 | 結果 |
|---------|-----------------|-----------|--------|------|
| A点前クリック（A=30, B=60, click=10） | prev=10 | curr=10200ms | 10 < 60 → 成立待ち | 60秒でループ ✓ |
| ループ内クリック（A=30, B=60, click=45） | prev=45 | curr=45200ms | 45 < 60 → 成立待ち | 60秒でループ ✓ |
| B点以降クリック（A=30, B=60, click=70） | prev=70 | curr=70200ms | 70 < 60 → 不成立 | A点に飛ばない ✓ |
| 自然なB点到達（A=30, B=60） | prev=59800ms | curr=60000ms | 59800 < 60000 → 成立 | A点へ戻る ✓ |

### テスト戦略（Constitution I 準拠）

実装前に以下を作成・失敗確認する:

**ユニットテスト** (`tests/unit/test_seekbar_click_loop.py`):
- `test_click_past_b_does_not_jump_to_a` — B点以降クリック後タイマーで A点ジャンプなし
- `test_natural_b_crossing_triggers_loop` — 自然な B点到達でループトリガー
- `test_seek_before_b_then_loop_triggers` — B点前シーク → 自然に到達でループ
- `test_loop_toggle_off_preserves_position` — ループOFF後に位置ジャンプなし
- `test_a_only_no_loop_behavior` — A点のみ設定でループ動作なし
- `test_prev_timer_ms_reset_on_seek` — `_on_seek_ms()` で `_prev_timer_ms` がリセットされる

**統合テスト** (`tests/integration/test_seekbar_click_during_loop.py`):
- `test_click_within_loop_starts_from_click_position` — ループ内クリック → クリック位置から再生
- `test_click_outside_loop_starts_from_click_position` — ループ外クリック → クリック位置から再生
- `test_pause_state_preserved_on_click` — 一時停止中クリック → 一時停止維持
- `test_zoom_mode_click_seeks_correctly` — ズームモード中クリック → 正しい位置

---

## 生成済み成果物

| ファイル | 内容 |
|---------|------|
| `research.md` | 根本原因分析・修正アプローチ選定・テスト戦略 |
| `data-model.md` | `_prev_timer_ms` フィールド仕様・状態遷移 |
| `quickstart.md` | 実装手順・コード例・検証手順 |
