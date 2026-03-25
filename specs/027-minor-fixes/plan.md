# Implementation Plan: 細かな修正（バージョン更新キャッシュ短縮・B点アイコン改善）

**Branch**: `027-minor-fixes` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/027-minor-fixes/spec.md`

---

## Summary

2 つの独立した局所修正。定数値の変更（1行）と Qt StandardPixmap の変更（1行）のみ。
Constitution I に従い、テストを先に書いてから実装する。

---

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/settings.json`（`last_update_check_ts` フィールド、既存）
**Testing**: pytest + pytest-qt
**Target Platform**: Windows / macOS / Linux（デスクトップ）
**Project Type**: desktop-app
**Performance Goals**: N/A（定数変更・アイコン変更のみ）
**Constraints**: 既存テストを全 PASS に維持すること
**Scale/Scope**: 変更ファイル 2 本（updater.py, player.py）、テスト追加 2 本

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. テストファースト ✅

- US1: `_CHECK_INTERVAL_SECS == 21600` を検証するテスト＋境界テストを先に書く
- US2: B点アイコンが `SP_MediaSkipForward` であることを検証するテストを先に書く
- どちらも「テストが FAIL してから実装」の手順を厳守する

### II. シンプルさ重視 ✅

- US1: 定数 1 行の変更のみ（新フィールド・設定公開なし）
- US2: `StandardPixmap` 引数 1 箇所の変更のみ（新メソッド・ヘルパー追加なし）

### III. 過度な抽象化の禁止 ✅

- 新しいクラス・ヘルパー・パターンは一切導入しない

### IV. 日本語コミュニケーション ✅

- コメント・コミットメッセージは日本語で記述する

---

## Project Structure

### Documentation (this feature)

```text
specs/027-minor-fixes/
├── plan.md              # このファイル
├── spec.md              # 機能仕様
├── research.md          # Phase 0 出力
├── quickstart.md        # 手動確認手順
└── tasks.md             # Phase 2 出力（/speckit.tasks コマンド）
```

### Source Code（変更対象）

```text
looplayer/
├── updater.py           # US1: _CHECK_INTERVAL_SECS 変更（1行）
└── player.py            # US2: set_b_btn StandardPixmap 変更（1行）

tests/
├── unit/
│   └── test_updater.py  # US1: docstring 更新 + 境界テスト追加
└── integration/
    └── test_button_icons_p2.py  # US2: B点アイコン具体確認テスト追加
```

---

## Phase 0: Research 結果

→ 詳細は [research.md](research.md) を参照。

**US1 決定事項**:
- `_CHECK_INTERVAL_SECS = 21600`（86400 → 21600、6h = 6 × 3600）
- コメントも合わせて更新（`# 24時間キャッシュ` → `# 6時間キャッシュ`）
- 変更ファイル: `looplayer/updater.py`（2行変更）

**US2 決定事項**:
- `QStyle.StandardPixmap.SP_FileDialogEnd` → `QStyle.StandardPixmap.SP_MediaSkipForward`
- `SP_MediaSkipForward`（⏭）は `SP_MediaSkipBackward`（⏮）との完全対称を実現する
- 変更ファイル: `looplayer/player.py`（1行変更）

---

## Phase 1: Design

### データモデル変更

なし。`last_update_check_ts` フィールドはすでに `AppSettings` に存在し、変更不要。

### インターフェース契約

アプリ内部の変更のみ。外部インターフェースなし。

### テスト設計

#### US1 テスト

**追加場所**: `tests/unit/test_updater.py`

| テスト名 | 目的 | 方法 |
|----------|------|------|
| `test_check_interval_is_6h` | `_CHECK_INTERVAL_SECS == 21600` を定数テスト | `from looplayer.updater import _CHECK_INTERVAL_SECS; assert _CHECK_INTERVAL_SECS == 21600` |
| `test_update_checker_skips_within_6h` | 5h前チェック済み → スキップ | `last_ts=time.time() - 5*3600`, urlopen が呼ばれないこと |
| `test_update_checker_runs_after_6h` | 7h前チェック済み → 実行 | `last_ts=time.time() - 7*3600`, urlopen が呼ばれること |
| `test_update_checker_skips_when_checked_recently` | docstring を「6h」に更新 | 既存テスト・ロジック変更なし |

#### US2 テスト

**追加場所**: `tests/integration/test_button_icons_p2.py`

| テスト名 | 目的 | 方法 |
|----------|------|------|
| `test_set_b_btn_icon_matches_sp_media_skip_forward` | B点アイコンが `SP_MediaSkipForward` であること | `player.style().standardIcon(SP_MediaSkipForward).cacheKey()` と `player.set_b_btn.icon().cacheKey()` の比較 |
| `test_set_a_and_b_icons_are_symmetric_pair` | A・B点が対称アイコンペアであること | A点: `SP_MediaSkipBackward`, B点: `SP_MediaSkipForward` の cacheKey 確認 |

---

## Complexity Tracking

なし（Constitution Check 違反ゼロ）。

---

## 実装手順サマリー（tasks.md 生成前の参考）

```
Phase 1: Setup（ベースライン確認）
  T001: pytest tests/unit/test_updater.py + tests/integration/test_button_icons_p2.py

Phase 2: US1 テストファースト
  T002: test_check_interval_is_6h を書いて FAIL を確認
  T003: test_update_checker_skips_within_6h を書いて FAIL を確認
  T004: test_update_checker_runs_after_6h を書いて FAIL を確認
  T005: _CHECK_INTERVAL_SECS 変更（21600）+ docstring 更新 → テスト PASS 確認

Phase 3: US2 テストファースト
  T006: test_set_b_btn_icon_matches_sp_media_skip_forward を書いて FAIL を確認
  T007: test_set_a_and_b_icons_are_symmetric_pair を書いて FAIL を確認
  T008: set_b_btn StandardPixmap 変更 → テスト PASS 確認

Phase 4: Polish
  T009: 全テストスイート回帰確認
```
