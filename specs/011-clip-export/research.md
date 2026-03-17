# Research: AB ループ区間クリップ書き出し

**Date**: 2026-03-17 | **Branch**: `011-clip-export`

## ffmpeg ストリームコピーの最適コマンド構成

**Decision**: `ffmpeg -ss START -to END -i INPUT -c copy OUTPUT -y`

**Rationale**:
- `-ss` を `-i` の**前**に置くことで入力シーク（input seeking）が有効になり、キーフレームレベルの高速シークが実現する。`-i` の後に置くと出力シーク（output seeking）となり、先頭から全フレームをデコードするため低速
- `-to` は絶対タイムスタンプ指定。`-t`（継続時間）より直感的で、A点・B点の ms 値をそのまま変換できる
- ストリームコピーではキーフレーム境界で切り出されるため、最大でキーフレーム間隔分の誤差が生じる（通常 < 2 秒）。SC-002 の「前後 0.5 秒以内の誤差を許容」に対して許容範囲内
- `-y`: OS の保存ダイアログで上書き確認済みのため、ffmpeg 側の確認プロンプトを抑止

**Alternatives considered**:
- `-t`（継続時間）: 計算が必要で誤りやすい。棄却
- `-i` 後の `-ss`（output seeking）: 精度は高いが数倍低速。棄却
- `-accurate_seek`: 高精度だが低速かつコーデック依存。棄却

**タイムスタンプフォーマット変換**:
```
ms → HH:MM:SS.mmm
例: 15250 ms → "00:00:15.250"
```

---

## ffmpeg 検出方法

**Decision**: `shutil.which("ffmpeg")` を書き出し操作実行時（遅延検出）に呼ぶ

**Rationale**:
- `shutil.which()` はクロスプラットフォーム（Windows の `.exe` も自動考慮）
- 起動時チェックは不要（ffmpeg を使わないユーザーに無用な負荷）
- 検出に失敗した場合、エラーダイアログに公式ダウンロード URL を表示

**Alternatives considered**:
- `subprocess.run(["ffmpeg", "-version"])`: オーバーヘッドが大きい。棄却
- 起動時チェック: シンプルさを優先して棄却

---

## subprocess キャンセル戦略

**Decision**: `proc.terminate()` → `proc.wait(timeout=5)` → タイムアウト時 `proc.kill()`

**Rationale**:
- `terminate()` は SIGTERM（Unix）/ TerminateProcess（Windows）を送信。ffmpeg は SIGTERM を受け取ると出力を適切にクローズする
- `wait(timeout=5)` でプロセス終了を確認してからファイル削除
- タイムアウト後の `kill()` はフォールバック（通常不要）

**Alternatives considered**:
- `stdin` に `q` を送る: 対話的 TTY を前提とするため `subprocess.PIPE` 環境では動作不安定。棄却
- `kill()` 直接: SIGKILL は出力ファイルが不完全な状態で残る可能性がある。棄却

---

## QThread パターン

**Decision**: `updater.py` の `DownloadThread` と同一パターン

**Rationale**:
- `isInterruptionRequested()` を 100ms ポーリングで確認
- シグナル: `finished(str)` / `failed(str)` のみ（進捗% は不要）
- キャンセル時はファイルを削除してから静かに終了

**既存コードとの整合**:
- `looplayer/updater.py:101-128` の `DownloadThread` をテンプレートとして採用

---

## 不確定プログレスバー

**Decision**: `QProgressBar.setRange(0, 0)`

**Rationale**:
- minimum == maximum のとき PyQt6 は往復アニメーション（busy indicator）を自動表示
- `setRange(0, 100)` + 手動更新は不要（% が取れないため）
- 既存の `DownloadDialog` のプログレスバーを参考に構成
