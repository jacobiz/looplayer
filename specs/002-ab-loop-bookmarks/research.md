# Research: AB Loop Bookmarks & Sequential Playback

**Feature**: 002-ab-loop-bookmarks
**Date**: 2026-03-15

---

## 1. JSON ブックマーク保存先

**Decision**: `~/.looplayer/bookmarks.json`（クロスプラットフォーム共通パス）

**Rationale**:
- `pathlib.Path.home() / ".looplayer" / "bookmarks.json"` で Linux・Windows・macOS 全て統一できる
- `platformdirs` 等の追加依存なしで実現できる（憲法 II: シンプルさ重視）
- ファイルが存在しない場合は空の辞書として扱い、初回起動時に自動作成する

**Alternatives considered**:
- `~/.config/looplayer/bookmarks.json`（XDG準拠）— Linux では標準的だが Windows では `~/.config` が不自然
- `%APPDATA%/looplayer/bookmarks.json`（Windows標準）— OS 分岐が必要で複雑化

**Format**:
```json
{
  "/abs/path/to/video.mp4": [
    {
      "id": "uuid-string",
      "name": "サビ部分",
      "point_a_ms": 62000,
      "point_b_ms": 78000,
      "repeat_count": 3,
      "order": 0
    }
  ]
}
```

---

## 2. PyQt6 ドラッグ＆ドロップによる並び替え

**Decision**: `QListWidget` + `InternalMove` モード + ドロップ後に行順を永続化

**Rationale**:
- `QListWidget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)` を設定するだけで内部行移動が有効化される
- `model().rowsMoved` シグナルで並び替え後のイベントを取得できる
- 各行にカスタムウィジェットを `setItemWidget()` で設定している場合、ドラッグ操作後にウィジェットを再適用する必要がある

**Implementation note**:
- `dropEvent` をオーバーライドして `super().dropEvent(event)` 呼び出し後に永続化処理を行う

---

## 3. 連続再生の実装方針

**Decision**: 既存の `_on_timer()` タイマーコールバックを拡張する

**Rationale**:
- `VideoPlayer` はすでに200ms間隔のポーリングタイマーを持っており、ABループの境界チェックもここで行っている
- 連続再生状態（`SequentialPlayState`）をフィールドとして持ち、タイマーコールバック内で「B点到達時に次のブックマークへ移動する」ロジックを追加する
- 既存の ABループ OFF 状態と排他制御とする（連続再生中は通常ABループを無効化）

**State machine**:
```
通常再生 → [連続再生開始] → 区間N再生中 → [B点到達] → repeat_countを消費
                                                      → [残り回数=0] → 区間N+1へ
                                                      → [最終区間終了] → 区間0へ戻る
                         → [停止操作] → 通常再生
```

---

## 4. ブックマーク一覧UIの行ウィジェット設計

**Decision**: `QListWidget` + `setItemWidget()` でカスタム行ウィジェットを使用

**Rationale**:
- 各行に「名前」「A点/B点表示」「繰り返し回数スピンボックス」「削除ボタン」を配置するため、カスタムウィジェットが必要
- `QListWidgetItem` + `setItemWidget(item, widget)` パターンで実装
- 名前のインライン編集は `QListWidgetItem.setFlags(... | Qt.ItemFlag.ItemIsEditable)` を使用せず、ダブルクリックで `QInputDialog.getText()` を呼ぶシンプルな方法を採用（スピンボックスとの競合を避けるため）

**行ウィジェットのレイアウト**:
```
[選択インジケーター] | 名前（ダブルクリックで編集）| A:mm:ss B:mm:ss | 繰返:[SpinBox] | [削除]
```

---

## 5. 既存 ABループとブックマーク切り替えの統合

**Decision**: ブックマーク選択時に `VideoPlayer` のAB状態（`ab_point_a`, `ab_point_b`, `ab_loop_active`）を直接更新する

**Rationale**:
- 既存の `_on_timer()` はすでに `ab_point_a/b` と `ab_loop_active` を参照してループ制御している
- ブックマーク選択時にこれらを上書きするだけで、既存のループ機構をそのまま流用できる
- 新たな抽象レイヤーは不要（憲法 III: 過度な抽象化の禁止）
