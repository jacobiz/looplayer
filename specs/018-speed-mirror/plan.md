# Implementation Plan: 再生速度拡張・ミラー表示（F-101 / F-203）

**Branch**: `018-speed-mirror` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-speed-mirror/spec.md`

## Summary

再生速度の選択可能範囲を 0.25x〜3.0x に拡張し（F-101）、Shift+[/] による 0.05x 刻みの微調整ショートカットを追加する。また、VLC メディアオプション経由で映像の左右反転（ミラー表示）をトグルする機能を表示メニューに追加する（F-203）。ミラー状態はアプリ設定に永続化し、動画切り替えおよびアプリ再起動後も保持する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203
**Storage**: `~/.looplayer/settings.json`（AppSettings、mirror_display フィールド追加）
**Testing**: pytest
**Target Platform**: デスクトップアプリ（Linux / Windows / macOS）
**Project Type**: desktop-app
**Performance Goals**: Shift+[/] 操作から速度変化反映まで 100ms 以内（SC-001）
**Constraints**: 速度 0.25x〜3.0x の全範囲でクラッシュなし（SC-002）；ミラートグル 1 回の操作で即完了（SC-003）
**Scale/Scope**: 既存 VideoPlayer クラスへの最小限の拡張。ファイル変更は player.py / app_settings.py / i18n.py の 3 ファイル + テストファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 適合状況 | 備考 |
|------|---------|------|
| I. テストファースト | ✅ PASS | 各 US にユニットテストを先に作成する（RED→GREEN） |
| II. シンプルさ重視 | ✅ PASS | `_PLAYBACK_RATES` リスト変更のみで US2 対応。抽象レイヤー追加なし |
| III. 過度な抽象化の禁止 | ✅ PASS | 新クラス・ヘルパーなし。既存メソッドにロジック追加のみ |
| IV. 日本語コミュニケーション | ✅ PASS | UI ラベル・コメント・コミットは日本語で記述 |

**Constitution Check（Phase 1 design 後）**: 全原則 PASS。Complexity Tracking 記録なし（複雑さの導入なし）。

## Project Structure

### Documentation (this feature)

```text
specs/018-speed-mirror/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — 技術的判断の記録
├── data-model.md        # Phase 1 — エンティティ・定数変更
├── contracts/
│   └── ui-contracts.md  # Phase 1 — UI コントラクト
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
looplayer/
├── player.py            # 変更: _PLAYBACK_RATES, Shift+[/] ショートカット, ミラーメニュー, _open_path
├── app_settings.py      # 変更: mirror_display プロパティ追加
└── i18n.py              # 変更: 3 つの新規 i18n キー追加

tests/
└── unit/
    ├── test_speed_fine_adjustment.py   # 新規: US1 ユニットテスト
    ├── test_speed_menu_expansion.py    # 新規: US2 ユニットテスト
    └── test_mirror_display.py         # 新規: US3 ユニットテスト
```

**Structure Decision**: 既存単一プロジェクト構造を踏襲。新ファイルは `tests/unit/` のみ。本体変更は既存 3 ファイルへの追記のみで完結。

## Implementation Phases

### Phase 1: 基盤（Foundation）

**目的**: 既存 `_PLAYBACK_RATES` 定数の拡張と `AppSettings.mirror_display` プロパティ追加。後続 US すべての前提。

変更対象:
- `looplayer/player.py`: `_PLAYBACK_RATES = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]`
- `looplayer/app_settings.py`: `mirror_display` getter/setter プロパティ
- `looplayer/i18n.py`: `menu.view.mirror_display`, `status.speed_fine_up`, `status.speed_fine_down` キー

### Phase 2: US1 — 速度微調整ショートカット（Shift+[/]）

**目的**: `_speed_fine_up()` / `_speed_fine_down()` メソッドと対応ショートカット。

変更対象:
- `looplayer/player.py`: `_speed_fine_up()`, `_speed_fine_down()`, `_build_shortcuts()` に Shift+[/] 追加

テスト（先に作成）:
- `tests/unit/test_speed_fine_adjustment.py`

### Phase 3: US2 — 速度メニュー 10 段階（自動対応）

**目的**: `_PLAYBACK_RATES` の変更により `_build_menus()` の速度メニューループが自動で 10 段階を生成する。追加実装不要。

確認テスト:
- `tests/unit/test_speed_menu_expansion.py`（メニュー生成ロジックの検証）

### Phase 4: US3 — ミラー表示

**目的**: 表示メニューへの「左右反転」追加、`_toggle_mirror_display()` メソッド、`_open_path()` へのミラーオプション付加。

変更対象:
- `looplayer/player.py`: `_build_menus()` に mirror_action 追加、`_toggle_mirror_display()`, `_open_path()` 内 mirror 分岐

テスト（先に作成）:
- `tests/unit/test_mirror_display.py`

## Key Design Decisions

| 決定 | 内容 | 根拠 |
|------|------|------|
| `_PLAYBACK_RATES` 置き換え | 6 要素 → 10 要素に変更 | インデックス操作コードが自動対応；変更箇所 1 箇所 |
| `round(..., 2)` 適用 | 0.05x 刻み加算時の浮動小数点誤差防止 | 繰り返し加算で `0.9999...` が蓄積するため必須 |
| VLC `media.add_option()` | ミラー実装手段 | Qt ウィジェット変形は VLC の winId 描画に効かない。VLC メディアオプションが唯一の公式手段 |
| `mirror_display` を AppSettings に保存 | `always_on_top` と同パターン | セッション間で永続化が必要；既存パターン踏襲で低リスク |
| 速度は AppSettings に保存しない | 起動時常に 1.0x | 練習動画ごとに速度が異なるため前回値引き継ぎは有害（仕様確認済み） |

## Complexity Tracking

> 今回の実装に複雑さの追加なし。Constitution Check 全 PASS のため記録不要。
