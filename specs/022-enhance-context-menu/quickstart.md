# Quickstart: コンテキストメニューの充実

## 変更対象ファイル

```text
looplayer/
├── bookmark_store.py          # insert_after() 追加
├── i18n.py                    # ctx.* / bookmark.copy_suffix キー追加
├── player.py                  # 動画エリアコンテキストメニュー実装
└── widgets/
    ├── bookmark_panel.py      # シグナル追加・空白エリアメニュー実装
    └── bookmark_row.py        # シグナル追加・rename 抽出・メニュー拡充

tests/
├── unit/
│   ├── test_bookmark_store_insert_after.py   # NEW (US-2 複製用)
│   ├── test_bookmark_row_ctx_menu.py         # NEW (US-2 拡充)
│   └── test_bookmark_panel_ctx_menu.py       # NEW (US-3 空白エリア)
└── integration/
    └── test_video_ctx_menu.py                # NEW (US-1 動画エリア)
```

## 実装順序

```
1. i18n.py に新キーを追加する
2. bookmark_store.py に insert_after() を追加する
3. tests/unit/test_bookmark_store_insert_after.py を書いてパスさせる
4. bookmark_row.py にシグナル追加・_start_rename() 抽出・メニュー拡充する
5. tests/unit/test_bookmark_row_ctx_menu.py を書いてパスさせる
6. bookmark_panel.py にシグナル追加・空白エリアメニュー・ハンドラ追加する
7. tests/unit/test_bookmark_panel_ctx_menu.py を書いてパスさせる
8. player.py に動画エリアオーバーレイ・コンテキストメニュー実装する
9. tests/integration/test_video_ctx_menu.py を書いてパスさせる
10. 既存テスト全件パスを確認してコミットする
```

## 主要 API サマリー

### BookmarkStore.insert_after
```python
store.insert_after(video_path, new_bm, after_id="some-uuid")
```

### BookmarkPanel 新シグナル
```python
panel.seek_to_ms_requested.connect(lambda ms: media_player.set_time(ms))
```

### VideoPlayer での接続
```python
# player.py _build_ui() 末尾
self.bookmark_panel.seek_to_ms_requested.connect(self._on_seek_to_ms)
```

### 動画エリアオーバーレイ
```python
# video_frame の子として追加、resizeEvent で追従
self._video_ctx_overlay = QWidget(self.video_frame)
self._video_ctx_overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
self._video_ctx_overlay.resize(self.video_frame.size())
self._video_ctx_overlay.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._video_ctx_overlay.customContextMenuRequested.connect(self._show_video_context_menu)
self._video_ctx_overlay.raise_()
```

## テスト実行方法

```bash
pytest tests/ -v
```
