# Quickstart: 024-seekbar-zoom-position

## 概要

ズームモード有効時、QSlider のハンドル（現在位置マーカー）がズーム範囲内の正確な位置に表示されるようにする。

## 変更ファイル

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `looplayer/widgets/bookmark_slider.py` | 追加 | `set_position_ms(current_ms: int)` メソッド |
| `looplayer/player.py` | 修正 | `_on_timer()` の `setValue` → `set_position_ms` 呼び出し |
| `tests/unit/test_bookmark_slider_zoom.py` | 追加 | `set_position_ms` のユニットテスト（テストファースト） |

## 実装手順（テストファースト）

1. `test_bookmark_slider_zoom.py` に `TestSetPositionMs` クラスを追加（赤テスト）
2. `bookmark_slider.py` に `set_position_ms()` メソッドを実装（テスト通過）
3. `player.py` の `_on_timer()` を修正（統合確認）
4. 全テスト実行: `pytest tests/unit/test_bookmark_slider_zoom.py -v`

## 動作確認

```bash
python main.py
# 1. 動画を開く
# 2. AB 点を設定してズームを有効化
# 3. 再生中にシークバーのハンドルがズーム範囲内の正しい位置に表示されることを確認
# 4. ズームを解除して通常位置に戻ることを確認
```
