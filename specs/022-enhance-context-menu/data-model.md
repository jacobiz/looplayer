# Data Model: コンテキストメニューの充実

## 変更・追加エンティティ

### BookmarkStore（変更）

新規メソッド: `insert_after(video_path, bookmark, after_id)`

```
insert_after(
  video_path: str,         # 動画ファイルの絶対パス
  bookmark: LoopBookmark,  # 挿入するブックマーク（order は自動設定）
  after_id: str            # このIDのブックマークの直後に挿入する
) -> None
```

- 指定 ID のブックマークが存在しない場合は末尾に追加する（フォールバック）
- 挿入後に全件の `order` を 0 から再採番する
- 最後に `_save_all()` を一回だけ呼ぶ（アトミック保存）

### BookmarkRow（変更）

追加シグナル:
```
jump_to_a_requested = pyqtSignal(str)    # bookmark_id
duplicate_requested = pyqtSignal(str)    # bookmark_id
```

変更:
- `eventFilter` の名前変更ダイアログ処理を `_start_rename()` メソッドに抽出
- `_show_context_menu()` に「A点へジャンプ」「名前を変更」「複製」「削除」を追加

コンテキストメニュー項目（順序）:
1. 「A点へジャンプ」— `jump_to_a_requested` を emit
2. セパレータ
3. 「名前を変更」— `_start_rename()` を呼ぶ
4. 「複製」— `duplicate_requested` を emit
5. 「削除」— `deleted` を emit（既存）
6. セパレータ
7. 「クリップを書き出す」— 既存（A/B両方設定時のみ有効）
8. 「再生回数をリセット」— 既存

### BookmarkPanel（変更）

追加シグナル:
```
seek_to_ms_requested = pyqtSignal(int)   # ms（「A点へジャンプ」用）
```

追加ハンドラ（内部）:
```
_on_jump_to_a(bookmark_id: str) -> None
  → bookmark を lookup → seek_to_ms_requested(a_ms) を emit

_on_duplicate(bookmark_id: str) -> None
  → bookmark を lookup → 複製 LoopBookmark 作成 → store.insert_after() → _refresh_list()
```

変更:
- `_refresh_list()` で新シグナルを接続
- `list_widget.setContextMenuPolicy(CustomContextMenu)` を設定
- `_show_panel_context_menu(pos)` を追加（import/export メニュー）

### VideoPlayer / player.py（変更）

追加属性:
```
_video_ctx_overlay: QWidget  # video_frame の透明子ウィジェット
```

追加メソッド:
```
_build_video_context_overlay() -> None
  → video_frame の子として透明 QWidget を作成
  → setContextMenuPolicy(CustomContextMenu)
  → customContextMenuRequested → _show_video_context_menu

_show_video_context_menu(pos: QPoint) -> None
  → QMenu を生成して動画エリアのコンテキストメニューを表示

_on_seek_to_ms(ms: int) -> None
  → media_player.set_time(ms)
  → （再生状態は変えない）
```

変更:
- `resizeEvent` でオーバーレイのサイズを video_frame に追従させる
- `bookmark_panel.seek_to_ms_requested` を `_on_seek_to_ms` に接続

## i18n 追加キー

| キー | 日本語 | 英語 |
|------|--------|------|
| `ctx.jump_to_a` | A点へジャンプ | Jump to A point |
| `ctx.rename` | 名前を変更 | Rename |
| `ctx.duplicate` | 複製 | Duplicate |
| `ctx.delete` | 削除 | Delete |
| `ctx.import_bookmarks` | ブックマークをインポート | Import Bookmarks |
| `ctx.export_bookmarks` | ブックマークをエクスポート | Export Bookmarks |
| `ctx.play_pause` | 再生 / 一時停止 | Play / Pause |
| `ctx.stop` | 停止 | Stop |
| `ctx.set_a` | A点を設定 | Set A Point |
| `ctx.set_b` | B点を設定 | Set B Point |
| `ctx.add_bookmark` | ここにブックマークを追加 | Add Bookmark Here |
| `ctx.screenshot` | スクリーンショット | Screenshot |
| `ctx.fullscreen` | フルスクリーン切り替え | Toggle Fullscreen |
| `bookmark.copy_suffix` | のコピー |  Copy |

## シグナルフロー図

```
[動画エリア右クリック]
  _video_ctx_overlay.customContextMenuRequested
    └→ VideoPlayer._show_video_context_menu(pos)
         └→ QMenu.exec(globalPos)

[ブックマーク行 A点へジャンプ]
  BookmarkRow.jump_to_a_requested(bookmark_id)
    └→ BookmarkPanel._on_jump_to_a(bookmark_id)
         └→ BookmarkPanel.seek_to_ms_requested(a_ms)
              └→ VideoPlayer._on_seek_to_ms(ms)
                   └→ media_player.set_time(ms)

[ブックマーク行 複製]
  BookmarkRow.duplicate_requested(bookmark_id)
    └→ BookmarkPanel._on_duplicate(bookmark_id)
         └→ BookmarkStore.insert_after(path, new_bm, after_id)
              └→ BookmarkPanel._refresh_list()

[ブックマーク行 削除（コンテキストメニュー）]
  BookmarkRow.deleted(bookmark_id)  ← 既存シグナルを再利用
    └→ BookmarkPanel._on_delete(bookmark_id)  ← 既存 Undo フロー

[パネル空白エリア右クリック]
  list_widget.customContextMenuRequested(pos)
    └→ BookmarkPanel._show_panel_context_menu(pos)
         └→ QMenu.exec(globalPos)
              import → VideoPlayer._import_bookmarks()
              export → VideoPlayer._export_bookmarks()
```
