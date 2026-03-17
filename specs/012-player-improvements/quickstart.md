# Quickstart: AB Loop Player Improvements — Integration Test Scenarios

## テストの実行方法

```bash
pytest tests/ -v                                    # 全テスト
pytest tests/unit/ -v                               # ユニットテストのみ
pytest tests/integration/test_ab_shortcuts.py -v   # US1
pytest tests/integration/test_frame_adjust.py -v   # US2
pytest tests/integration/test_bookmark_save.py -v  # US3
pytest tests/integration/test_loop_pause.py -v     # US4
pytest tests/integration/test_seq_mode.py -v       # US5
pytest tests/integration/test_play_count.py -v     # US6
pytest tests/integration/test_folder_menu.py -v    # US7
pytest tests/integration/test_playlist_ui.py -v    # US8
pytest tests/unit/test_bookmark_tags.py -v         # US9
pytest tests/unit/test_transcode_export.py -v      # US10
```

---

## US1: A/B 点キーボードショートカット

```python
# tests/integration/test_ab_shortcuts.py

def test_i_key_sets_point_a(player, qtbot):
    """I キーで A 点が設定される"""
    with patch.object(player.media_player, "get_time", return_value=3000):
        qtbot.keyPress(player, Qt.Key.Key_I)
    assert player.ab_point_a == 3000

def test_o_key_sets_point_b(player, qtbot):
    """O キーで B 点が設定される"""
    player.ab_point_a = 1000
    with patch.object(player.media_player, "get_time", return_value=5000):
        qtbot.keyPress(player, Qt.Key.Key_O)
    assert player.ab_point_b == 5000

def test_shortcut_inactive_when_lineedit_focused(player, qtbot):
    """QLineEdit フォーカス中は I/O が無効"""
    # ブックマーク名編集中はショートカットが発火しない
    ...
```

---

## US2: A/B 点フレーム単位微調整

```python
# tests/unit/test_frame_adjust.py

def test_frame_adjust_a_plus(bookmark_row_with_fps):
    """A点 +1F で point_a_ms が 1フレーム分増加する"""
    row, bm = bookmark_row_with_fps  # fps=25, frame_ms=40
    initial_a = bm.point_a_ms
    row._adjust_a_plus()
    assert bm.point_a_ms == initial_a + 40

def test_frame_adjust_rejects_a_gte_b(bookmark_row):
    """A点 >= B点 になる微調整を拒否する"""
    bm = LoopBookmark(point_a_ms=4960, point_b_ms=5000)  # B-A = 40ms = 1フレーム
    row = BookmarkRow(bm)
    row._adjust_a_plus()  # A=5000 になろうとする
    assert bm.point_a_ms == 4960  # 変化しない
```

---

## US3: ブックマーク保存時の名前入力

```python
# tests/integration/test_bookmark_save.py

def test_save_bookmark_with_custom_name(player, qtbot):
    """名前を入力してブックマークが保存される"""
    player.ab_point_a = 1000
    player.ab_point_b = 5000
    player._video_path = "/fake/video.mp4"
    with patch("looplayer.player.QInputDialog.getText",
               return_value=("マイブックマーク", True)):
        player._save_bookmark()
    bms = player._store.get_bookmarks("/fake/video.mp4")
    assert len(bms) == 1
    assert bms[0].name == "マイブックマーク"

def test_save_bookmark_cancelled(player, qtbot):
    """キャンセル時にブックマークが保存されない"""
    player.ab_point_a = 1000
    player.ab_point_b = 5000
    with patch("looplayer.player.QInputDialog.getText",
               return_value=("", False)):
        player._save_bookmark()
    assert player._store.get_bookmarks(player._video_path or "") == []
```

---

## US4: ループ間ポーズ

```python
# tests/unit/test_loop_pause.py

def test_pause_ms_zero_seeks_immediately(player):
    """pause_ms=0 のとき即座に A 点にシークする（既存動作）"""
    bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, pause_ms=0)
    # B点到達処理 → media_player.set_time(1000) が即呼ばれる

def test_pause_ms_nonzero_pauses_before_seeking(player):
    """pause_ms>0 のとき一時停止してからシークする"""
    bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, pause_ms=2000)
    # B点到達処理 → media_player.pause() + _pause_timer.start(2000)
    assert player._pause_timer is not None
    assert player._pause_timer.isActive()
```

---

## US5: 連続再生1周停止

```python
# tests/unit/test_sequential_one_round.py

def test_one_round_stops_after_last_bookmark(qtbot):
    """1周停止モードで最後のブックマーク完了時に None を返す"""
    bms = [
        LoopBookmark(point_a_ms=0, point_b_ms=1000, repeat_count=1),
        LoopBookmark(point_a_ms=2000, point_b_ms=3000, repeat_count=1),
    ]
    state = SequentialPlayState(bookmarks=bms, one_round_mode=True)
    state.on_b_reached()  # bm[0] 完了 → bm[1] へ
    result = state.on_b_reached()  # bm[1] 完了 → None
    assert result is None

def test_infinite_mode_wraps_around(qtbot):
    """無限ループモード（デフォルト）では先頭に戻る"""
    bms = [LoopBookmark(point_a_ms=0, point_b_ms=1000, repeat_count=1)]
    state = SequentialPlayState(bookmarks=bms, one_round_mode=False)
    result = state.on_b_reached()
    assert result == 0  # bm[0].point_a_ms
```

---

## US6: 練習カウンター

```python
# tests/integration/test_play_count.py

def test_play_count_increments_on_b_reached(player):
    """B点到達で play_count が 1 増える"""
    bm = LoopBookmark(point_a_ms=1000, point_b_ms=5000, play_count=0)
    # simulate B point reached → play_count should become 1

def test_play_count_persists_after_restart(tmp_path):
    """play_count が JSON に保存されアプリ再起動後も保持される"""
    store = BookmarkStore(storage_path=tmp_path / "bm.json")
    bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, play_count=5)
    store.add("/video.mp4", bm, 10000)
    store2 = BookmarkStore(storage_path=tmp_path / "bm.json")
    loaded = store2.get_bookmarks("/video.mp4")
    assert loaded[0].play_count == 5
```

---

## US7: フォルダを開くメニュー

```python
# tests/integration/test_folder_menu.py

def test_folder_menu_item_exists(player):
    """ファイルメニューに「フォルダを開く」が存在する"""
    assert player._open_folder_action is not None

def test_open_folder_loads_playlist(player, tmp_path, qtbot):
    """フォルダ選択でプレイリストが読み込まれる"""
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()
    with patch("looplayer.player.QFileDialog.getExistingDirectory",
               return_value=str(tmp_path)):
        player.open_folder()
    assert player._playlist is not None
    assert len(player._playlist) == 2
```

---

## US8: プレイリスト UI パネル

```python
# tests/integration/test_playlist_ui.py

def test_playlist_panel_shown_when_playlist_loaded(player, tmp_path, qtbot):
    """プレイリスト読み込み後にパネルが表示される"""
    ...

def test_alt_right_advances_playlist(player, tmp_path, qtbot):
    """Alt+→ で次のファイルに切り替わる"""
    ...
```

---

## US9: ブックマークタグ付け

```python
# tests/unit/test_bookmark_tags.py

def test_tags_saved_and_loaded(tmp_path):
    """タグが JSON 保存・読み込みで保持される"""
    store = BookmarkStore(storage_path=tmp_path / "bm.json")
    bm = LoopBookmark(point_a_ms=0, point_b_ms=1000, tags=["発音", "N2"])
    store.add("/v.mp4", bm, 10000)
    loaded = BookmarkStore(storage_path=tmp_path / "bm.json").get_bookmarks("/v.mp4")
    assert loaded[0].tags == ["発音", "N2"]

def test_tag_filter_or_logic(bookmark_panel):
    """OR フィルタで複数タグのいずれかを持つブックマークが表示される"""
    ...
```

---

## US10: クリップ書き出しトランスコード

```python
# tests/unit/test_transcode_export.py

def test_copy_mode_uses_c_copy(tmp_path):
    """copy モードで -c copy が使われる"""
    job = ClipExportJob(source_path=..., start_ms=0, end_ms=1000,
                        output_path=..., encode_mode="copy")
    # ffmpeg コマンドに "-c", "copy" が含まれる

def test_transcode_mode_uses_libx264(tmp_path):
    """transcode モードで libx264 + aac が使われる"""
    job = ClipExportJob(..., encode_mode="transcode")
    # ffmpeg コマンドに "-c:v", "libx264", "-c:a", "aac" が含まれる
```

