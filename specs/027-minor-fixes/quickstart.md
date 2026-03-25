# Quickstart: 細かな修正（バージョン更新キャッシュ短縮・B点アイコン改善）

**Branch**: `027-minor-fixes` | **Date**: 2026-03-25

---

## 概要

2 つの独立した修正を含む。それぞれ単独で動作確認できる。

---

## Step 1: セットアップ（ベースライン確認）

```bash
# 既存テストが全 PASS であることを確認
pytest tests/unit/test_updater.py -v
pytest tests/integration/test_button_icons_p2.py -v
```

---

## Step 2: US1 - バージョン更新キャッシュ境界テスト

### 手動確認手順

1. アプリを起動して更新チェックを1回実行させる
2. `~/.looplayer/settings.json` を開き `last_update_check_ts` の値（Unix タイムスタンプ）を確認する
3. タイムスタンプを「現在時刻 − 5時間」に書き換えてアプリを再起動する
   → 更新チェックが**スキップされる**こと（ログ出力なし）を確認
4. タイムスタンプを「現在時刻 − 7時間」に書き換えてアプリを再起動する
   → 更新チェックが**実行される**こと（GitHub API へのネットワークアクセスが発生する）を確認

### 受け入れ基準

| シナリオ | 期待動作 |
|----------|----------|
| 前回チェックから 5h 経過 | チェックをスキップ（up_to_date シグナル発行） |
| 前回チェックから 7h 経過 | GitHub API へアクセスしてチェック実行 |

---

## Step 3: US2 - B点アイコン対称確認

### 手動確認手順

1. アプリを起動し、ABループコントロール部分を目視確認する
2. A点セットボタン（I キー対応）と B点セットボタン（O キー対応）を並べて確認する
   → A点: ⏮（縦棒+左矢印 = `SP_MediaSkipBackward`）
   → B点: ⏭（右矢印+縦棒 = `SP_MediaSkipForward`）
3. 両アイコンが左右対称のペアに見えることを確認する
4. B点ボタンにカーソルを当ててツールチップを確認する
   → ツールチップが従来どおり表示されること（機能・ラベルは変更なし）

### 受け入れ基準

| 確認項目 | 期待状態 |
|----------|----------|
| B点アイコン | ⏭（右矢印+縦棒）が表示される |
| A点・B点の対称性 | 左右対称のペアに見える |
| B点ツールチップ | 変更前と同じ内容が表示される |
| B点クリック動作 | 変更前と同じ動作（B点がセットされる） |

---

## Step 4: 回帰確認

```bash
pytest tests/unit/test_updater.py -v
pytest tests/unit/test_seekbar_click_loop.py -v
pytest tests/integration/test_button_icons_p2.py -v
pytest tests/integration/test_ab_loop.py -v
```

全テストが PASS であることを確認する。
