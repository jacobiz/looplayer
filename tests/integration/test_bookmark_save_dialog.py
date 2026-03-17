"""T014: ブックマーク保存時の名前入力ダイアログの統合テスト。"""
from unittest.mock import patch, MagicMock
from looplayer.player import VideoPlayer


def test_ok_saves_default_name(player: VideoPlayer, qtbot):
    """OK + デフォルト名でブックマークが保存される。"""
    player.ab_point_a = 1000
    player.ab_point_b = 5000
    player.bookmark_panel.load_video("/test.mp4")
    player._current_video_path = "/test.mp4"

    with patch("looplayer.player.QInputDialog.getText", return_value=("デフォルト", True)):
        with patch.object(player.media_player, 'get_length', return_value=60000):
            player._save_bookmark()

    bms = player._store.get_bookmarks("/test.mp4")
    assert len(bms) == 1
    assert bms[0].name == "デフォルト"


def test_ok_saves_custom_name(player: VideoPlayer, qtbot):
    """OK + 入力名でブックマークが保存される。"""
    player.ab_point_a = 2000
    player.ab_point_b = 6000
    player.bookmark_panel.load_video("/test.mp4")
    player._current_video_path = "/test.mp4"

    with patch("looplayer.player.QInputDialog.getText", return_value=("カスタム名", True)):
        with patch.object(player.media_player, 'get_length', return_value=60000):
            player._save_bookmark()

    bms = player._store.get_bookmarks("/test.mp4")
    assert len(bms) == 1
    assert bms[0].name == "カスタム名"


def test_cancel_does_not_save(player: VideoPlayer, qtbot):
    """Cancel でブックマークが保存されない。"""
    player.ab_point_a = 1000
    player.ab_point_b = 5000
    player.bookmark_panel.load_video("/test.mp4")
    player._current_video_path = "/test.mp4"

    with patch("looplayer.player.QInputDialog.getText", return_value=("", False)):
        with patch.object(player.media_player, 'get_length', return_value=60000):
            player._save_bookmark()

    bms = player._store.get_bookmarks("/test.mp4")
    assert len(bms) == 0
