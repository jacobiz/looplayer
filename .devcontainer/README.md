# Devcontainer セットアップメモ

## 前提条件

- Windows 11 + WSL2 (WSLg 対応)
- Docker Desktop (WSL2 バックエンド)
- VSCode + Dev Containers 拡張機能

## 起動方法

1. VSCode でプロジェクトフォルダを開く
2. コマンドパレット → `Dev Containers: Reopen in Container`

## GUI 表示について

WSL2 + WSLg 環境では DISPLAY 設定が自動的に引き継がれます。
GUI が表示されない場合は WSL 側で以下を確認してください:

```bash
echo $DISPLAY        # :0 などが表示されればOK
echo $WAYLAND_DISPLAY
```

## 実行

```bash
python main.py
```
