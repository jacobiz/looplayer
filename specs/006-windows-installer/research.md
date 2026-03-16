# Research: Windows スタンドアロンアプリ インストーラ

**Branch**: `006-windows-installer` | **Date**: 2026-03-16

## 決定事項

### 1. Python バンドラー: PyInstaller

**Decision**: PyInstaller を使用する（既存の build-windows.yml と同じ）

**Rationale**:
- PyQt6 6.x および python-vlc との相性が最も安定している
- `--onefile` で単一 .exe を生成できる
- 月間 476 万ダウンロードの実績あり、VLC バンドルの事例が豊富
- 既存の `.github/workflows/build-windows.yml` で既に採用済み

**Alternatives considered**:
- Nuitka: 起動速度は 2〜4 倍速いが、C++ ツールチェーンが必要でビルド時間が長い。UI アプリには不要
- cx_Freeze: VLC サポートが薄く、コミュニティ事例が少ない

**Known issues**:
- `--onefile` では起動時に一時ディレクトリへ展開するため、起動が 1〜3 秒遅くなる
- VLC プラグインディレクトリを明示的に `--add-data` で指定しないと動画再生が失敗する
- 既存の build-windows.yml の `--add-binary` 指定に `libvlccore.dll` の扱いが不完全な可能性あり → `.spec` ファイルで管理推奨

**Typical output size**: PyQt6 + python-vlc バンドル込みで 120〜200MB

---

### 2. インストーラフレームワーク: Inno Setup

**Decision**: Inno Setup を使用する

**Rationale**:
- 日英 2 言語対応を標準サポート（25 言語のビルトイン翻訳）
- Windows システム言語を自動検出して UI 言語を切り替える
- インストール失敗時の自動ロールバックが標準機能として組み込まれている
- 「アプリと機能」への登録が自動（レジストリへの Uninstall エントリ自動生成）
- 無料・オープンソース
- シンプルな Pascal スクリプトで記述でき、NSIS より習得コストが低い

**Alternatives considered**:
- WiX Toolset v6: MSI 形式が必要な企業向け配布に適するが、XML + C# の学習コストが高い。今回のスコープには過剰
- NSIS: インストーラ本体が 34KB と最小だが、多言語対応にプラグイン追加が必要でスクリプトが複雑

**Inno Setup での多言語設定**:
```ini
[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
```
システム言語が日本語なら日本語 UI、それ以外は英語 UI で表示される。

---

### 3. VLC 依存ライブラリのバンドル方法

**Decision**: PyInstaller `.spec` ファイルを使い、VLC DLL とプラグインを明示的に指定する

**Rationale**:
コマンドラインオプションよりも `.spec` ファイルのほうが管理しやすく、パスや設定の変更に強い。

**必要なファイル**:
- `libvlc.dll`
- `libvlccore.dll`
- `plugins/` ディレクトリ（コーデック等が含まれる）

**ランタイムでのプラグインパス設定**:
バンドルされた exe 起動時に VLC_PLUGIN_PATH を設定する必要がある。`player.py` の vlc.Instance() 生成前に以下を追加:

```python
import sys, os
if getattr(sys, 'frozen', False):
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'plugins')
```

---

### 4. GitHub Releases への配布

**Decision**: `gh release create` を使い、バージョンタグのプッシュをトリガーに自動アップロードする

**Rationale**:
- 既存の GitHub Actions 環境と統合が容易
- `GITHUB_TOKEN` のみで認証可能
- インストーラ .exe と SHA256 チェックサムを同時に添付できる

**基本コマンド**:
```bash
gh release create v1.0.0 \
  "dist/LoopPlayer-Setup.exe#LoopPlayer インストーラ (Windows)" \
  --title "LoopPlayer v1.0.0" \
  --generate-release-notes
```

---

## ファイルサイズ見込み

| 成果物 | サイズ目安 |
|--------|-----------|
| PyInstaller 出力 (.exe) | 120〜200MB |
| Inno Setup インストーラ (.exe) | 80〜140MB（圧縮済み）|
| SC-002 基準（200MB 以下） | 達成可能 |

---

## ビルド環境

- GitHub Actions の `windows-latest` ランナーで PyInstaller + Inno Setup をネイティブ実行
- Inno Setup は Chocolatey でインストール: `choco install innosetup`
- VLC は Chocolatey でインストール: `choco install vlc`（既存）
