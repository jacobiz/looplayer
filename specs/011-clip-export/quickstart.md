# Quickstart: AB ループ区間クリップ書き出し

**Date**: 2026-03-17 | **Branch**: `011-clip-export`

## テストシナリオ（手動検証）

### シナリオ 1: 基本的なクリップ書き出し（US1）

```
前提: ffmpeg がインストール済みで PATH が通っている
前提: 動画ファイルを読み込んでいる
手順:
  1. A点（例: 15秒）を設定する
  2. B点（例: 45秒）を設定する
  3. ファイルメニュー → 「クリップを書き出す...」をクリック
  4. ファイル保存ダイアログが開く
     確認: デフォルトファイル名が "{元ファイル名}_00m15s-00m45s.mp4" になっている
     確認: デフォルトフォルダが元動画と同じフォルダになっている
  5. 保存先を確認して「保存」をクリック
  6. 書き出し中ダイアログが表示される
     確認: プログレスバーが往復アニメーションしている
     確認: 「キャンセル」ボタンがある
  7. 書き出し完了後、成功ダイアログが表示される
     確認: 「フォルダを開く」ボタンがある
  8. 出力ファイルをプレイヤーで開いて確認
     確認: 30 秒の区間（15〜45秒）のみ含まれる
     確認: 映像・音声品質が元と同等（コーデック一致）
期待結果: ✅ 書き出し成功
```

### シナリオ 2: AB ループ未設定時のメニュー無効化

```
前提: 動画ファイルを読み込んでいる
手順:
  1. AB ループをクリアした状態でファイルメニューを開く
  2. 「クリップを書き出す...」を確認
期待結果: ✅ 項目がグレーアウト（クリック不可）
```

### シナリオ 3: キャンセル動作

```
前提: ffmpeg インストール済み、AB ループ設定済み
手順:
  1. クリップ書き出しを開始
  2. 書き出し中ダイアログで「キャンセル」をクリック
  3. 出力先フォルダを確認
期待結果: ✅ ダイアログが閉じる
期待結果: ✅ 出力先に中途半端なファイルが残らない
```

### シナリオ 4: ffmpeg 未インストール

```
前提: ffmpeg が PATH に存在しない（またはアンインストール済み）
手順:
  1. AB ループを設定
  2. ファイルメニュー → 「クリップを書き出す...」をクリック
期待結果: ✅ 「ffmpeg が見つかりません」エラーダイアログが表示される
期待結果: ✅ ffmpeg 公式ダウンロード URL が表示される
期待結果: ✅ アプリがクラッシュしない
```

### シナリオ 5: ブックマークから書き出し（US2）

```
前提: ffmpeg インストール済み、ブックマークに A点・B点が設定済み
手順:
  1. ブックマーク行を右クリック
  2. コンテキストメニューに「クリップを書き出す」が表示されることを確認
  3. クリックして書き出しを実行
  4. デフォルトファイル名を確認
     確認: ブックマーク名を含むファイル名になっている
  5. 保存して完了を確認
期待結果: ✅ ブックマークの A〜B 区間のみを含む動画ファイルが生成される
```

### シナリオ 6: A点・B点未設定のブックマーク

```
前提: ブックマークが存在するが A点またはB点が未設定
手順:
  1. 該当ブックマーク行を右クリック
  2. コンテキストメニューを確認
期待結果: ✅ 「クリップを書き出す」項目がグレーアウト（クリック不可）
```

---

## ユニットテストシナリオ（自動化対象）

### ExportWorker テスト

| テスト | 前提 | シグナル | 確認内容 |
|--------|------|---------|---------|
| `test_export_worker_emits_finished_on_success` | subprocess モック（returncode=0） | `finished` | 出力パスが渡される |
| `test_export_worker_emits_failed_on_ffmpeg_error` | subprocess モック（returncode=1） | `failed` | エラーメッセージが渡される |
| `test_export_worker_emits_failed_when_ffmpeg_not_found` | `shutil.which` → None | `failed` | ffmpeg 未検出メッセージ |
| `test_export_worker_deletes_file_on_cancel` | subprocess モック + requestInterruption | なし | 出力ファイルが削除される |
| `test_export_worker_builds_correct_ffmpeg_command` | subprocess モック | `finished` | コマンドが `-ss START -to END -i INPUT -c copy OUTPUT` の順 |

### ClipExportJob テスト

| テスト | 確認内容 |
|--------|---------|
| `test_default_filename_format` | `{stem}_00m15s-01m30s.mp4` の形式 |
| `test_bookmark_filename_sanitizes_special_chars` | `\ / : * ? " < > |` → `_` |
| `test_ms_to_ffmpeg_time_conversion` | `15250` → `"00:00:15.250"` |

### 統合テスト（player.py）

| テスト | 確認内容 |
|--------|---------|
| `test_clip_export_menu_disabled_without_ab_loop` | AB ループ未設定時にアクションが disabled |
| `test_clip_export_menu_enabled_with_ab_loop` | AB ループ設定済みでアクションが enabled |
| `test_clip_export_menu_disabled_during_export` | 書き出し中はアクションが disabled |
