# Tasks: P1優先度機能の実装

**Input**: Design documents from `/specs/016-p1-features/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Organization**: タスクはユーザーストーリー単位で整理。各ストーリーは独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル・依存なし）
- **[Story]**: 対応するユーザーストーリー（US1/US2/US3）
- 各タスクに具体的なファイルパスを明記

---

## Phase 1: Setup（ベースライン確認）

**Purpose**: 実装前にテストスイートがクリーンな状態であることを確認する

- [X] T001 ベースラインテストがすべて通ることを確認する: `pytest tests/ -v`

---

## Phase 2: Foundational（共通基盤 — 全ストーリーの前提）

**Purpose**: US1・US2・US3 が依存する i18n キーを先行追加する（US2 は `menu.view.reset_window` キーを使用）。テストファースト原則に従い、まずテストを書いて RED を確認してから実装する。

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの実装は開始しない

- [X] T002 [P] F-201 字幕メッセージキー・F-403 メニューキー（`menu.view.reset_window`）・F-502 ツールチップキーの新規追加に対する失敗テストを `tests/unit/test_i18n.py` に追記する（RED を確認すること）
- [X] T003 `looplayer/i18n.py` に `data-model.md` 記載の全新規キー（字幕 7 件・ウィンドウ 1 件・ツールチップ 16 件）を追記し T002 を GREEN にする

**Checkpoint**: `pytest tests/unit/test_i18n.py -v` がすべて通ること

---

## Phase 3: User Story 1 — 外部字幕ファイルの読み込み（F-201）🎯

**Goal**: 語学学習者が SRT/ASS 字幕ファイルをメニューから読み込み、字幕付き AB ループ練習を開始できる

**Independent Test**: メニューから SRT ファイルを選択すると字幕が表示され、別の動画を開くと字幕がリセットされる

### Tests for User Story 1

> **テストを書いて RED を確認してから実装すること（constitution I 必須）**

- [X] T004 [P] [US1] 以下のシナリオを含む統合テストを `tests/integration/test_subtitles.py` に新規作成する（RED を確認すること。実 VLC インスタンス使用、モック不可）:
  - 動画未選択時に「字幕ファイルを開く」を呼ぶとエラーメッセージが表示される（FR-103）
  - 動画再生中に有効な SRT ファイルを選択すると字幕が読み込まれる（FR-102）
  - 非対応拡張子（.txt など）を選択するとフォーマットエラーが表示される（FR-104）
  - 別の動画を開くと外部字幕パスがリセットされる（FR-106）
  - 外部字幕読み込み後に字幕メニューで内蔵字幕トラックへ切り替えができる（FR-105）

### Implementation for User Story 1

- [X] T005 [US1] `looplayer/player.py` の `__init__` に `self._external_subtitle_path: Path | None = None` を追加し、`_open_subtitle_file()` メソッドを実装する（`add_slave` 呼び出し・拡張子バリデーション・エラーダイアログを含む）
- [X] T006 [US1] `looplayer/player.py` の `_build_menus()` で字幕メニューにセパレータと「字幕ファイルを開く」QAction を追加し `_open_subtitle_file()` に接続する（T003 の i18n キー使用）
- [X] T007 [US1] `looplayer/player.py` の `_open_video()` 内で `self._external_subtitle_path = None` によるリセット処理を追加する

**Checkpoint**: `pytest tests/integration/test_subtitles.py -v` がすべて通ること

---

## Phase 4: User Story 2 — ウィンドウ位置・サイズの記憶（F-403）

**Goal**: 再起動後も前回終了時と同じウィンドウ位置・サイズで起動する。フルスクリーン中に終了しても前回のウィンドウ状態に戻る

**Independent Test**: ウィンドウを移動してアプリを終了し再起動すると同じ位置で表示される

### Tests for User Story 2

> **テストを書いて RED を確認してから実装すること（constitution I 必須）**

- [X] T008 [P] [US2] `tests/unit/test_app_settings.py` に `window_geometry` プロパティのユニットテストを追記する（RED を確認すること）:
  - デフォルト（キーなし）は `None` を返す
  - 有効な dict をセット→保存→リロードで同値が返る
  - `None` をセットするとキーが削除される
  - 必須フィールド欠損の dict は `None` を返す
- [X] T009 [P] [US2] 以下のシナリオを含む統合テストを `tests/integration/test_window_geometry.py` に新規作成する（RED を確認すること）:
  - ジオメトリを設定して再起動すると同じ位置・サイズで復元される
  - 画面外座標の場合はプライマリスクリーン中央に補正される
  - `width < 800` または `height < 600` の場合は最小値に補正される
  - フルスクリーン中に終了するとフルスクリーン前のジオメトリが保存される
  - 「ウィンドウ位置をリセット」を選択すると `window_geometry` が `None` になる

### Implementation for User Story 2

- [X] T010 [US2] `looplayer/app_settings.py` に `window_geometry: dict | None` プロパティ（getter/setter）を追加して T008 を GREEN にする
- [X] T011 [US2] `looplayer/player.py` に以下を追加して T009 を GREEN にする:
  - `__init__` に `self._pre_fullscreen_geometry: QRect | None = None`
  - `_restore_window_geometry()` メソッド（画面外チェック・最小サイズ補正を含む）
  - コンストラクタ末尾で `_restore_window_geometry()` を呼ぶ
  - `toggle_fullscreen()` の `showFullScreen()` 前に `self._pre_fullscreen_geometry = self.geometry()` を追加
  - `_exit_fullscreen()` で `_pre_fullscreen_geometry` を `None` にリセット
- [X] T012 [US2] `looplayer/player.py` の `closeEvent()` でジオメトリを保存する処理を追加し、`_build_menus()` の表示メニューに「ウィンドウ位置をリセット」QAction と `_reset_window_geometry()` メソッドを追加する（T003 の i18n キー使用、T010・T011 に依存）

**Checkpoint**: `pytest tests/unit/test_app_settings.py tests/integration/test_window_geometry.py -v` がすべて通ること

---

## Phase 5: User Story 3 — ツールチップの充実（F-502）

**Goal**: すべての主要コントロールにマウスを乗せると機能とショートカットキーを説明するツールチップが表示される

**Independent Test**: 再生/停止ボタン・+1F/-1F ボタン・A/B 点ボタンのツールチップを確認できる

### Tests for User Story 3

> **テストを書いて RED を確認してから実装すること（constitution I 必須）**

- [X] T013 [P] [US3] 以下のウィジェットのツールチップ文字列が空でないことを検証する統合テストを `tests/integration/test_tooltips.py` に新規作成する（RED を確認すること）。対象スコープは FR-304 の最小スコープとし、既存ツールチップ（`bookmark.row.memo_tip`/`delete_tip`/`enabled_tip`）は対象外:
  - 再生/停止ボタン（`play_btn`）
  - シークバー（`seek_slider`）
  - 音量スライダー（`volume_slider`）
  - 再生フレーム移動ボタン（`frame_minus_btn`, `frame_plus_btn`、ラベル -1F/+1F）
  - A/B 点フレーム調整ボタン 4 種（`frame_a_minus_btn`, `frame_a_plus_btn`, `frame_b_minus_btn`, `frame_b_plus_btn`）
  - A 点セットボタン・B 点セットボタン
  - AB ループトグルボタン
  - ポーズ間隔スピンボックス
  - ブックマーク行のタグ編集ボタン・再生回数リセットボタン

### Implementation for User Story 3

- [X] T014 [P] [US3] `looplayer/player.py` のコントロール初期化箇所に `setToolTip(t("tooltip.key"))` を追加して T013 を GREEN にする（対象: play_btn, seek_slider, volume_slider, frame_minus_btn, frame_plus_btn, frame_a_minus_btn, frame_a_plus_btn, frame_b_minus_btn, frame_b_plus_btn, set_a_btn, set_b_btn, ab_loop_btn, pause_interval_spin）（T003 に依存）
- [X] T015 [P] [US3] `looplayer/widgets/bookmark_row.py` のタグ編集ボタン・再生回数リセットボタンに `setToolTip(t("tooltip.key"))` を追加する（T003 に依存）

**Checkpoint**: `pytest tests/integration/test_tooltips.py -v` がすべて通ること

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全ストーリーにまたがる最終確認

- [X] T016 [P] `pytest tests/ -v` でテストスイート全体を実行し、失敗・警告がゼロであることを確認する
- [X] T017 `looplayer/player.py` の変更箇所（字幕・ジオメトリ・ツールチップ）に対してコードスタイル（PEP 8）を確認し必要に応じて修正する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即開始可能
- **Foundational (Phase 2)**: Phase 1 完了後 — 全ストーリーをブロック
- **US1/US2/US3 (Phase 3–5)**: Phase 2 完了後に並列実行可能
- **Polish (Phase 6)**: 全ストーリー完了後

### User Story Dependencies

- **US1 (字幕, Phase 3)**: Phase 2 完了後 — 他ストーリーへの依存なし
- **US2 (ウィンドウ, Phase 4)**: Phase 2 完了後 — 他ストーリーへの依存なし
- **US3 (ツールチップ, Phase 5)**: Phase 2 完了後 — 他ストーリーへの依存なし

### Within Each User Story

1. テストを書いて RED を確認（constitution I 必須）
2. 最小限のコードで GREEN にする
3. リファクタリング
4. ストーリーチェックポイントを確認してからコミット

### Parallel Opportunities

- T004・T008・T009・T013 は Phase 2 完了後に並列実行可能（独立した新規テストファイル）
- T014 と T015 は並列実行可能（別ファイル）
- US1・US2・US3 の各フェーズは 3 人で並列実装可能

---

## Parallel Example: Phase 3–5 を並列実行する場合

```bash
# Phase 2 完了後、以下のテスト作成を並列で進める:
Task A: "T004 - test_subtitles.py を作成して RED を確認"
Task B: "T008+T009 - test_app_settings.py と test_window_geometry.py を作成して RED を確認"
Task C: "T013 - test_tooltips.py を作成して RED を確認"

# テスト RED 確認後、実装を並列で進める:
Task A: "T005→T006→T007 - 字幕読み込み実装"
Task B: "T010→T011→T012 - ウィンドウジオメトリ実装"
Task C: "T014+T015 - ツールチップ追加"
```

---

## Implementation Strategy

### MVP First（US2 → US3 → US1 の推奨実装順）

実装順序は仕様の US 番号に縛られない。影響範囲の小さい順に進めてリスクを低減する:

1. **Phase 2** (T002–T003): i18n 基盤を確立
2. **Phase 4** (T008–T012): `AppSettings` 単体変更 → 最もリスクが低い
3. **Phase 5** (T013–T015): `player.py` + `bookmark_row.py` へのツールチップ追加 → 動作変更なし
4. **Phase 3** (T004–T007): `add_slave` API 呼び出し → VLC API 依存のため最後に実施

各ストーリー完了後に `pytest tests/ -v` を実行してリグレッションがないことを確認すること。

### Incremental Delivery

1. T001–T003 完了 → i18n 基盤確立
2. T004–T007 完了 → 字幕機能リリース可能
3. T008–T012 完了 → ウィンドウ記憶リリース可能
4. T013–T015 完了 → ツールチップリリース可能（= 全 P1 機能完成）
5. T016–T017 完了 → リリース準備完了

---

## Notes

- [P] タスク = 異なるファイル・依存なし → 並列実行可
- テストは実装前に必ず RED を確認すること（constitution I）
- 各ストーリーチェックポイントでテストをパスしてからコミット
- `player.py` は 1600 行超のため、編集前に対象箇所を Read ツールで確認してから編集する
- `add_slave()` の検証は既存統合テストと同じパターン（実 VLC インスタンス + テスト用動画ファイル）で行う。モックは使用しない（constitution I: 統合テストはモックではなく実際の依存を使う）
