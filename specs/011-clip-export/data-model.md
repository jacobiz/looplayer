# Data Model: AB ループ区間クリップ書き出し

**Date**: 2026-03-17 | **Branch**: `011-clip-export`

## エンティティ

### ClipExportJob

書き出し1件を表す不変データクラス。

| フィールド | 型 | 説明 | バリデーション |
|-----------|-----|------|--------------|
| `source_path` | `Path` | 元動画ファイルの絶対パス | 存在確認は書き出し実行時 |
| `start_ms` | `int` | A点（ミリ秒、0以上） | start_ms < end_ms |
| `end_ms` | `int` | B点（ミリ秒、start_msより大） | end_ms > start_ms |
| `output_path` | `Path` | 出力先絶対パス | 親ディレクトリの存在確認は書き出し実行時 |

**バリデーションルール**:
- `start_ms >= 0`
- `end_ms > start_ms`（区間長 0 は不可）
- `source_path.suffix == output_path.suffix` を推奨（異なるコンテナは ffmpeg エラーになる）

**導出値**（フィールドではなくプロパティ）:
- `duration_ms: int` = `end_ms - start_ms`

---

### ExportWorker (QThread)

`ClipExportJob` を受け取り ffmpeg subprocess を実行するバックグラウンドスレッド。

**シグナル**:

| シグナル | 引数 | タイミング |
|---------|------|----------|
| `finished` | `str`（出力ファイルの絶対パス） | ffmpeg が戻り値 0 で終了したとき |
| `failed` | `str`（エラーメッセージ） | ffmpeg エラー・ffmpeg 未検出・ファイル不存在など |

**状態遷移**:
```
idle → running → finished
                → failed
                → cancelled (isInterruptionRequested → ファイル削除 → 静かに終了)
```

**責務境界**:
- ffmpeg 検出（`shutil.which`）
- タイムスタンプ変換（ms → HH:MM:SS.mmm）
- subprocess 起動・監視・キャンセル
- 失敗・キャンセル時のファイル削除

---

### ExportProgressDialog (QDialog)

不確定プログレスバーとキャンセルボタンを持つモーダルダイアログ。`ExportWorker` を内包して管理する。

**UI 要素**:
- `QLabel`: 「書き出し中...」メッセージ
- `QProgressBar`: `setRange(0, 0)`（往復アニメーション）
- `QPushButton`: 「キャンセル」

**シグナル接続**:
- `ExportWorker.finished` → `_on_finished()` → ダイアログを accept、成功通知を表示
- `ExportWorker.failed` → `_on_failed()` → エラーメッセージを表示、ダイアログを reject

---

## 既存エンティティとの関係

| 既存エンティティ | 関係 |
|----------------|------|
| `VideoPlayer.loop_a_ms / loop_b_ms` | ClipExportJob の `start_ms` / `end_ms` の元データ |
| `LoopBookmark.loop_a_ms / loop_b_ms` | US2: ブックマークからのクリップ書き出しの元データ |
| `AppSettings` | 変更なし（書き出し設定の永続化は対象外） |

## デフォルトファイル名生成ルール

```
{source_path.stem}_{start_label}-{end_label}{source_path.suffix}
```

- `start_label` = A点を `{分:02d}m{秒:02d}s` 形式に変換（例: `00m15s`）
- `end_label` = B点を同形式に変換（例: `01m30s`）
- ブックマークから書き出す場合: `{sanitized_bookmark_name}_{start_label}-{end_label}{suffix}`
- 安全な文字置換: `\ / : * ? " < > |` → `_`
