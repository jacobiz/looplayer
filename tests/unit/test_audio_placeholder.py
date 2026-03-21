"""020: 音楽再生中プレースホルダーのユニットテスト（T006）。"""
from unittest.mock import patch, MagicMock


class TestIsAudioFlag:
    """_is_audio フラグが拡張子に基づき正しく設定されることを確認。"""

    def test_initial_is_audio_is_false(self, player):
        """初期状態では _is_audio は False。"""
        assert player._is_audio is False

    def test_is_audio_true_for_mp3(self, player, tmp_path):
        """mp3 ファイルを開くと _is_audio == True。"""
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"")
        with patch.object(player, "_size_poll_timer") as mock_timer, \
             patch.object(player.instance, "media_new", return_value=MagicMock()), \
             patch.object(player.media_player, "set_media"), \
             patch.object(player.media_player, "play"), \
             patch.object(player.media_player, "get_time", return_value=0), \
             patch.object(player.media_player, "get_length", return_value=0):
            player._open_path(str(audio))
        assert player._is_audio is True

    def test_is_audio_true_for_all_audio_formats(self, player, tmp_path):
        """すべての対応音楽形式で _is_audio == True。"""
        for ext in [".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a", ".opus"]:
            audio = tmp_path / f"track{ext}"
            audio.write_bytes(b"")
            with patch.object(player.instance, "media_new", return_value=MagicMock()), \
                 patch.object(player.media_player, "set_media"), \
                 patch.object(player.media_player, "play"), \
                 patch.object(player.media_player, "get_time", return_value=0), \
                 patch.object(player.media_player, "get_length", return_value=0), \
                 patch.object(player, "_video_changed"):
                player._open_path(str(audio))
            assert player._is_audio is True, f"{ext} で _is_audio が True にならない"

    def test_is_audio_false_for_mp4(self, player, tmp_path):
        """mp4 ファイルを開くと _is_audio == False。"""
        video = tmp_path / "movie.mp4"
        video.write_bytes(b"")
        with patch.object(player.instance, "media_new", return_value=MagicMock()), \
             patch.object(player.media_player, "set_media"), \
             patch.object(player.media_player, "play"), \
             patch.object(player.media_player, "get_time", return_value=0), \
             patch.object(player.media_player, "get_length", return_value=0), \
             patch.object(player, "_video_changed"):
            player._open_path(str(video))
        assert player._is_audio is False

    def test_is_audio_resets_when_switching_to_video(self, player, tmp_path):
        """音楽→動画の切り替えで _is_audio が False に戻る。"""
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"")
        video = tmp_path / "movie.mp4"
        video.write_bytes(b"")
        with patch.object(player.instance, "media_new", return_value=MagicMock()), \
             patch.object(player.media_player, "set_media"), \
             patch.object(player.media_player, "play"), \
             patch.object(player.media_player, "get_time", return_value=0), \
             patch.object(player.media_player, "get_length", return_value=0), \
             patch.object(player, "_video_changed"):
            player._open_path(str(audio))
            assert player._is_audio is True
            player._open_path(str(video))
        assert player._is_audio is False


class TestAudioPlaceholder:
    """_audio_placeholder ウィジェットの表示・非表示切り替えを確認。
    _update_audio_placeholder() を直接呼び出して VLC を介さずテストする。
    """

    def test_audio_placeholder_exists(self, player):
        """_audio_placeholder 属性が存在する。"""
        assert hasattr(player, "_audio_placeholder"), (
            "_audio_placeholder が VideoPlayer に存在しない"
        )

    def test_placeholder_hidden_initially(self, player):
        """初期状態ではプレースホルダーは非表示。"""
        assert player._audio_placeholder.isHidden()

    def test_update_audio_placeholder_method_exists(self, player):
        """_update_audio_placeholder メソッドが存在する。"""
        assert hasattr(player, "_update_audio_placeholder"), (
            "_update_audio_placeholder が VideoPlayer に存在しない"
        )

    def test_update_audio_placeholder_shows_when_is_audio_true(self, player):
        """_is_audio = True のとき _update_audio_placeholder() でプレースホルダーが非表示でなくなる。
        (isVisible() は親ウィジェットの表示状態に依存するため isHidden() で判定する)
        """
        player._is_audio = True
        player._update_audio_placeholder()
        assert not player._audio_placeholder.isHidden()

    def test_update_audio_placeholder_hides_when_is_audio_false(self, player):
        """_is_audio = False のとき _update_audio_placeholder() でプレースホルダーが非表示になる。"""
        player._is_audio = True
        player._update_audio_placeholder()
        player._is_audio = False
        player._update_audio_placeholder()
        assert player._audio_placeholder.isHidden()

    def test_placeholder_shown_for_audio_via_open_path(self, player, tmp_path):
        """音楽ファイルを開くとプレースホルダーが非表示でなくなる。"""
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"")
        with patch.object(player.instance, "media_new", return_value=MagicMock()), \
             patch.object(player.media_player, "set_media"), \
             patch.object(player.media_player, "play"), \
             patch.object(player.media_player, "get_time", return_value=0), \
             patch.object(player.media_player, "get_length", return_value=0), \
             patch.object(player, "_video_changed"):
            player._open_path(str(audio))
        assert not player._audio_placeholder.isHidden()

    def test_placeholder_hidden_for_video_via_open_path(self, player, tmp_path):
        """動画ファイルを開くとプレースホルダーが非表示になる。"""
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"")
        video = tmp_path / "movie.mp4"
        video.write_bytes(b"")
        with patch.object(player.instance, "media_new", return_value=MagicMock()), \
             patch.object(player.media_player, "set_media"), \
             patch.object(player.media_player, "play"), \
             patch.object(player.media_player, "get_time", return_value=0), \
             patch.object(player.media_player, "get_length", return_value=0), \
             patch.object(player, "_video_changed"):
            player._open_path(str(audio))
            assert not player._audio_placeholder.isHidden()
            player._open_path(str(video))
        assert player._audio_placeholder.isHidden()
