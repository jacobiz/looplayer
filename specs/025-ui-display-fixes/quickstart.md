# Quickstart: 025-ui-display-fixes

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `looplayer/app_settings.py` | `bookmark_panel_visible` デフォルト `False` → `True` |
| `looplayer/player.py` | A点・B点アイコン変更（2行） |
| `tests/unit/test_app_settings.py` | デフォルト値テスト追加 |

## 動作確認

```bash
# 1. 設定ファイルを退避して初回起動相当の状態を作る
mv ~/.looplayer/settings.json ~/.looplayer/settings.json.bak 2>/dev/null || true

# 2. アプリ起動
python main.py
# → ブックマークサイドパネルが表示されていることを確認
# → A点セットボタンが SP_FileDialogStart アイコン（|◀ 相当）になっていることを確認
# → B点セットボタンが SP_FileDialogEnd アイコン（▶| 相当）になっていることを確認

# 3. 設定を戻す
mv ~/.looplayer/settings.json.bak ~/.looplayer/settings.json 2>/dev/null || true
```
