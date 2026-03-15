"""FR-015: ファイルが開けない場合のエラーハンドリングテスト。"""
from unittest.mock import patch
from looplayer.player import VideoPlayer


def test_error_shows_dialog(player: VideoPlayer):
    """VLC MediaPlayerEncounteredError 発生時に QMessageBox.warning が呼ばれる。"""
    with patch("looplayer.player.QMessageBox") as mock_msgbox:
        player._on_media_error(None)
    mock_msgbox.warning.assert_called_once_with(
        player, "エラー", "動画ファイルを開けませんでした。"
    )


def test_error_preserves_playback_state(player: VideoPlayer):
    """エラー後に play_btn のラベルが変わらないこと（再生状態を維持）。"""
    initial_label = player.play_btn.text()
    with patch("looplayer.player.QMessageBox"):
        player._on_media_error(None)
    assert player.play_btn.text() == initial_label
