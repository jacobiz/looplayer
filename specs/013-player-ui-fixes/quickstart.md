# Quickstart: プレイヤー UI バグ修正・操作性改善

**Branch**: `013-player-ui-fixes`

## 開発環境の確認

```bash
# 現在のブランチを確認
git branch

# 依存関係のインストール確認
pip install PyQt6 python-vlc pytest pytest-qt

# テスト実行（全体）
pytest tests/ -v

# 特定のテストファイルのみ
pytest tests/integration/test_fullscreen.py -v
pytest tests/unit/test_bookmark_slider.py -v
```

## 実装の流れ（テストファースト）

### Step 1: US1 — ESC キー修正

```bash
# テスト追加（失敗を確認）
pytest tests/integration/test_fullscreen.py -v -k "esc"

# 実装後に再実行（通過を確認）
pytest tests/integration/test_fullscreen.py -v
```

変更ファイル: `looplayer/player.py`

```python
# __init__ または _setup_shortcuts 内に追加
from PyQt6.QtGui import QShortcut, QKeySequence
esc_sc = QShortcut(QKeySequence("Escape"), self)
esc_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
esc_sc.activated.connect(self._exit_fullscreen)
```

### Step 2: US2 — AB 点シークバープレビュー

```bash
pytest tests/unit/test_bookmark_slider.py -v -k "ab_preview"
```

変更ファイル: `looplayer/widgets/bookmark_slider.py`（`set_ab_preview` メソッド追加）、`looplayer/player.py`（呼び出し追加）

### Step 3: US3 — AB 点ドラッグ

```bash
pytest tests/unit/test_bookmark_slider.py -v -k "ab_drag"
pytest tests/integration/test_ab_seekbar.py -v
```

変更ファイル: `looplayer/widgets/bookmark_slider.py`（マウスイベント拡張）、`looplayer/player.py`（`_on_ab_drag_finished` 追加）

### Step 4: US4 — スピンボックス幅修正

```bash
pytest tests/unit/test_bookmark_row_layout.py -v
```

変更ファイル: `looplayer/widgets/bookmark_row.py`

## 動作確認

```bash
python main.py
```

確認項目:
1. F キーでフルスクリーン → ESC で解除（スピンボックスにフォーカスがある状態でも）
2. A 点セット → シークバーに白い縦線表示
3. B 点セット → シークバーに A〜B 白い半透明バー表示
4. バー端の縦線付近をドラッグ → A/B 点が移動
5. ブックマーク行の「繰返」「ポーズ」の数値が読めること
