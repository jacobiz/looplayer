# UI Contracts: AB ループ区間クリップ書き出し

**Date**: 2026-03-17 | **Branch**: `011-clip-export`

## Contract 1: ファイルメニュー「クリップを書き出す...」

### 状態条件

| 条件 | メニュー項目の状態 |
|------|-----------------|
| 動画未読み込み | 無効（disabled） |
| 動画読み込み済み、A点またはB点が未設定 | 無効（disabled） |
| 動画読み込み済み、A点・B点ともに設定済み | 有効（enabled） |
| A点 == B点（区間長 0） | 無効（disabled） |
| 書き出し中 | 無効（disabled）— 二重起動防止 |

### アクション

- **トリガー**: `QAction.triggered`
- **前処理**: ffmpeg 検出（`shutil.which("ffmpeg")`）
  - 未検出時: エラーダイアログを表示して終了
  - 検出済み: ファイル保存ダイアログを表示
- **ファイル保存ダイアログ**: `QFileDialog.getSaveFileName`
  - デフォルトディレクトリ: 元動画と同じフォルダ
  - デフォルトファイル名: `{stem}_{start_label}-{end_label}{suffix}`
  - フィルター: 元ファイルの拡張子 + 「すべてのファイル」
- **キャンセル時**: ダイアログを閉じて終了（何もしない）
- **確定時**: `ExportProgressDialog` を表示して書き出し開始

---

## Contract 2: ExportProgressDialog

### 表示条件

- `ExportProgressDialog.exec()` 呼び出しで表示（モーダル）
- 表示と同時に `ExportWorker.start()` を呼ぶ

### UI 要素

| 要素 | 状態 |
|------|------|
| ウィンドウタイトル | 「クリップを書き出し中...」 |
| ラベル | 「書き出し中...」（初期値）、エラー時はエラーメッセージ |
| プログレスバー | `setRange(0, 0)`（往復アニメーション） |
| キャンセルボタン | 常に表示。書き出し中は「キャンセル」、完了時はボタン非表示 |

### シグナルフロー

```
ExportWorker.finished(path)
  → ダイアログを accept()
  → 成功 QMessageBox を表示（「フォルダを開く」ボタン付き）

ExportWorker.failed(error)
  → ラベルにエラーメッセージを表示
  → ダイアログを reject()

キャンセルボタン押下
  → ExportWorker.requestInterruption()
  → ExportWorker.wait()
  → ダイアログを reject()
```

### closeEvent

- スレッド実行中は `requestInterruption()` + `wait()` を実行してから `accept()`

---

## Contract 3: 成功通知ダイアログ

### 表示条件

- 書き出し成功時（`ExportWorker.finished` シグナル受信後）

### UI 要素

- `QMessageBox.information` ベース
- タイトル: 「書き出し完了」
- 本文: 「{ファイル名} を書き出しました。」
- ボタン: 「フォルダを開く」（クリックで出力先フォルダを OS ファイルマネージャーで開く）、「OK」

---

## Contract 4: エラーダイアログ（ffmpeg 未検出）

### UI 要素

- `QMessageBox.warning` ベース
- タイトル: 「ffmpeg が見つかりません」
- 本文: 「クリップの書き出しには ffmpeg が必要です。\nhttps://ffmpeg.org/download.html からインストールしてください。」
- ボタン: 「OK」

---

## Contract 5: ブックマーク行コンテキストメニュー「クリップを書き出す」

### 表示条件

- `BookmarkRow` を右クリックしたときのコンテキストメニューに追加

### 状態条件

| 条件 | 項目の状態 |
|------|----------|
| `loop_a_ms` と `loop_b_ms` が両方設定済み（かつ a < b） | 有効 |
| どちらか一方でも None、または a >= b | 無効（disabled） |

### アクション

- Contract 1 と同じフロー（ffmpeg 検出 → 保存ダイアログ → ExportProgressDialog）
- デフォルトファイル名: `{sanitized_bookmark_name}_{start_label}-{end_label}{suffix}`
