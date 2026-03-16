# Tasks: Windows スタンドアロンアプリ インストーラ

**Input**: Design documents from `/specs/006-windows-installer/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: タスクはユーザーストーリー単位でグループ化されており、各ストーリーを独立して実装・テスト・デモできる。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: 対象ユーザーストーリー（US1, US2, US3）
- ファイルパスをすべての説明に含める

---

## Phase 1: Setup（共有インフラ）

**Purpose**: ビルドツール用のディレクトリ構造とバージョン管理の初期化

- [x] T001 `installer/` ディレクトリを作成する（`looplayer.spec`, `looplayer.iss`, `build.ps1` の置き場）
- [x] T002 [P] `looplayer/version.py` を作成し `VERSION`, `APP_NAME`, `PUBLISHER` 定数を定義する

---

## Phase 2: Foundational（全ストーリーの前提条件）

**Purpose**: バンドルされた exe が正しく動作するための修正。すべてのユーザーストーリーはこのフェーズの完了後に開始できる。

**⚠️ CRITICAL**: このフェーズが完了するまでインストーラのテストは不可能

> **Constitution I. テストファースト**: T003・T004 で `player.py` を修正する前に、既存テストがパスすることを確認すること
> `pytest tests/unit/ -v` を実行し、すべてグリーンであることを確認してから着手する

- [x] T003 `looplayer/player.py` の `vlc.Instance()` 生成前に frozen exe 実行時の `VLC_PLUGIN_PATH` 設定コードを追加する（`sys.frozen` チェック）
- [x] T004 `looplayer/player.py` のウィンドウタイトルを `version.py` の `APP_NAME` と `VERSION` を参照するよう更新する
- [x] T005 `installer/looplayer.spec` を作成する（`libvlc.dll`, `libvlccore.dll`, `plugins/` を `--add-binary`/`--add-data` で指定）

**Checkpoint**: `pyinstaller installer/looplayer.spec` が成功し、生成された `dist/LoopPlayer.exe` が動画を再生できる状態

---

## Phase 3: User Story 1 - インストーラを実行してアプリをインストールする（Priority: P1）🎯 MVP

**Goal**: Python 未インストールの Windows 10/11 環境で `.exe` をダブルクリックするだけで LoopPlayer をインストールし起動できる

**Independent Test**: Python 未インストールの Windows 環境に `LoopPlayer-Setup-x.x.x.exe` を転送して実行し、デスクトップショートカットから LoopPlayer が起動して動画を再生できることを確認する

### Implementation for User Story 1

- [x] T006 [US1] `installer/looplayer.iss` を作成する（`AppName`, `AppVersion`, `DefaultDirName=%LOCALAPPDATA%\LoopPlayer`, `PrivilegesRequired=lowest`）
- [x] T007 [US1] `installer/looplayer.iss` の `[Languages]` セクションに日本語・英語の 2 言語エントリを追加する（`Japanese.isl` + `Default.isl`）
- [x] T008 [US1] `installer/looplayer.iss` の `[Icons]` セクションにデスクトップとスタートメニューのショートカットを追加する
- [x] T009 [US1] `installer/looplayer.iss` の `[Run]` セクションに「インストール完了後に起動する」オプションを追加する
- [x] T010 [US1] `installer/build.ps1` を作成する（PyInstaller でビルド → Inno Setup でインストーラ生成 → SHA256 チェックサム出力）

**Checkpoint**: `installer/build.ps1` を実行して `dist/LoopPlayer-Setup-x.x.x.exe` が生成され、Python 未インストール環境でインストール・起動が成功する

---

## Phase 4: User Story 2 - アプリをアンインストールする（Priority: P2）

**Goal**: Windows の「アプリと機能」から LoopPlayer を選択してアンインストールでき、ユーザーデータ（`~/.looplayer/`）が保持される

**Independent Test**: インストール後に「アプリと機能」から LoopPlayer を選択してアンインストールを実行し、アプリファイル・ショートカットが消え、`~/.looplayer/` フォルダが残っていることを確認する

### Implementation for User Story 2

- [x] T011 [US2] `installer/looplayer.iss` の `[Setup]` セクションに `CreateUninstallRegKey=yes`, `UninstallDisplayName=LoopPlayer` を追加して「アプリと機能」への登録を確実にする
- [x] T012 [US2] `installer/looplayer.iss` の `[UninstallDelete]` セクションを追加し、アプリフォルダ（`{app}`）のみを削除対象とする（`~/.looplayer/` は対象外）
- [x] T013 [US2] `installer/looplayer.iss` の `[Setup]` セクションに `CloseApplications=yes` を追加してアンインストール前に起動中のアプリを閉じる処理を追加する
- [x] T013b [US2] `quickstart.md` の手動テスト手順に「インストール中に強制終了した場合、`%LOCALAPPDATA%\LoopPlayer` にファイルが残っていないこと（FR-011: Inno Setup 標準ロールバック）」の確認項目を追記する

**Checkpoint**: アンインストール後に `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\LoopPlayer` が削除され、`~/.looplayer/` が残っている

---

## Phase 5: User Story 3 - 同じ PC で新バージョンに更新する（Priority: P3）

**Goal**: 旧バージョンがインストール済みの PC で新バージョンのインストーラを実行すると上書きアップデートされ、ユーザーデータが保持される

**Independent Test**: 旧バージョンをインストール後に新バージョンのインストーラを実行し、起動時のタイトルバーで新バージョン番号を確認し、`~/.looplayer/bookmarks.json` が残っていることを確認する

### Implementation for User Story 3

- [x] T014 [US3] `installer/looplayer.iss` の `[Setup]` セクションに `AppId={{GUID}}` を追加する（Inno Setup が既存インストールを識別するための固定 GUID）
- [x] T015 [US3] `installer/looplayer.iss` の `[Setup]` セクションに `VersionInfoVersion={#AppVersion}` を追加してバージョン情報を .exe に埋め込む
- [x] T016 [US3] `.github/workflows/release.yml` を新規作成する（`v*` タグプッシュトリガー、VLC + Inno Setup インストール、PyInstaller ビルド、Inno Setup ビルド、`gh release create` で GitHub Releases に公開）
- [x] T017 [US3] `.github/workflows/release.yml` に SHA256 チェックサムファイル（`SHA256SUMS.txt`）の生成とアップロードを追加する

**Checkpoint**: `git tag v1.0.0 && git push origin v1.0.0` で GitHub Actions が起動し、リリースページにインストーラと SHA256 が添付される

---

## Phase 6: Polish & 横断的な改善

**Purpose**: 既存ファイルの整理と手順文書の仕上げ

- [x] T018 [P] `.github/workflows/build-windows.yml` を更新して `installer/looplayer.spec` を参照するよう修正し、`master` ブランチ名を `main` に変更する
- [x] T019 [P] `README.md` にインストーラのダウンロード方法（GitHub Releases リンク）とリリース手順を追記する
- [ ] T020 `quickstart.md` のテスト手順に従って Windows 実機での最終動作確認を実施し、結果を記録する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし。即座に開始可能
- **Foundational (Phase 2)**: Phase 1 の完了が前提。**全ユーザーストーリーをブロック**
- **US1 (Phase 3)**: Phase 2 の完了が前提。MVP
- **US2 (Phase 4)**: Phase 3 に依存（`looplayer.iss` の拡張のため）
- **US3 (Phase 5)**: Phase 3 に依存（同上）。US2 と並列実行可能
- **Polish (Phase 6)**: 必要なストーリーの完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 完了後に開始可能
- **US2 (P2)**: US1 完了後（`looplayer.iss` の拡張）
- **US3 (P3)**: US1 完了後（`looplayer.iss` の拡張）。US2 と並列実行可能

### Within Each User Story

- `looplayer.iss` の編集タスクは順番に実行（同一ファイル）
- GitHub Actions ワークフロー（T016, T017）は並列実行可能

### Parallel Opportunities

- T002（version.py）は T001 完了後 T003/T004 と並列実行可能
- T016（release.yml 作成）は T015 完了後 T017 と並列実行可能
- T018（build-windows.yml 更新）と T019（README 更新）は並列実行可能

---

## Parallel Example: User Story 3

```bash
# T016 と T017 は同じ新規ファイルの異なる部分を対象とするが、
# T016 で基本構造を作成後 T017 で SHA256 部分を追加する順番が安全:
Task T016: .github/workflows/release.yml の基本ビルド・リリース処理を作成
Task T017: release.yml に SHA256 チェックサム生成・アップロードを追加
```

---

## Implementation Strategy

### MVP First（User Story 1 のみ）

1. Phase 1: Setup を完了
2. Phase 2: Foundational を完了（CRITICAL）
3. Phase 3: User Story 1 を完了
4. **STOP & VALIDATE**: Windows 実機でインストール・起動を確認
5. 動作確認後に US2・US3 へ進む

### Incremental Delivery

1. Setup + Foundational → 動作する exe が生成される
2. US1 完了 → インストーラ .exe が配布可能 → **MVP リリース可能**
3. US2 完了 → アンインストール対応
4. US3 完了 → バージョンアップ対応 + GitHub Releases 自動公開

---

## Notes

- [P] タスクは異なるファイルを対象とするため並列実行可能
- インストーラのテストは **Windows 実機**が必要（Linux CI 環境では不可）
- `looplayer.iss` の `AppId` に使う GUID は `uuidgen` または https://www.guidgenerator.com で生成
- `installer/looplayer.spec` の VLC パスは `C:\Program Files\VideoLAN\VLC` を前提（Chocolatey インストール）
- 各フェーズ完了後にコミットして進捗を記録する
