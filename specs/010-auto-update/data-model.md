# Data Model: 自動更新機能 (010-auto-update)

## エンティティ

### UpdateInfo（値オブジェクト）

バージョン確認結果を保持する不変の値オブジェクト。永続化は行わない（メモリのみ）。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `latest_version` | `str` | 最新バージョン文字列（例: `"1.2.0"`、"v" プレフィックスなし） |
| `download_url` | `str` | プラットフォーム対応インストーラーの直接ダウンロード URL |
| `has_update` | `bool` | 現在バージョンより新しいかどうか |

**バリデーション**: `latest_version` はセマンティックバージョニング形式 (`\d+\.\d+\.\d+`) でなければならない。不正な場合はエラーとして扱う。

---

### AppSettings の追加フィールド

既存の `~/.looplayer/settings.json` に追記する新規フィールド:

| JSONキー | 型 | デフォルト | 説明 |
|---------|----|----------|------|
| `check_update_on_startup` | `bool` | `true` | アプリ起動時に更新確認を実行するか否か |

**既存フィールド（変更なし）**:
- `end_of_playback_action`: `"stop"` \| `"rewind"` \| `"loop"`

---

## 状態遷移

### 更新確認フロー

```
アプリ起動
    │
    ├─[check_update_on_startup=false]─→ スキップ（終了）
    │
    └─[true]──→ UpdateChecker スタート（バックグラウンド）
                    │
                    ├─[ネットワークエラー/タイムアウト]──→ サイレント終了
                    │
                    ├─[最新]──────────────────────────→ サイレント終了
                    │
                    └─[新バージョアリ]──→ 更新通知ダイアログ表示
                                              │
                                              ├─[あとで]──→ 終了（次回起動まで抑制）
                                              │
                                              └─[今すぐダウンロード]──→ DownloadDialog
                                                                            │
                                                              ┌─[完了]──→ インストーラー起動 → アプリ終了
                                                              ├─[失敗]──→ エラー表示 + 再試行/キャンセル
                                                              └─[キャンセル]──→ アプリ継続
```

### 手動確認フロー（ヘルプ → 更新を確認）

```
手動確認実行
    │
    ├─[ネットワークエラー]──→ エラーダイアログ表示
    ├─[最新]──────────────→ 「最新バージョンです」ダイアログ
    └─[新バージョアリ]────→ 更新通知ダイアログ（起動時フローと同一）
```

---

## 外部依存データ

### GitHub Releases API レスポンス（使用フィールドのみ）

```json
{
  "tag_name": "v1.2.0",
  "assets": [
    {
      "name": "LoopPlayer-Setup-1.2.0.exe",
      "browser_download_url": "https://github.com/jacobiz/looplayer/releases/download/v1.2.0/LoopPlayer-Setup-1.2.0.exe"
    },
    {
      "name": "LoopPlayer-1.2.0.dmg",
      "browser_download_url": "https://github.com/jacobiz/looplayer/releases/download/v1.2.0/LoopPlayer-1.2.0.dmg"
    }
  ]
}
```

### プラットフォーム別アセット選択ルール

| `sys.platform` | アセット名パターン | フォールバック |
|---------------|-----------------|-------------|
| `"win32"` | `LoopPlayer-Setup-{ver}.exe` | なし（対応外の場合は通知のみ） |
| `"darwin"` | `LoopPlayer-{ver}.dmg` | なし |
| その他 | — | ダウンロードをスキップ、通知のみ表示 |
