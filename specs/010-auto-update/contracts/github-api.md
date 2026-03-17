# Contract: GitHub Releases API

## エンドポイント

```
GET https://api.github.com/repos/jacobiz/looplayer/releases/latest
```

## リクエスト

| ヘッダー | 値 | 必須 |
|---------|-----|------|
| `User-Agent` | `LoopPlayer/{CURRENT_VERSION}` | 必須（GitHub API 要件） |

タイムアウト: **5 秒**

## レスポンス（成功: HTTP 200）

使用するフィールドのみ記載:

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

## バージョン抽出ルール

- `tag_name` から先頭の `"v"` を除去して比較用バージョン文字列を得る
  - 例: `"v1.2.0"` → `"1.2.0"`
- セマンティックバージョニング比較: `tuple(int(x) for x in ver.split("."))`

## アセット選択ルール

| `sys.platform` | アセット名パターン |
|---------------|-----------------|
| `"win32"` | `LoopPlayer-Setup-{ver}.exe` |
| `"darwin"` | `LoopPlayer-{ver}.dmg` |
| その他 | ダウンロード不可（通知のみ） |

アセットが見つからない場合はダウンロードをスキップする（クラッシュしない）。

## エラー処理

| 状態 | 処理 |
|------|------|
| HTTP 4xx / 5xx | `check_failed` シグナルを発行 |
| タイムアウト（5秒超過） | `check_failed` シグナルを発行 |
| JSON パースエラー | `check_failed` シグナルを発行 |
| ネットワーク到達不能 | `check_failed` シグナルを発行 |

起動時チェックの場合: `check_failed` は無視（サイレント）。
手動確認の場合: `check_failed` を受けてエラーダイアログを表示。
