"""tests/unit/test_i18n.py — looplayer.i18n モジュールのユニットテスト。"""
import looplayer.i18n as i18n


# ── Phase 2: Foundational tests ─────────────────────────────────────────────


def test_t_returns_japanese_when_lang_is_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("menu.file") == "ファイル(&F)"


def test_t_returns_english_when_lang_is_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("menu.file") == "File(&F)"


def test_t_fallback_returns_key_for_unknown_key(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("unknown.key") == "unknown.key"


def test_all_keys_have_both_languages():
    for key, translations in i18n._STRINGS.items():
        assert "ja" in translations, f"キー '{key}' に 'ja' が欠けています"
        assert "en" in translations, f"キー '{key}' に 'en' が欠けています"


# ── Phase 3: User Story 1 additional tests ───────────────────────────────────


def test_t_menu_playback_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("menu.playback") == "Playback(&P)"


def test_t_btn_play_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("btn.play") == "再生"


def test_t_bookmark_panel_title_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("bookmark.panel.title") == "Bookmarks"


def test_t_msg_file_not_found_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("msg.file_not_found.title") == "File Not Found"


# ── 016-p1-features: 新規 i18n キーのテスト ──────────────────────────────────


# F-201: 字幕メッセージキー
def test_subtitle_open_file_menu_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("menu.playback.subtitle.open_file") != "menu.playback.subtitle.open_file"


def test_subtitle_open_file_menu_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("menu.playback.subtitle.open_file") != "menu.playback.subtitle.open_file"


def test_subtitle_no_video_error_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("msg.subtitle_no_video.title") != "msg.subtitle_no_video.title"
    assert i18n.t("msg.subtitle_no_video.body") != "msg.subtitle_no_video.body"


def test_subtitle_bad_format_error_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("msg.subtitle_bad_format.title") != "msg.subtitle_bad_format.title"
    assert i18n.t("msg.subtitle_bad_format.body") != "msg.subtitle_bad_format.body"


def test_subtitle_load_error_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("msg.subtitle_load_error.title") != "msg.subtitle_load_error.title"
    assert i18n.t("msg.subtitle_load_error.body") != "msg.subtitle_load_error.body"


# F-403: ウィンドウリセットメニューキー
def test_reset_window_menu_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("menu.view.reset_window") != "menu.view.reset_window"


def test_reset_window_menu_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("menu.view.reset_window") != "menu.view.reset_window"


# F-502: ツールチップキー
def test_tooltip_btn_play_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("tooltip.btn.play") != "tooltip.btn.play"


def test_tooltip_btn_play_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("tooltip.btn.play") != "tooltip.btn.play"


def test_tooltip_seekbar_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("tooltip.seekbar") != "tooltip.seekbar"


def test_tooltip_volume_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("tooltip.volume") != "tooltip.volume"


def test_tooltip_frame_buttons_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    for key in ("tooltip.btn.frame_minus", "tooltip.btn.frame_plus",
                "tooltip.btn.frame_a_minus", "tooltip.btn.frame_a_plus",
                "tooltip.btn.frame_b_minus", "tooltip.btn.frame_b_plus"):
        assert i18n.t(key) != key, f"キー '{key}' が未登録"


def test_tooltip_ab_buttons_en(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "en")
    for key in ("tooltip.btn.set_a", "tooltip.btn.set_b", "tooltip.btn.ab_loop"):
        assert i18n.t(key) != key, f"キー '{key}' が未登録"


def test_tooltip_bookmark_controls_ja(monkeypatch):
    monkeypatch.setattr(i18n, "_lang", "ja")
    for key in ("tooltip.btn.edit_tags", "tooltip.btn.reset_play_count",
                "tooltip.pause_interval"):
        assert i18n.t(key) != key, f"キー '{key}' が未登録"
