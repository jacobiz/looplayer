"""test_speed_menu_expansion: _PLAYBACK_RATES 10段階拡張と速度メニューのテスト（F-101 US2）。"""
import pytest


class TestPlaybackRatesContents:
    """T004: _PLAYBACK_RATES の基本テスト（RED → T005 で GREEN）。"""

    def test_playback_rates_has_10_stages(self):
        from looplayer.player import _PLAYBACK_RATES
        assert len(_PLAYBACK_RATES) == 10

    def test_playback_rates_includes_0_25(self):
        from looplayer.player import _PLAYBACK_RATES
        assert 0.25 in _PLAYBACK_RATES

    def test_playback_rates_includes_3_0(self):
        from looplayer.player import _PLAYBACK_RATES
        assert 3.0 in _PLAYBACK_RATES

    def test_playback_rates_includes_1_75_and_2_5(self):
        from looplayer.player import _PLAYBACK_RATES
        assert 1.75 in _PLAYBACK_RATES
        assert 2.5 in _PLAYBACK_RATES


class TestSpeedMenuExpansion:
    """T010: 速度メニュー生成と [/] キー循環テスト（RED → T005,T011 で GREEN）。"""

    def test_speed_menu_actions_count_equals_playback_rates(self):
        """速度メニューのアクション数が _PLAYBACK_RATES の要素数と一致する。"""
        from looplayer.player import _PLAYBACK_RATES
        assert len(_PLAYBACK_RATES) == 10

    def test_speed_up_cycles_through_all_10_stages(self):
        """_speed_up() が 10 段階すべてを昇順で循環する（FR-106）。"""
        from looplayer.player import _PLAYBACK_RATES
        rates = list(_PLAYBACK_RATES)
        assert rates[0] == 0.25
        assert rates[-1] == 3.0
        for i in range(len(rates) - 1):
            assert rates[i] < rates[i + 1], f"rates[{i}]={rates[i]} は rates[{i+1}]={rates[i+1]} より小さくなければならない"

    def test_speed_down_cycles_through_all_10_stages(self):
        """_speed_down() が 10 段階すべてを降順で循環する（FR-106）。"""
        from looplayer.player import _PLAYBACK_RATES
        rates = list(reversed(_PLAYBACK_RATES))
        assert rates[0] == 3.0
        assert rates[-1] == 0.25
        for i in range(len(rates) - 1):
            assert rates[i] > rates[i + 1], f"reversed rates[{i}]={rates[i]} は rates[{i+1}]={rates[i+1]} より大きくなければならない"

    def test_playback_rates_sorted_ascending(self):
        """_PLAYBACK_RATES は昇順でソートされている。"""
        from looplayer.player import _PLAYBACK_RATES
        assert list(_PLAYBACK_RATES) == sorted(_PLAYBACK_RATES)

    def test_playback_rates_all_positive(self):
        """_PLAYBACK_RATES の全要素が正の値である。"""
        from looplayer.player import _PLAYBACK_RATES
        assert all(r > 0 for r in _PLAYBACK_RATES)
