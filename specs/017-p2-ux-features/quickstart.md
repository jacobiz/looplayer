# Quickstart & Integration Scenarios: P2 UX 機能群

**Branch**: `017-p2-ux-features` | **Date**: 2026-03-18

---

## セットアップ

```bash
# リポジトリルートから
python main.py          # アプリ起動
pytest tests/ -v        # 全テスト
pytest tests/unit/ -v   # ユニットテストのみ
```

---

## シナリオ 1: フルスクリーン中コントロールオーバーレイ（F-503）

### 手動確認フロー

1. 動画ファイルを開く
2. `F` キーまたは「表示 > フルスクリーン」でフルスクリーンへ
3. マウスを画面中央に移動 → コントロールバーは非表示のまま
4. マウスを画面下端（画面高さの下10%）に移動 → コントロールバーが表示される
5. 3秒間マウスを動かさない → コントロールバーが自動的に非表示になる
6. 再度コントロールバーを表示し、シークバーをドラッグ → シークが機能する
7. `Esc` またはフルスクリーン解除ボタン → 通常ウィンドウに戻る、コントロールバーが通常位置に復帰

### テスト対象クラス

```python
# tests/unit/test_fullscreen_overlay.py
class TestFullscreenOverlayMethods:
    def test_enter_exits_overlay_mode(self, player):
        """_enter_fullscreen_overlay_mode でコントロールパネルがレイアウトから外れる"""

    def test_exit_restores_layout(self, player):
        """_exit_fullscreen_overlay_mode でコントロールパネルがレイアウトに戻る"""

    def test_mouse_in_bottom_10_percent_shows_overlay(self, player):
        """画面下端10%にマウスが入ると controls_panel が表示される"""

    def test_mouse_outside_bottom_does_not_show(self, player):
        """画面中央のマウス移動では controls_panel が表示されない"""

    def test_overlay_timer_hides_after_3s(self, player):
        """_overlay_hide_timer.timeout で controls_panel が非表示になる"""
```

---

## シナリオ 2: 設定画面（F-401）

### 手動確認フロー

1. 「ファイル > 設定...」メニューをクリック → `PreferencesDialog` が開く
2. 「再生」タブ → 再生終了時動作を「ループ」に変更
3. 「アップデート」タブ → 「起動時に更新を確認する」をオフ
4. 「OK」をクリック → ダイアログが閉じる
5. 再度「設定...」を開く → 変更した値が保持されている
6. 値を変更して「キャンセル」をクリック → 元の値のまま

### テスト対象クラス

```python
# tests/unit/test_preferences_dialog.py
class TestPreferencesDialog:
    def test_opens_with_current_values(self, qtbot, settings):
        """ダイアログ開時に AppSettings の現在値が反映される"""

    def test_ok_saves_values(self, qtbot, settings):
        """OK ボタンで変更が AppSettings に保存される"""

    def test_cancel_discards_changes(self, qtbot, settings):
        """キャンセルで AppSettings の値が変更されない"""

    def test_preferences_menu_item_exists(self, player):
        """「ファイル」メニューに「設定...」アクションがある"""
```

---

## シナリオ 3: 初回起動オンボーディング（F-501）

### 手動確認フロー

1. `~/.looplayer/settings.json` の `onboarding_shown` キーを削除（または初回起動）
2. アプリを起動 → オーバーレイが中央に表示される（ステップ 1/4）
3. 「次へ」を 3 回クリック → ステップが進む（2→3→4）
4. 最終ステップで「完了」をクリック → オーバーレイが閉じる
5. アプリを再起動 → オーバーレイは表示されない
6. 「ヘルプ > チュートリアルを表示」をクリック → ステップ1から再表示される

### 途中終了シナリオ

1. オーバーディング表示中にウィンドウを閉じる
2. 再起動 → ステップ 1 から再表示される（完了フラグ未保存）

### テスト対象クラス

```python
# tests/unit/test_onboarding_overlay.py
class TestOnboardingOverlay:
    def test_shows_on_first_launch(self, qtbot, settings):
        """onboarding_shown=False のとき VideoPlayer 起動でオーバーレイが表示される"""

    def test_does_not_show_when_completed(self, qtbot, settings):
        """onboarding_shown=True のとき起動でオーバーレイが表示されない"""

    def test_next_advances_step(self, qtbot, overlay):
        """「次へ」ボタンでステップが増加する"""

    def test_finish_saves_flag(self, qtbot, overlay, settings):
        """最終ステップの「完了」で onboarding_shown=True が保存される"""

    def test_skip_saves_flag(self, qtbot, overlay, settings):
        """「スキップ」で onboarding_shown=True が保存される"""

    def test_close_without_finish_does_not_save(self, qtbot, overlay, settings):
        """ウィンドウを閉じても完了前は onboarding_shown が保存されない"""

    def test_help_menu_retrigger(self, player):
        """「ヘルプ > チュートリアルを表示」で onboarding_shown=False → オーバーレイ表示"""
```

---

## シナリオ 4: ABループ区間のズーム表示（F-105）

### 手動確認フロー

1. 動画を開き、A点・B点を設定（例: 0:10.000 〜 0:12.000 の 2秒区間）
2. コントロールパネルの「ズーム」ボタンをクリック
3. シークバーが A/B 区間全幅に拡大表示される（前後に余白あり）
4. ドラッグで A/B 点を微調整 → フレーム単位の精密操作が可能
5. A/B 区間を変更 → 拡大範囲が自動更新される
6. 「ズーム」ボタンを再度クリック → 通常表示に戻る
7. 動画を別のファイルに切り替え → ズームが自動解除される

### AB 区間未設定時

- 「ズーム」ボタンは `setEnabled(False)` 状態

### テスト対象クラス

```python
# tests/unit/test_bookmark_slider_zoom.py
class TestBookmarkSliderZoom:
    def test_set_zoom_enables_zoom_mode(self, slider):
        """set_zoom 後に zoom_enabled == True"""

    def test_clear_zoom_disables(self, slider):
        """clear_zoom 後に zoom_enabled == False"""

    def test_ms_to_x_uses_zoom_range(self, slider):
        """ズームモード中の _ms_to_x は zoom_start_ms を左端として変換する"""

    def test_x_to_ms_uses_zoom_range(self, slider):
        """ズームモード中の _x_to_ms は zoom 範囲を逆変換する"""

    def test_set_zoom_invalid_range_raises(self, slider):
        """start_ms >= end_ms で set_zoom は ValueError を raise する"""

    def test_zoom_btn_disabled_without_ab(self, player):
        """AB 点未設定時はズームボタンが無効"""

    def test_zoom_resets_on_video_change(self, player):
        """動画変更時にズームモードが解除される"""
```

---

## 統合確認: AppSettings の相互影響なし

```python
# tests/integration/test_settings_isolation.py
def test_onboarding_flag_does_not_affect_other_settings():
    """onboarding_shown の変更が end_of_playback_action などに影響しない"""
```
