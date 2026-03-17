# Implementation Plan: タイムライン強化・連続再生選択・動画情報・ショートカット一覧

**Branch**: `005-timeline-seq-info-help` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-timeline-seq-info-help/spec.md`

## Summary

シークバー上への ABループ区間の可視化（US1）、連続再生対象のチェックボックス選択（US2）、動画情報ダイアログ（US3）、ショートカット一覧ダイアログ（US4）の4機能を実装する。US1・US2はメイン学習機能の強化（P1）、US3・US4はユーザービリティ補助（P2）。技術的アプローチは `QSlider` サブクラス化による非侵入的な区間描画、`LoopBookmark` への `enabled` フィールド追加による後方互換性維持。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/bookmarks.json`（既存・`enabled` フィールドを追加）
**Testing**: pytest（既存 conftest.py 使用）
**Target Platform**: Linux デスクトップ (WSL2 環境での動作確認済み)
**Project Type**: デスクトップアプリ（PyQt6 GUI）
**Performance Goals**: タイムラインバー表示 < 1秒、クリック応答 < 0.5秒（SC-001, SC-002）
**Constraints**: 追加ライブラリなし（PyQt6・python-vlc の既存 API のみ使用）
**Scale/Scope**: 単一ユーザー、1動画あたり最大数十件のブックマーク

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | 全US で テスト→実装→リファクタの順序を維持。ユニット + 統合テスト計画あり |
| II. シンプルさ重視 | ✅ PASS | QSlider サブクラス化（最小変更）。VideoInfo は player.py 内のローカル構造体 |
| III. 過度な抽象化の禁止 | ✅ PASS | BookmarkSlider は1箇所だけ使う新ファイル（ただし QSlider の描画責務として正当）。ショートカットダイアログはインライン実装 |
| IV. 日本語コミュニケーション | ✅ PASS | UIラベル・コメント・コミットメッセージは日本語 |

**Post-design re-check**: 設計後も全原則パス。Complexity Tracking 記載事項なし。

## Project Structure

### Documentation (this feature)

```text
specs/005-timeline-seq-info-help/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (変更・追加対象ファイル)

```text
looplayer/
├── bookmark_store.py           # LoopBookmark に enabled フィールド追加
│                               # BookmarkStore.update_enabled() メソッド追加
├── player.py                   # _show_video_info(), _show_shortcut_dialog()
│                               # ヘルプメニュー, ? キー, _video_info_action
│                               # _sync_slider_bookmarks() を各変更点で呼ぶ
└── widgets/
    ├── bookmark_slider.py      # 【新規】BookmarkSlider (QSlider サブクラス)
    ├── bookmark_panel.py       # seq_btn 有効判定を enabled フィルタで変更
    │                           # _on_enabled_changed ハンドラ追加
    └── bookmark_row.py         # チェックボックス追加, enabled_changed シグナル

tests/
├── unit/
│   ├── test_bookmark_slider.py       # 【新規】区間計算・クリック判定
│   ├── test_bookmark_enabled.py      # 【新規】enabled フィールドの永続化
│   └── test_video_info.py            # 【新規】ファイルサイズフォーマット変換
└── integration/
    ├── test_timeline_display.py      # 【新規】ブックマーク追加後の表示確認
    ├── test_sequential_filter.py     # 【新規】enabled=True のみ連続再生
    ├── test_video_info_dialog.py     # 【新規】ダイアログ項目確認
    └── test_shortcut_dialog.py       # 【新規】ショートカット一覧確認
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。`bookmark_slider.py` のみ新規ファイルとして追加（QSlider の描画責務を分離するため正当）。それ以外は既存ファイルへの変更のみ。

## Complexity Tracking

*憲法原則違反なし。記録事項なし。*
