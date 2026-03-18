# Implementation Plan: P1優先度機能の実装

**Branch**: `016-p1-features` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-p1-features/spec.md`

---

## Summary

F-201（外部字幕読み込み）・F-403（ウィンドウ位置記憶）・F-502（ツールチップ充実）の 3 つの P1 機能を実装する。
いずれも既存モジュールの拡張のみで完結し、新規ファイルは最小限に抑える。
実装順は F-403 → F-502 → F-201 とし、各機能を独立したコミットで完結させる。

---

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: `~/.looplayer/settings.json`（JSON, `AppSettings` クラスで管理）
**Testing**: pytest（`tests/unit/`・`tests/integration/`）
**Target Platform**: Windows デスクトップ（クロスプラットフォーム動作可）
**Project Type**: デスクトップアプリ
**Performance Goals**: 応答遅延なし（字幕読み込みは VLC 内部で非同期）
**Constraints**: UI 文字列は必ず `t()` 経由、テストファースト（constitution I）
**Scale/Scope**: 単一ユーザー、変更対象は ~3 ファイル（新規テストファイル 2〜3 本）

---

## Constitution Check

*GATE: Phase 0 着手前に確認。Phase 1 設計後に再確認。*

| 原則 | 評価 | 判定 |
|------|------|------|
| I. テストファースト | 各機能はテストを先に書いてから実装する | ✅ PASS |
| II. シンプルさ重視 | 新規モジュールなし。既存クラスへのプロパティ/メソッド追加のみ | ✅ PASS |
| III. 過度な抽象化の禁止 | ヘルパークラス・Repository パターン等は使用しない | ✅ PASS |
| IV. 日本語コミュニケーション | 全 UI 文字列を `i18n.py` に追記、コミットメッセージも日本語 | ✅ PASS |

**Complexity Tracking**: 違反なし（記録不要）

---

## Project Structure

### Documentation (this feature)

```text
specs/016-p1-features/
├── plan.md          # このファイル
├── research.md      # Phase 0 出力
├── data-model.md    # Phase 1 出力
└── tasks.md         # /speckit.tasks コマンドで生成
```

### Source Code (変更対象ファイル)

```text
looplayer/
├── app_settings.py          # window_geometry プロパティを追加（F-403）
├── player.py                # 字幕メニュー項目・ジオメトリ保存・ツールチップ・リセットメニュー
├── i18n.py                  # 新規翻訳キーを追記（F-201/F-403/F-502）
└── widgets/
    └── bookmark_row.py      # ツールチップ追加（F-502）

tests/unit/
├── test_app_settings.py     # window_geometry テストを追記（F-403）
└── test_i18n.py             # 新規キーのカバレッジテストを追記

tests/integration/
├── test_subtitles.py        # 新規作成（F-201）
├── test_window_geometry.py  # 新規作成（F-403）
└── test_tooltips.py         # 新規作成（F-502）
```

**Structure Decision**: 既存のシングルプロジェクト構造を維持。新規モジュールは作成しない。

---

## Phase 0: Research 完了

→ [research.md](research.md) 参照

**解決済み事項**:
- F-201 字幕 API: `media_player.add_slave(MediaSlaveType.Subtitle, uri, True)` を使用
- F-403 ジオメトリ: `AppSettings.window_geometry` を `dict | None` で保存
- F-403 フルスクリーン: `_pre_fullscreen_geometry = self.geometry()` を突入時に保持
- F-502 ツールチップ: `setToolTip(t("tooltip.key"))` を各ウィジェットに追加

---

## Phase 1: Design & Contracts 完了

→ [data-model.md](data-model.md) 参照

契約（contracts/）: 外部 API なし（デスクトップアプリ内部実装のみ）のためスキップ

---

## 実装詳細（機能別）

### F-403 ウィンドウ位置・サイズの記憶

**変更ファイル 1**: `looplayer/app_settings.py`

```python
# 追加するプロパティ
@property
def window_geometry(self) -> dict | None:
    geo = self._data.get("window_geometry")
    if geo is None:
        return None
    if not all(k in geo for k in ("x", "y", "width", "height")):
        return None
    return geo

@window_geometry.setter
def window_geometry(self, value: dict | None) -> None:
    if value is None:
        self._data.pop("window_geometry", None)
    else:
        self._data["window_geometry"] = value
    self.save()
```

**変更ファイル 2**: `looplayer/player.py`

```python
# __init__ に追加
self._pre_fullscreen_geometry: QRect | None = None

# _restore_window_geometry() メソッドを追加（コンストラクタ末尾で呼ぶ）
def _restore_window_geometry(self):
    geo = self._settings.window_geometry
    if geo is None:
        return
    x, y, w, h = geo["x"], geo["y"], geo["width"], geo["height"]
    w = max(800, w)
    h = max(600, h)
    from PyQt6.QtCore import QPoint
    from PyQt6.QtWidgets import QApplication
    if QApplication.screenAt(QPoint(x, y)) is None:
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
    self.setGeometry(x, y, w, h)

# toggle_fullscreen() に追加（showFullScreen() 前）
self._pre_fullscreen_geometry = self.geometry()

# closeEvent() に追加（super().closeEvent(event) 前）
if self.isFullScreen() and self._pre_fullscreen_geometry:
    geo = self._pre_fullscreen_geometry
else:
    geo = self.geometry()
self._settings.window_geometry = {
    "x": geo.x(), "y": geo.y(),
    "width": geo.width(), "height": geo.height(),
}

# 表示メニューに追加
reset_window_action = QAction(t("menu.view.reset_window"), self)
reset_window_action.triggered.connect(self._reset_window_geometry)
view_menu.addSeparator()
view_menu.addAction(reset_window_action)

def _reset_window_geometry(self):
    self._settings.window_geometry = None
```

---

### F-201 外部字幕ファイルの読み込み

**変更ファイル**: `looplayer/player.py`

```python
# __init__ に追加
self._external_subtitle_path: Path | None = None

# 字幕メニューに追加（_rebuild_subtitle_menu 前に固定アクションとして追加）
# _build_menus() 内の _subtitle_menu 設定後:
open_sub_action = QAction(t("menu.playback.subtitle.open_file"), self)
open_sub_action.triggered.connect(self._open_subtitle_file)
self._subtitle_menu.addSeparator()
self._subtitle_menu.addAction(open_sub_action)

def _open_subtitle_file(self):
    if not self._current_video_path:
        QMessageBox.warning(self, t("msg.subtitle_no_video.title"),
                            t("msg.subtitle_no_video.body"))
        return
    path, _ = QFileDialog.getOpenFileName(
        self, t("menu.playback.subtitle.open_file"), "",
        "Subtitle Files (*.srt *.ass *.SRT *.ASS)"
    )
    if not path:
        return
    p = Path(path)
    if p.suffix.lower() not in (".srt", ".ass"):
        QMessageBox.warning(self, t("msg.subtitle_bad_format.title"),
                            t("msg.subtitle_bad_format.body"))
        return
    result = self.media_player.add_slave(
        vlc.MediaSlaveType.Subtitle, p.as_uri(), True
    )
    if result != 0:
        QMessageBox.warning(self, t("msg.subtitle_load_error.title"),
                            t("msg.subtitle_load_error.body"))
        return
    self._external_subtitle_path = p

# _open_video() 内で動画切替時にリセット
self._external_subtitle_path = None

# _rebuild_subtitle_menu() に外部字幕トラックの識別ロジックは不要
# （add_slave 後は VLC が自動的にトラックリストに追加するため、
#  既存の video_get_spu_description() で表示される）
```

---

### F-502 ツールチップの充実

**変更ファイル 1**: `looplayer/i18n.py`（data-model.md のキーをすべて追記）

**変更ファイル 2**: `looplayer/player.py`（各コントロールに `setToolTip()` を追加）

```python
# 再生/停止ボタン
self.play_btn.setToolTip(t("tooltip.btn.play"))
# シークバー
self.seek_slider.setToolTip(t("tooltip.seekbar"))
# 音量スライダー
self.volume_slider.setToolTip(t("tooltip.volume"))
# フレームボタン（A 点・B 点の ±1F ボタン）
self.frame_a_minus_btn.setToolTip(t("tooltip.btn.frame_a_minus"))
self.frame_a_plus_btn.setToolTip(t("tooltip.btn.frame_a_plus"))
self.frame_b_minus_btn.setToolTip(t("tooltip.btn.frame_b_minus"))
self.frame_b_plus_btn.setToolTip(t("tooltip.btn.frame_b_plus"))
# A/B 点セットボタン
self.set_a_btn.setToolTip(t("tooltip.btn.set_a"))
self.set_b_btn.setToolTip(t("tooltip.btn.set_b"))
# AB ループトグル
self.ab_loop_btn.setToolTip(t("tooltip.btn.ab_loop"))
# ポーズ間隔スピンボックス
self.pause_interval_spin.setToolTip(t("tooltip.pause_interval"))
```

**変更ファイル 3**: `looplayer/widgets/bookmark_row.py`（タグ・カウンターボタン）

```python
self.tags_btn.setToolTip(t("tooltip.btn.edit_tags"))
self.reset_count_btn.setToolTip(t("tooltip.btn.reset_play_count"))
```

---

## Constitution Check（Phase 1 後再確認）

| 原則 | 評価 | 判定 |
|------|------|------|
| I. テストファースト | テストファイル先行作成・RED→GREEN→Refactor を守る | ✅ PASS |
| II. シンプルさ重視 | 新規モジュールなし、メソッド追加最小限 | ✅ PASS |
| III. 過度な抽象化の禁止 | `_restore_window_geometry()` は 1 箇所のみ使用（コンストラクタ内）。許容範囲内 | ✅ PASS |
| IV. 日本語コミュニケーション | 全 i18n キー追加済み | ✅ PASS |

---

## リスクと注意事項

| リスク | 対策 |
|--------|------|
| `add_slave()` のリターン値が環境依存で 0 以外を返す可能性 | 統合テストで VLC モック使用、エラーメッセージ表示で対処 |
| フルスクリーン状態でのジオメトリが `showNormal()` で正しく復元されない場合 | `_exit_fullscreen()` 内で `_pre_fullscreen_geometry` を `setGeometry()` で明示復元する防御コードを追加 |
| `QApplication.screenAt()` の動作がマルチモニタ設定に依存 | 単一モニタ環境でのみユニットテスト。統合テストは手動確認 |
| player.py が 1600 行を超えており、ウィジェット名の確認が必要 | 実装前に `player.py` の該当箇所を Read ツールで確認してから編集 |
