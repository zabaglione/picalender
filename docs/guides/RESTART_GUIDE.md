# PiCalendar 更新・再起動ガイド

systemd に登録した PiCalendar は、SSH 接続後に Git で更新し、systemd から再起動します。以下の `USER` は Raspberry Pi のログインユーザー名に置き換えてください。

```bash
ssh USER@raspberrypi.local
cd ~/picalender
git pull --ff-only
sudo systemctl restart picalender
sudo systemctl status picalender --no-pager
```

更新で `requirements.txt` が変わった場合は、再起動前に仮想環境の依存関係を更新します。

```bash
cd ~/picalender
venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart picalender
```

## サービス操作

```bash
sudo systemctl start picalender
sudo systemctl stop picalender
sudo systemctl restart picalender
sudo systemctl status picalender --no-pager
```

この unit テンプレートではアプリの標準出力とエラーは logs/service.log に記録されます。journal は unit や起動前のエラー確認に使います。ExecStart が Python を直接起動する unit では、アプリの出力も journal に記録されます。

```bash
sudo journalctl -u picalender -f
sudo journalctl -u picalender -b -n 100 --no-pager
tail -f ~/picalender/logs/service.log
```

自動起動の登録状態を確認し、必要なら有効化します。

```bash
sudo systemctl is-enabled picalender
sudo systemctl enable picalender
```

サービス登録がない環境では [インストールガイド](INSTALL_GUIDE.md) を参照してください。サービス登録後に起動しない場合は [トラブルシューティング](TROUBLESHOOTING.md) を参照してください。
