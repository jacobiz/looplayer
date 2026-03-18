# Implementation Plan: P2 UX 機能群

**Branch**: `017-p2-ux-features` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: F-105 ABループ区間のズーム表示 / F-401 設定画面（Preferences）/ F-501 初回起動オンボーディング / F-503 フルスクリーン中コントロールオーバーレイ

## Summary

4つのP2 UX機能を実装する。F-503（フルスクリーンオーバーレイ）は既存の `controls_panel` をフローティングオーバーレイとして再利用。F-401（設定ダイアログ）は新規 `PreferencesDialog(QDialog)` を `looplayer/widgets/preferences_dialog.py` に作成。F-501（オンボーディング）は新規 `OnboardingOverlay(QWidget)` を `looplayer/widgets/onboarding_overlay.py` に作成し `AppSettings.onboarding_shown` フラグで制御。F-105（ズーム）は `BookmarkSlider` に `_zoom_enabled`/`set_zoom()`/`clear_zoom()` を追加して座標変換を拡張。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/settings.json`（`AppSettings` クラスで管理）
**Testing**: pytest（TDD: テストファースト）
**Target Platform**: Linux / Windows / macOS デスクトップ
**Project Type**: desktop-app
**Performance Goals**: フルスクリーンオーバーレイ表示 ≤ 300ms（SC-001）
**Constraints**: 新規依存パッケージ追加なし、既存コードの再利用を最大化
**Scale/Scope**: 4機能、新規ファイル 2 件、既存ファイル 5 件変更

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **テストファースト**: 各機能の実装前にテストを作成する (TDD: RED → GREEN → Refactor)
- [x] **シンプルさ重視**: 既存ウィジェットの再利用（`controls_panel` フロート）、新規クラス最小化
- [x] **過度な抽象化の禁止**: `ZoomableSlider` サブクラスは不要、`BookmarkSlider` への直接拡張
- [x] **YAGNI**: `FullscreenOverlay` 新規ウィジェット作成不要
- [x] **i18n 必須**: 全新規 UI 文字列を `looplayer/i18n.py` の `t()` 経由で取得
- [x] **依存順序**: F-401 → F-501 の順に実装（`onboarding_shown` が F-401 の `AppSettings` 拡張に依存）

## Project Structure

### Documentation (this feature)

```text
specs/017-p2-ux-features/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ui-contracts.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
looplayer/
├── player.py                      # 変更: F-503 オーバーレイ、F-401 メニュー、F-501 起動、F-105 ズームボタン
├── app_settings.py                # 変更: onboarding_shown プロパティ追加
├── i18n.py                        # 変更: 新規 UI 文字列追加（約30キー）
└── widgets/
    ├── bookmark_slider.py         # 変更: zoom state + set_zoom/clear_zoom
    ├── preferences_dialog.py      # 新規: PreferencesDialog(QDialog)
    └── onboarding_overlay.py      # 新規: OnboardingOverlay(QWidget)

tests/
├── unit/
│   ├── test_fullscreen_overlay.py  # 新規
│   ├── test_preferences_dialog.py  # 新規
│   ├── test_onboarding_overlay.py  # 新規
│   └── test_bookmark_slider_zoom.py # 新規
└── integration/
    └── test_settings_isolation.py  # 新規
```

**Structure Decision**: Single project。既存 `looplayer/widgets/` に新規ウィジェットを追加。テストは既存 `tests/unit/` および `tests/integration/` に追加。

## Implementation Order (Priority)

1. **F-401 PreferencesDialog** — 他機能より先（`onboarding_shown` の AppSettings 拡張を含む）
2. **F-503 Fullscreen Overlay** — P1 優先度、既存ユーザーへの影響大
3. **F-501 Onboarding Overlay** — F-401 の AppSettings 拡張に依存
4. **F-105 Zoom Mode** — 独立機能、最後に追加
