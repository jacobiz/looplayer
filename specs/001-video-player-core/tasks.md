# Tasks: ビデオプレイヤーコア機能

**Input**: Design documents from `/specs/001-video-player-core/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: タスクはユーザーストーリー単位でグループ化されており、各ストーリーを独立して実装・テストできます。

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: 対象ユーザーストーリー（US1, US2）
- 各タスクに実際のファイルパスを含める

---

## Phase 1: Setup（プロジェクト初期化）

**Purpose**: テスト基盤の構築

- [x] T001 pytest と pytest-qt を requirements.txt に追加（`pytest>=8.0.0`, `pytest-qt>=4.4.0`）
- [x] T002 [P] `tests/unit/` ディレクトリと `tests/unit/__init__.py` を作成
- [x] T003 [P] `tests/integration/` ディレクトリと `tests/integration/__init__.py` を作成
- [x] T004 `tests/conftest.py` を作成（pytest-qt の `qt_app` フィクスチャ設定）

---

## Phase 2: Foundational（共通基盤）

**Purpose**: 全ユーザーストーリーが共有するテストフィクスチャの準備

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの作業を開始しない

- [x] T005 `tests/conftest.py` に `VideoPlayer` インスタンスを生成する `player` フィクスチャを追加
  （`qtbot` を使い、テスト後に `media_player.stop()` でクリーンアップ）

**Checkpoint**: フィクスチャが動作することを `pytest tests/ --collect-only` で確認してから進む

---

## Phase 3: User Story 1 - 動画ファイルの再生（Priority: P1）🎯 MVP

**Goal**: ファイルを開き、再生・一時停止・停止・シーク、時刻表示が正しく動作することを検証する。
加えて FR-015（ファイルエラー時のハンドリング）を実装する。

**Independent Test**: `pytest tests/unit/test_ms_to_str.py tests/integration/test_playback.py tests/integration/test_error_handling.py -v`

### テスト for US1（先に書いて、失敗を確認してから実装）

> **⚠️ NOTE: テストを書き、RED（失敗）を確認してから T009 の実装へ進むこと**

- [x] T006 [P] [US1] `tests/unit/test_ms_to_str.py` を作成し `_ms_to_str` のユニットテストを記述
  - `None` → `"00:00"`, `0` → `"00:00"`, `60000` → `"01:00"`, `3661000` → `"01:01:01"`
- [x] T007 [P] [US1] `tests/integration/test_playback.py` を作成し再生制御の統合テストを記述
  - 初期状態確認（ボタンラベル・スライダー位置）
  - `play_btn` クリック時のラベル変化
  - `stop_btn` クリック後のスライダー/時刻表示リセット
- [x] T008 [P] [US1] `tests/integration/test_error_handling.py` を作成し FR-015 のテストを記述
  - 存在しないパスを `open_file()` に渡したとき `QMessageBox` が表示されること
  - エラー後に直前の `media_player` 状態が維持されること
  - （このテストは T009 実装前に RED になることを確認する）

### 実装 for US1

- [x] T009 [US1] `main.py` の `VideoPlayer.__init__` に VLC `MediaPlayerEncounteredError` イベント購読を追加
  ```python
  em = self.media_player.event_manager()
  em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)
  ```
- [x] T010 [US1] `main.py` に `_on_media_error` メソッドを追加
  - VLC イベントスレッドから UI スレッドへ安全に委譲（`QMetaObject.invokeMethod` 使用）
  - `QMessageBox.warning(self, "エラー", "動画ファイルを開けませんでした。")` を表示
  - `media_player` の状態変更は行わない（直前状態を維持）

**Checkpoint**: `pytest tests/unit/test_ms_to_str.py tests/integration/test_error_handling.py -v` が全てパスすること

---

## Phase 4: User Story 2 - ABループ再生（Priority: P2）

**Goal**: A点・B点のセット、ABループ ON/OFF、リセットが正しく動作することを検証する。

**Independent Test**: `pytest tests/unit/test_ab_loop_logic.py tests/integration/test_ab_loop.py -v`

### テスト for US2（先に書いて、失敗を確認してから実装）

> **⚠️ NOTE: 既存コードが仕様を満たしているか、テストによって確認する**

- [x] T011 [P] [US2] `tests/unit/test_ab_loop_logic.py` を作成し ABループ判定ロジックのユニットテストを記述
  - A のみセット時にループが発動しないこと
  - B のみセット時にループが発動しないこと
  - A/B 両方セット・`ab_loop_active=True`・`current_ms >= ab_point_b` のとき発動すること
  - 終端到達後も `ab_loop_active` が維持されること（動画停止でフラグ変更なし）
- [x] T012 [P] [US2] `tests/integration/test_ab_loop.py` を作成し ABループ操作フローの統合テストを記述
  - `set_point_a()` 呼び出し後に `ab_point_a` が設定され UI ラベルが更新されること
  - `set_point_b()` 呼び出し後に `ab_point_b` が設定され UI ラベルが更新されること
  - `toggle_ab_loop(True)` 後にボタンラベルが「ABループ: ON」になること
  - `reset_ab()` 後に全状態がクリアされ UI が「A: --  B: --」に戻ること

### 実装 for US2

- [x] T013 [US2] テスト実行・全パス確認（既存 ABループコードの検証）
  `pytest tests/unit/test_ab_loop_logic.py tests/integration/test_ab_loop.py -v`
  失敗がある場合は `main.py` の該当ロジックを修正する

**Checkpoint**: US1・US2 の全テストが通ること
`pytest tests/ -v` でグリーンを確認

---

## Phase 5: Polish & Cross-Cutting

**Purpose**: 全ストーリー横断の品質確認

- [x] T014 [P] `quickstart.md` の手動検証チェックリストを実際に実行して確認
- [x] T015 [P] `CLAUDE.md` の Commands セクションを最終化（`pytest tests/ -v` が正しく動くことを確認）
- [x] T016 全テスト実行・最終確認: `pytest tests/ -v --tb=short`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即開始可能
- **Foundational (Phase 2)**: Phase 1 完了後
- **US1 (Phase 3)**: Phase 2 完了後 — テスト先行（T006-T008）→ 実装（T009-T010）
- **US2 (Phase 4)**: Phase 2 完了後（US1 完了を待たず開始可能）
- **Polish (Phase 5)**: US1・US2 の完了後

### Within Each User Story

1. テスト記述（`[P]` タスクは並列）
2. テストが **RED** であることを確認
3. 実装
4. テストが **GREEN** であることを確認
5. リファクタリング（必要な場合のみ）

### Parallel Opportunities

```bash
# Phase 1 並列実行例
Task: T002 tests/unit/ ディレクトリ作成
Task: T003 tests/integration/ ディレクトリ作成

# US1 テスト並列実行例
Task: T006 tests/unit/test_ms_to_str.py
Task: T007 tests/integration/test_playback.py
Task: T008 tests/integration/test_error_handling.py

# US2 テスト並列実行例
Task: T011 tests/unit/test_ab_loop_logic.py
Task: T012 tests/integration/test_ab_loop.py
```

---

## Implementation Strategy

### MVP First（US1 のみ）

1. Phase 1: Setup 完了
2. Phase 2: Foundational 完了
3. Phase 3: US1（テスト → FR-015 実装）
4. **STOP and VALIDATE**: `pytest tests/unit/ tests/integration/test_playback.py tests/integration/test_error_handling.py -v`

### Incremental Delivery

1. Setup + Foundational → テスト基盤完成
2. US1 → テスト追加 + FR-015 実装 → **MVP！**
3. US2 → テスト追加 + 既存コード検証

---

## Notes

- `[P]` = 別ファイル・依存なし、並列実行可
- `[US?]` = どのユーザーストーリーのタスクかを示す
- VLC 再生を伴う統合テストはヘッドレス環境では動作しない可能性がある（GUI 環境で実行）
- モックは VLC ネイティブライブラリに限定して許容（research.md に根拠記載済み）
- コミットは各フェーズ完了後、またはチェックポイントごとに行う
