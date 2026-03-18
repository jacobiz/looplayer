# Research: 015-fix-window-resize

## Decision 1: UIオフセットの取得方法

**Decision**: `self.height() - self.video_frame.height()` で動的に差分を取得する

**Rationale**:
- `_resize_to_video` は必ずウィンドウ表示後（`open_file` 経由 or メニュー操作）に呼ばれるため、レイアウトが確定した状態でこの差分が正確に取得できる
- `controls_panel.sizeHint()` は非表示・サイズ未確定時に不正確になるリスクがある
- タイトルバー高さを含む全 UI オフセットを一度に取れる点でも優れている

**Alternatives considered**:
- `controls_panel.height()` + レイアウトマージン加算: レイアウト構造の変化に追従しにくい
- `controls_panel.sizeHint().height()`: ウィジェットが未表示時は 0 を返す可能性がある
- ハードコードした定数: UI 変更のたびに手動更新が必要で脆弱

---

## Decision 2: ポーリングタイムアウトの実装方針

**Decision**: カウンタ変数 `_size_poll_count` を追加し、100回（5秒）でタイマーを強制停止する

**Rationale**:
- 既存のポーリング構造（50ms 間隔 QTimer）を最小限の変更で拡張できる
- 別途タイムアウト用 QTimer を追加するより単純
- `_start_size_poll` でカウンタをリセットすれば再利用も安全

**Alternatives considered**:
- 別途タイムアウト用 `QTimer.singleShot(5000, ...)` を追加: タイマー2本管理で複雑度が増す
- `QTimer` を `setSingleShot(True)` + 短周期ループに変更: 大きな構造変更が必要

---

## Decision 3: デッドコードの扱い

**Decision**: `_user_resized` フラグと `_on_vlc_video_changed` メソッドを単純削除する

**Rationale**:
- `_user_resized` は `_start_size_poll` でセットされるのみで参照箇所が存在しない（grep 確認済み）
- `_on_vlc_video_changed` は VLC の EventManager に接続されておらず、`open_file` 内の手動 emit で代替されている
- VLC `MediaPlayerVideoChanged` イベントへの再接続はスコープ外とする（spec.md Assumptions に明記）

**Alternatives considered**:
- `_on_vlc_video_changed` を VLC イベントに接続して活用: 今回スコープ外、別フィーチャーで対応
