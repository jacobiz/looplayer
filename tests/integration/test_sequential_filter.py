"""US2: 連続再生対象フィルター統合テスト。"""
import pytest
from pytestqt.qtbot import QtBot

from looplayer.bookmark_store import BookmarkStore, LoopBookmark
from looplayer.widgets.bookmark_panel import BookmarkPanel


@pytest.fixture
def store(tmp_path):
    return BookmarkStore(storage_path=tmp_path / "bookmarks.json")


@pytest.fixture
def panel(qtbot, store):
    w = BookmarkPanel(store)
    qtbot.addWidget(w)
    return w


def _add_bm(store, path, a, b, enabled=True):
    bm = LoopBookmark(point_a_ms=a, point_b_ms=b, enabled=enabled)
    store.add(path, bm)
    return store.get_bookmarks(path)[-1]


class TestSeqBtnEnableLogic:
    """連続再生ボタンの有効/無効はチェック済みブックマーク件数に依存する。"""

    def test_btn_disabled_when_no_bookmarks(self, panel):
        panel.load_video("/v.mp4")
        assert not panel.seq_btn.isEnabled()

    def test_btn_enabled_when_one_enabled_bm(self, panel, store):
        _add_bm(store, "/v.mp4", 0, 1000)
        panel.load_video("/v.mp4")
        assert panel.seq_btn.isEnabled()

    def test_btn_disabled_when_all_disabled(self, qtbot, store):
        """全ブックマークが enabled=False のとき連続再生ボタンは無効化される（FR-008）。"""
        _add_bm(store, "/v.mp4", 0, 1000, enabled=False)
        _add_bm(store, "/v.mp4", 2000, 3000, enabled=False)
        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")
        assert not panel.seq_btn.isEnabled()

    def test_btn_enabled_when_at_least_one_enabled(self, qtbot, store):
        _add_bm(store, "/v.mp4", 0, 1000, enabled=False)
        _add_bm(store, "/v.mp4", 2000, 3000, enabled=True)
        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")
        assert panel.seq_btn.isEnabled()


class TestSequentialFilteredPlay:
    """連続再生は enabled=True のブックマークのみを対象とする（FR-006）。"""

    def test_sequential_started_only_enabled_bookmarks(self, qtbot, store):
        """enabled=True の2件のみが SequentialPlayState に含まれる。"""
        bm_a = _add_bm(store, "/v.mp4", 0, 1000, enabled=True)
        bm_b = _add_bm(store, "/v.mp4", 2000, 3000, enabled=False)
        bm_c = _add_bm(store, "/v.mp4", 4000, 5000, enabled=True)

        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")

        received_states = []
        panel.sequential_started.connect(lambda state: received_states.append(state))

        panel.seq_btn.click()  # 連続再生開始

        assert len(received_states) == 1
        state = received_states[0]
        ids_in_state = [bm.id for bm in state.bookmarks]
        assert bm_a.id in ids_in_state
        assert bm_b.id not in ids_in_state
        assert bm_c.id in ids_in_state

    def test_sequential_uses_all_when_all_enabled(self, qtbot, store):
        bm_a = _add_bm(store, "/v.mp4", 0, 1000)
        bm_b = _add_bm(store, "/v.mp4", 2000, 3000)
        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")

        received_states = []
        panel.sequential_started.connect(lambda state: received_states.append(state))
        panel.seq_btn.click()

        state = received_states[0]
        assert len(state.bookmarks) == 2


class TestAllUncheckedAutoStop:
    """連続再生中に全チェックが外れた場合、次の区間移行時に自動停止する（Edge Case）。"""

    def test_seq_state_uses_only_enabled_at_start(self, qtbot, store):
        """enabled のみで開始すること自体を検証（停止の詳細は _on_timer が担う）。"""
        bm = _add_bm(store, "/v.mp4", 0, 1000, enabled=True)
        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")

        states = []
        panel.sequential_started.connect(lambda s: states.append(s))
        panel.seq_btn.click()

        assert states[0].active is True
        assert len(states[0].bookmarks) == 1

    def test_stop_sequential_when_no_enabled_bookmarks_remain(self, qtbot, store):
        """enabled=False に変えた後、パネルが seq_btn を無効化することを確認。"""
        bm = _add_bm(store, "/v.mp4", 0, 1000, enabled=True)
        panel = BookmarkPanel(store)
        qtbot.addWidget(panel)
        panel.load_video("/v.mp4")

        # enabled を False に変更
        store.update_enabled("/v.mp4", bm.id, False)
        # 手動でリフレッシュ（通常はチェックボックス経由）
        panel.load_video("/v.mp4")

        assert not panel.seq_btn.isEnabled()
