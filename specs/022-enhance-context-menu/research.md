# Research: コンテキストメニューの充実

## 1. VLC 埋め込み中の mouse event 問題

### Decision
video_frame に透明な QWidget（`_video_ctx_overlay`）を子として重ね、その上でコンテキストメニューイベントを受信する。

### Rationale
VLC は `set_xwindow(win_id)` / `set_hwnd(win_id)` によりネイティブウィンドウを占有する。
Linux(X11) では VLC が子 X ウィンドウを作成し、その領域のマウスイベントが Qt のイベントループを迂回する。
一方、Qt の子 QWidget はレンダリングレイヤーの上に配置できるため、透明オーバーレイが事実上フォールバックとなる。
既存の `_audio_placeholder`（QLabel 子ウィジェット）が video_frame 上に正常表示されていることから、子ウィジェット手法の有効性が確認済み。

### Alternatives considered
- `video_frame.setContextMenuPolicy(CustomContextMenu)` — VLC が X11 レベルで右クリックを横取りするため Linux では動作しない
- アプリケーションレベルの `QApplication.installEventFilter` — 全イベントに割り込むためパフォーマンスコストがあり、座標変換が複雑
- `VideoPlayer.contextMenuEvent` オーバーライド — VLC 占有時は MainWindow まで ContextMenu イベントが到達しない

## 2. BookmarkStore.insert_after の欠如

### Decision
`BookmarkStore` に `insert_after(video_path, bookmark, after_id)` メソッドを追加する。

### Rationale
複製ブックマークを「元の直後」に挿入するには order の差し込みが必要だが、既存の `add()` は末尾追加のみ、`add_many()` も末尾追記のみ。
`update_order()` は既存 ID のみを対象とするため、新規 ID を含む並べ替えには使えない。
新メソッドを追加するのが最もシンプルで、既存 API を破壊しない。

### Alternatives considered
- `add()` で末尾に追加後 `update_order()` で位置を調整 — 2回の save() が走るためアトミック性が低い
- `add()` 後に `_refresh_list()` 表示順だけ差し込む — 永続化順序と表示順が乖離する

## 3. BookmarkRow の rename ロジック再利用

### Decision
`eventFilter` にインラインで書かれている名前変更ダイアログ処理を `_start_rename()` メソッドに抽出し、eventFilter とコンテキストメニューの両方から呼び出す。

### Rationale
同一ダイアログを複数箇所から起動するために DRY 原則を適用。
抽出後のコード量は 4行程度であり、余計な抽象化にはあたらない（Constitution II 準拠）。

### Alternatives considered
- コンテキストメニューに別の実装を書く — 重複コードになる

## 4. 「A点へジャンプ」のシグナルチェーン設計

### Decision
`BookmarkRow` → `jump_to_a_requested(str)` → `BookmarkPanel` → `seek_to_ms_requested(int)` → `VideoPlayer._on_seek_to_ms(int)` → `media_player.set_time(ms)`

### Rationale
再生状態を変えずにシークするだけなので、既存の `bookmark_selected` シグナル（AB ループ設定・再生開始を伴う）を再利用しない。
専用シグナルを最短経路で繋ぐことで、既存の再生ロジックへの干渉をゼロにする。

### Alternatives considered
- `_on_bookmark_selected` を再利用 — AB ループが強制的にセットされ、再生状態が変わってしまう

## 5. BookmarkPanel 空白エリアのコンテキストメニュー

### Decision
`list_widget.setContextMenuPolicy(CustomContextMenu)` を設定し、`list_widget.customContextMenuRequested` に接続する。
ハンドラ内で `list_widget.itemAt(pos)` を確認し、None（空白エリア）のときのみパネルメニューを表示する。

### Rationale
BookmarkRow 自身が `CustomContextMenu` を持つため、行のクリックイベントは BookmarkRow が吸収し `list_widget` のシグナルには到達しない。
空白エリアのクリックのみが `list_widget` に届くため、`itemAt(pos) is None` で条件分岐するだけで済む。

### Alternatives considered
- `QListWidget` をサブクラス化して `contextMenuEvent` オーバーライド — 過度な抽象化（Constitution III 違反）
