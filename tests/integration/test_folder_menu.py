"""T029: フォルダを開くメニューの統合テスト。"""
from unittest.mock import patch, MagicMock
from looplayer.player import VideoPlayer
from looplayer.i18n import t


def test_open_folder_action_exists(player: VideoPlayer):
    """ファイルメニューに「フォルダを開く」アクションが存在する。"""
    file_menu = player.menuBar().actions()[0].menu()
    actions = file_menu.actions()
    labels = [a.text() for a in actions]
    assert t("menu.file.open_folder") in labels


def test_open_folder_cancel_no_change(player: VideoPlayer, qtbot):
    """キャンセルで変化なし。"""
    with patch("looplayer.player.QFileDialog.getExistingDirectory", return_value=""):
        player.open_folder()
    assert player._current_video_path is None


def test_open_folder_empty_dir_shows_warning(player: VideoPlayer, qtbot, tmp_path):
    """空フォルダを開くと動画なしの警告メッセージが表示される。"""
    with patch("looplayer.player.QFileDialog.getExistingDirectory", return_value=str(tmp_path)):
        with patch("looplayer.player.QMessageBox.warning") as mock_warn:
            player.open_folder()
    mock_warn.assert_called_once()


def test_open_folder_with_videos_loads_playlist(player: VideoPlayer, qtbot, tmp_path):
    """動画ファイルが含まれるフォルダを開くとプレイリストが読み込まれる。"""
    # ダミーの .mp4 ファイルを作る
    (tmp_path / "a.mp4").write_bytes(b"")
    (tmp_path / "b.mp4").write_bytes(b"")

    with patch("looplayer.player.QFileDialog.getExistingDirectory", return_value=str(tmp_path)):
        with patch.object(player, "_open_path") as mock_open:
            player.open_folder()

    assert mock_open.called
    assert player._playlist is not None
    assert len(player._playlist) == 2
