# Implementation Plan: AB Loop Player Improvements

**Branch**: `012-player-improvements` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-player-improvements/spec.md`

## Summary

ABループ特化の語学・楽器練習用プレイヤーとして10の機能を追加する。`I`/`O` キーショートカット（US1）、フレーム単位微調整（US2）、ブックマーク保存時名前入力（US3）、ループ間ポーズ（US4）、連続再生1周停止（US5）、練習カウンター（US6）、フォルダを開くメニュー（US7）、プレイリスト UI（US8）、ブックマークタグ付け（US9）、クリップ書き出しトランスコード（US10）。既存コードへの最小限の追記を基本方針とし、新規クラスは `PlaylistPanel` のみ（UI として独立が必然）。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203、ffmpeg（US10 のトランスコード用、既存）
**Storage**: `~/.looplayer/bookmarks.json`（LoopBookmark 拡張）、`~/.looplayer/settings.json`（AppSettings 拡張）
**Testing**: pytest + pytest-qt（既存テスト 340 件）
**Target Platform**: Linux / Windows / macOS デスクトップアプリ
**Project Type**: デスクトップアプリ
**Performance Goals**: ループ間ポーズ精度 ±200ms（SC-003）
**Constraints**: 後方互換 JSON（既存 bookmarks.json を壊さない）、`Alt+←/→` の既存 `Ctrl+←/→`（±10秒シーク）との競合を避ける
**Scale/Scope**: 単一ユーザー、単一プロセス、ローカルストレージのみ

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 状態 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | 各 US でテスト先行。quickstart.md にシナリオ記載済み |
| II. シンプルさ重視 | ✅ PASS | 既存コードへの追記中心。新規ファイルは `PlaylistPanel` のみ |
| III. 過度な抽象化の禁止 | ✅ PASS | `PlaylistPanel` は UI として独立が必然（Complexity Tracking に記録） |
| IV. 日本語コミュニケーション | ✅ PASS | UI ラベル・コメント・コミットメッセージは日本語 |

## Project Structure

### Documentation (this feature)

```text
specs/012-player-improvements/
├── plan.md              # このファイル
├── research.md          # 技術判断の根拠
├── data-model.md        # エンティティ拡張仕様
├── quickstart.md        # テストシナリオ
├── contracts/
│   └── widget-signals.md  # シグナル/スロット契約
└── tasks.md             # /speckit.tasks で生成
```

### Source Code（変更・新規ファイル）

```text
looplayer/
├── bookmark_store.py       # LoopBookmark に pause_ms, play_count, tags 追加
├── sequential.py           # on_b_reached() → int | None、one_round_mode 追加
├── app_settings.py         # sequential_play_mode, export_encode_mode 追加
├── clip_export.py          # ClipExportJob に encode_mode 追加、ExportWorker を分岐
├── playlist.py             # retreat() メソッド追加
├── i18n.py                 # 新 UI キー追加（US1〜10 のラベル）
├── player.py               # メインウィンドウ（最多変更箇所）
└── widgets/
    ├── bookmark_row.py     # frame_adjust ボタン、pause_spin、play_count、tags UI
    ├── bookmark_panel.py   # タグフィルタ、sequential mode トグル
    ├── playlist_panel.py   # 新規: プレイリスト UI
    └── export_dialog.py    # encode_mode 選択 RadioButton 追加

tests/
├── unit/
│   ├── test_bookmark_store_extensions.py   # pause_ms/play_count/tags の CRUD
│   ├── test_sequential_one_round.py        # 1周停止モード
│   ├── test_frame_adjust.py                # フレーム微調整ロジック
│   ├── test_bookmark_tags.py               # タグフィルタ・OR ロジック
│   └── test_transcode_export.py            # encode_mode の ffmpeg コマンド分岐
└── integration/
    ├── test_ab_shortcuts.py                # I/O ショートカット
    ├── test_bookmark_save_dialog.py        # 保存時名前入力
    ├── test_loop_pause.py                  # ポーズ間隔
    ├── test_play_count.py                  # 練習カウンター
    ├── test_folder_menu.py                 # フォルダを開くメニュー
    └── test_playlist_ui.py                 # プレイリスト UI
```

**Structure Decision**: 既存の単一パッケージ構造を維持。新規ファイルは `playlist_panel.py` のみ。

## Complexity Tracking

| 違反 | 理由 | よりシンプルな代替案を却下した根拠 |
|------|------|----------------------------------|
| 新規クラス `PlaylistPanel` | プレイリスト UI は独立した QWidget として分離しないと `bookmark_panel.py` が肥大化し単一責任の原則を破る | `bookmark_panel.py` に直接追記: ファイルが 500 行超になり既存機能との分離が困難 |

## Implementation Phases

### Phase 1（共有基盤）: データモデル拡張
- `LoopBookmark` に `pause_ms`, `play_count`, `tags` 追加
- `AppSettings` に `sequential_play_mode`, `export_encode_mode` 追加
- `SequentialPlayState.on_b_reached()` を `int | None` に変更
- `ClipExportJob` に `encode_mode` 追加
- `Playlist` に `retreat()` 追加
- `i18n.py` に新キー追加

### Phase 2（US1・US7: 最小工数）
- `I`/`O` ショートカット（player.py への QShortcut 追加）
- フォルダを開くメニュー（player.py + i18n 既存キー実装）

### Phase 3（US3・US6: ブックマーク操作）
- 保存時名前入力（QInputDialog）
- 練習カウンター（_on_timer + BookmarkRow 表示）

### Phase 4（US2・US4: BookmarkRow 拡張）
- フレーム単位微調整ボタン
- ポーズ間隔スピンボックス

### Phase 5（US5: 連続再生モード）
- 1周停止トグル（BookmarkPanel + SequentialPlayState）

### Phase 6（US8: プレイリスト UI）
- `PlaylistPanel` 新規作成
- `QTabWidget` でブックマーク/プレイリスト切り替え
- `Alt+←/→` ショートカット

### Phase 7（US9・US10: P4 機能）
- ブックマークタグ付け
- クリップ書き出しトランスコード

