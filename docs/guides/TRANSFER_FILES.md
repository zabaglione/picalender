# ファイル転送ガイド

この手順は旧 classic 表示の壁紙用です。標準の Field Notes ダッシュボードでは `wallpapers/` の画像を表示しません。

以下の `USER` は Raspberry Pi のログインユーザー名に置き換えます。接続先は mDNS の `raspberrypi.local` を例にしています。名前解決できない環境では、実際のホスト名または IP アドレスを使ってください。

## SCP で転送

プロジェクトの `wallpapers` ディレクトリへ単一ファイルまたは複数ファイルを転送します。

```bash
scp image.jpg USER@raspberrypi.local:~/picalender/wallpapers/
scp ./*.jpg USER@raspberrypi.local:~/picalender/wallpapers/
```

転送先ディレクトリがない場合は先に作成します。

```bash
ssh USER@raspberrypi.local "mkdir -p ~/picalender/wallpapers"
```

PC のデスクトップから転送する場合の例です。

```bash
scp "$HOME/Desktop/wallpapers/"*.jpg USER@raspberrypi.local:~/picalender/wallpapers/
```

## 転送の確認と反映

```bash
ssh USER@raspberrypi.local "ls -la ~/picalender/wallpapers"
ssh USER@raspberrypi.local "sudo systemctl restart picalender"
```

classic 表示を使っているか、`settings.yaml` の `ui.style` が `classic` であることも確認してください。PiCalendar が起動しない場合は [トラブルシューティング](TROUBLESHOOTING.md) を参照してください。
