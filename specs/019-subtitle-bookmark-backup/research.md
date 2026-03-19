# Research: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Phase 0 output** | **Date**: 2026-03-19 | **Branch**: `019-subtitle-bookmark-backup`

---

## 1. SRT パース方式

**Decision**: Python 標準ライブラリの `re` モジュールで直接パース
**Rationale**: プロジェクトは外部ライブラリ追加を避ける方針（YAGNI）。SRT フォーマットは仕様が単純（連番 → タイムスタンプ行 → テキスト行 → 空行）で `re` で十分。pysrt などサードパーティは不要。
**Alternatives considered**:
- `pysrt` / `srt` ライブラリ: 既存依存に追加することになり方針に反する
- 手動ステートマシン: `re` より複雑になるため却下

**実装詳細**:
```
SRT タイムスタンプ形式: HH:MM:SS,mmm --> HH:MM:SS,mmm
正規表現: r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
```

---

## 2. ASS タグ除去方式

**Decision**: 正規表現 `re.sub(r'\{[^}]*\}', '', text)` で装飾タグを除去
**Rationale**: ASS の装飾タグはすべて `{...}` 形式（`{\an8}`, `{\b1}`, `{\c&H00FF00&}` など）。単純な正規表現で一括除去可能。
**Alternatives considered**:
- `ass` ライブラリ: 外部依存追加のため却下
- 手動パース: `re` より複雑になるため却下

**ASS イベント行形式**:
```
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,テキスト
           ↑レイヤー ↑開始     ↑終了    ↑スタイル          ↑本文
```
タイムスタンプ形式: `H:MM:SS.cc`（センチ秒単位・100ms 刻み）

---

## 3. エンコーディング検出方式

**Decision**: まず UTF-8 で試みて失敗したら Shift-JIS (cp932) で再試行。それでも失敗したらエラーメッセージ表示。
**Rationale**: 日本語字幕ファイルの現実的なエンコーディングは UTF-8 と Shift-JIS の 2 択がほとんど。`chardet` などは外部依存となるため不使用。既存コードの `subtitle_load_error` メッセージとは別に「エンコーディング非対応」メッセージを追加。
**Alternatives considered**:
- `chardet`: 外部依存のため却下
- UTF-8 のみ対応: Shift-JIS ファイルが多い日本語環境では UX が悪い

---

## 4. Undo（元に戻す）方式

**Decision**: `bookmark_panel.py` の既存 `_undo_delete` パターンを参考に `_last_bulk_add: list[LoopBookmark]` を保持し `undo_bulk_add()` で一括削除
**Rationale**: 既存の Undo は「削除した 1 件を復元」するパターン（`_pending_delete` リスト）。同じ設計で「追加したブックマークを全削除」する逆操作として実装できる。QUndoStack は導入せず、「一括生成のみ元に戻せる」という限定的な Undo で仕様を満たす。
**Alternatives considered**:
- QUndoStack / QUndoCommand: 汎用 Undo フレームワーク。過度な抽象化に当たり YAGNI 違反
- 複数世代の Undo: 仕様外（FR-008 は「全件削除のみ」）

---

## 5. ZIP バックアップ方式

**Decision**: Python 標準ライブラリ `zipfile.ZipFile` を使用。各 JSON ファイルをフラット構造で ZIP に格納し、マニフェスト `looplayer-backup.json` を含める。
**Rationale**: `zipfile` は Python 標準ライブラリ。外部依存ゼロで要件を満たせる。フラット構造（サブディレクトリなし）にすることで復元時のパス解決が簡単になる。
**ZIP 内構造**:
```
looplayer-backup-YYYYMMDD-HHMMSS.zip
├── looplayer-backup.json    # マニフェスト（バージョン・作成日時・ファイル一覧）
├── bookmarks.json
├── settings.json
├── positions.json
└── recent_files.json        # 存在する場合のみ
```
**Alternatives considered**:
- `tarfile`: ZIP より馴染みが薄い（Windows ユーザーへの視認性が低い）
- `shutil.make_archive`: マニフェスト追加が難しいため却下

---

## 6. バックアップ対象ファイルの存在確認

**Decision**: `~/.looplayer/` 以下の 4 ファイルそれぞれを `Path.exists()` で確認し、存在するもののみ ZIP に含める。全ファイルが存在しない場合はエラーメッセージを表示して ZIP 作成をスキップ。
**Rationale**: 新規インストール直後など一部ファイルが未生成の場合も正常動作させるため。

---

## 7. 復元後の再起動方式

**Decision**: `QApplication.quit()` を呼び出してアプリを終了する（再起動は OS/ユーザー操作に委ねる）
**Rationale**: 仕様の clarification で「再起動必須 — アプリを再起動してください」と確定済み（FR-015）。自動再起動（`subprocess.Popen` + `sys.exit`）は環境依存の問題が生じやすいため、終了のみとする。
**Alternatives considered**:
- 自動再起動: Windows インストーラ環境でパス解決が複雑になるため却下
- インメモリリロード: 全モジュールの状態をリセットする必要があり複雑度が高い

---

## 8. メニュー配置・有効化条件

**F-202 メニュー**:
- 場所: 再生(&P) > 字幕(&S) サブメニュー（「字幕ファイルを開く...」の下、セパレータの後）
- 有効化条件: 動画が開かれており（`self._current_path is not None`）かつ外部字幕が読み込まれている（`self._external_subtitle_path is not None`）

**F-402 メニュー**:
- 場所: ファイル(&F) メニュー（「クリップを書き出す...」の前・セパレータで区切る）
- 有効化条件: 常に有効（データファイルが存在しない場合はメッセージで対応）

---

## 9. テスト方針

**ユニットテスト**:
- `test_subtitle_parser.py`: SRT パース・ASS パース・タグ除去・エンコーディング・切り詰め・無効エントリスキップを個別テスト
- `test_data_backup.py`: ZIP 作成・マニフェスト検証・ファイル不存在ケース・破損 ZIP 検出・復元処理を `tmp_path` で分離

**統合テスト**:
- `test_subtitle_bookmark_integration.py`: BookmarkStore を実際に使い字幕→ブックマーク生成→Undo サイクルを検証

**TDD 順序**: テスト先に書き→失敗確認→最小実装→パス確認（constitution I. 準拠）

