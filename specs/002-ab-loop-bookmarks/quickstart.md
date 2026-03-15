# Quickstart: AB Loop Bookmarks & Sequential Playback

**Feature**: 002-ab-loop-bookmarks
**Date**: 2026-03-15

---

## 新規ファイル

| ファイル | 役割 |
|---------|------|
| `bookmark_store.py` | `LoopBookmark` データクラス + `BookmarkStore` JSON永続化 |

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `main.py` | `BookmarkPanel` ウィジェット追加、`VideoPlayer._on_timer()` 拡張、`SequentialPlayState` 統合 |

## テストファイル（新規）

| ファイル | テスト対象 |
|---------|----------|
| `tests/unit/test_bookmark_store.py` | `LoopBookmark` バリデーション、`BookmarkStore` CRUD・永続化 |
| `tests/unit/test_sequential_play.py` | `SequentialPlayState` 状態遷移ロジック |
| `tests/integration/test_bookmark_integration.py` | パネルからのブックマーク保存・切り替え・連続再生の統合フロー |

---

## 実装の流れ（テストファースト）

### Step 1: `bookmark_store.py` のテストと実装

```bash
# テスト作成 → 失敗確認 → 実装 → テスト通過
pytest tests/unit/test_bookmark_store.py -v  # まず RED
# bookmark_store.py を実装
pytest tests/unit/test_bookmark_store.py -v  # GREEN
```

### Step 2: 連続再生ロジックのテストと実装

```bash
pytest tests/unit/test_sequential_play.py -v  # まず RED
# main.py に SequentialPlayState を追加
pytest tests/unit/test_sequential_play.py -v  # GREEN
```

### Step 3: UI統合（BookmarkPanel）と統合テスト

```bash
pytest tests/integration/test_bookmark_integration.py -v  # まず RED
# main.py に BookmarkPanel を組み込み
pytest tests/integration/test_bookmark_integration.py -v  # GREEN
```

### 全テスト確認

```bash
pytest tests/ -v
python main.py  # 動作確認
```

---

## UIレイアウトの変更

```
┌──────────────────────────────────────────────────┐
│  [動画フレーム]                                    │
│                                                  │
├──────────────────────────────────────────────────┤
│  シークバー ────────────────── 00:00 / 00:00      │
├──────────────────────────────────────────────────┤
│  [開く] [再生] [停止]                              │
├──────────────────────────────────────────────────┤
│  [A点セット] [B点セット] [ABループ:OFF] [ABリセット]│
│  A: --  B: --                                    │
├──────────────────────────────────────────────────┤
│  [ブックマーク保存]  ← A・B点設定済み時のみ有効    │
│  ──────────────────────────────────────────────  │
│  ブックマーク一覧:                   [連続再生]    │
│  ┌──────────────────────────────────────────┐   │
│  │ サビ部分  A:01:02 B:01:18  繰返:[3▲▼] [×] │   │
│  │ Aメロ    A:00:10 B:00:30  繰返:[1▲▼] [×] │   │
│  └──────────────────────────────────────────┘   │
│  （連続再生中）現在: サビ部分 → 次: Aメロ          │
└──────────────────────────────────────────────────┘
```

---

## 主要な設計判断

1. **単一ファイル拡張を避ける**: `bookmark_store.py` を分離することで `main.py` の肥大化を防ぎつつ、テストを独立して書ける
2. **既存タイマー流用**: 新しいタイマーを作らず `_on_timer()` に連続再生ロジックを追加（憲法 III: 過度な抽象化の禁止）
3. **UI統合テストはモックなし**: 実際の `BookmarkStore` を使い、一時ディレクトリにJSONを書いてテストする（憲法 I: 統合テストはモック不使用）
