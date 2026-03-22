# Quickstart: ボタンアイコン追加

**Branch**: `023-button-icons` | **Date**: 2026-03-22

---

## 手動検証シナリオ

### シナリオ 1 — US1: 主要再生ボタン確認

```bash
python main.py
```

**確認手順**:
1. アプリ起動直後に再生エリア下のコントロールバーを確認
2. 「開く」ボタンにフォルダアイコンが表示されている ✓
3. 「再生」ボタンに ▶ アイコンが表示されている（グレーアウト状態） ✓
4. 「停止」ボタンに ■ アイコンが表示されている ✓
5. 動画ファイルを開く → 再生開始後「再生/一時停止」ボタンが ‖ アイコンに変わる ✓
6. 一時停止 → ▶ アイコンに戻る ✓

---

### シナリオ 2 — US2: ABループボタン確認

1. 動画を開く
2. ABループエリアのボタンを確認:
   - 「A点セット」に |◄◄ 系アイコン ✓
   - 「B点セット」に ►► | 系アイコン ✓
   - 「ABループ: OFF」にループアイコン（通常色） ✓
   - 「ABリセット」にリセットアイコン ✓
3. A点・B点を設定して「ABループ: OFF」をクリック
4. ボタンが pressed/checked スタイル（強調色）に変わる ✓
5. 再度クリック → 通常スタイルに戻る ✓

---

### シナリオ 3 — US3: その他ボタン確認

1. A点・B点を設定する（ブックマーク保存・ズームボタンが有効化される）
2. 「ブックマーク保存」ボタンに保存アイコンが表示されている ✓
3. 「ズーム」ボタンに拡大表示アイコンが表示されている（通常色） ✓
4. 「ズーム」をクリック → checked スタイルに変わる ✓

---

### シナリオ 4 — FR-009: フォールバック確認（開発時のみ）

テストコードで `style().standardIcon()` をモックして null を返す:

```python
from unittest.mock import patch
from PyQt6.QtGui import QIcon

with patch.object(player, 'style') as mock_style:
    mock_style.return_value.standardIcon.return_value = QIcon()
    player._apply_btn_icon(player.open_btn, QStyle.StandardPixmap.SP_DirOpenIcon)

# open_btn はアイコン未設定（テキスト "開く" のまま）
assert player.open_btn.icon().isNull()
```

---

### シナリオ 5 — FR-010: ツールチップ確認

各ボタンにマウスを hover して以下を確認:
- 「開く」: ツールチップが表示される ✓
- 「停止」: ツールチップが表示される ✓
- 「ABリセット」: ツールチップが表示される ✓
- 「ブックマーク保存」: ツールチップが表示される ✓

---

## テスト実行

```bash
# 全テスト
pytest tests/ -v

# このフィーチャーのテストのみ
pytest tests/integration/test_button_icons_p1.py \
       tests/integration/test_button_icons_p2.py \
       tests/integration/test_button_icons_p3.py -v
```
