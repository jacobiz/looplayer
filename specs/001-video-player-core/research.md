# Research: ビデオプレイヤーコア機能

**Date**: 2026-03-15
**Branch**: 001-video-player-core

## 1. VLC アスペクト比保持

**Decision**: VLC はデフォルトでアスペクト比を自動維持する。追加実装不要。

**Rationale**: `python-vlc` の `MediaPlayer` は X11 ウィンドウへの描画時にアスペクト比を
自動的に保持する（レターボックス/ピラーボックス）。`set_aspect_ratio(None)` で
明示的にデフォルト（自動）に戻すことも可能。

**Alternatives considered**:
- `set_aspect_ratio("16:9")` で固定 → 動画ごとに比率が異なるため不適
- QWidget 側でスケーリング処理 → VLC レンダリングに干渉するため不採用

## 2. VLC 再生エラー検出

**Decision**: `MediaPlayerEncounteredError` イベントを購読し、エラー時にダイアログを表示して
直前状態を維持する。

**Rationale**: python-vlc は `EventManager.event_attach()` でメディアイベントを購読できる。
`vlc.EventType.MediaPlayerEncounteredError` が最も直接的なエラー検出手段。
状態確認として `media_player.get_state() == vlc.State.Error` も利用可能。

```python
em = self.media_player.event_manager()
em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)
```

VLC イベントは別スレッドから発火するため、PyQt6 の `QMetaObject.invokeMethod` か
シグナル経由で UI スレッドに渡す必要がある。

**Alternatives considered**:
- タイマーで定期的に `get_state()` をポーリング → 既存タイマー(_on_timer)と統合可能だが
  反応が最大200ms遅延するため、イベント方式を優先

## 3. PyQt6 テスト戦略

**Decision**: `pytest-qt`（`qtbot` フィクスチャ）を使用する。

**Rationale**: pytest-qt は PyQt6 に対応しており、ウィジェット操作・シグナル待機・
クリックシミュレーションを提供する。VLC の実際の再生を伴うテストは統合テストとし、
ロジック単体（`_ms_to_str`、ABループ判定）はユニットテストとして分離する。

**インストール**:
```
pytest-qt>=4.4.0
```

**テスト分類**:
- Unit: VLC 不要のロジック関数（`_ms_to_str`、ABループ条件判定）
- Integration: PyQt6 ウィジェット操作（ボタンクリック、状態確認）。VLC 再生は
  ヘッドレス環境で動作しないため、再生状態の検証は `media_player` のモックを許容する
  （例外的なモック使用：VLC はネイティブライブラリでありテスト時の代替手段がない）

## 4. 既存コードと仕様の差分

| 仕様要件 | 実装状況 | 対応 |
|----------|----------|------|
| FR-001〜014（基本再生・AB） | ✅ 実装済み | テスト追加のみ |
| FR-015（ファイル開けない時のエラー表示・状態維持） | ❌ 未実装 | `_on_media_error` 追加 |
| FR-016（アスペクト比保持） | ✅ VLC デフォルト動作 | 追加実装不要 |
