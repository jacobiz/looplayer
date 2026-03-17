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
