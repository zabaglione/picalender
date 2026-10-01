# PiCalendar インストールガイド

## 現行版の前提

標準表示は Field Notes ダッシュボードです。旧 classic 表示も選べますが、壁紙スライドショーは classic 表示用です。Raspberry Pi OS、Python 3.11 以上、接続するディスプレイを用意してください。天気情報にはネットワーク接続が必要です。

## インストール

Raspberry Pi 上で通常ユーザーとして実行し、プロジェクトを `~/picalender` に配置します。

```bash
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv python3-pygame python3-yaml python3-requests python3-pillow fonts-noto-cjk git
cd ~
git clone https://github.com/zabaglione/picalender.git
cd ~/picalender
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
cp -n settings.example.yaml settings.yaml
nano settings.yaml
```

`scripts/install.sh` は現在、サービスの `INSTALL_DIR` をスクリプト配置先の `scripts/` として扱い、誤った unit パスを生成します。この手順では使わず、上記の手動セットアップを行ってください。

前面起動で表示を確認します。既にサービスが登録・起動済みの環境では、二重起動を避けるため先にサービスを停止してください。

```bash
sudo systemctl stop picalender
cd ~/picalender
venv/bin/python main.py
```

終了するときは `Ctrl+C` を押します。標準の Field Notes 表示を旧 classic 表示に変える場合は、設定の `ui.style` を `classic` にします。

```yaml
ui:
  style: classic
```

## systemd サービス

表示確認後、通常ユーザーとしてプロジェクトルートからサービスを登録します。

```bash
cd ~/picalender
sudo ./scripts/install_service.sh
sudo systemctl cat picalender
```

このスクリプトは unit を登録して自動起動を有効にしますが、その場では起動しません。生成された unit の `User`、`Group`、`WorkingDirectory`、`PYTHONPATH`、`ExecStart` が実際のユーザーと設置先に合うことを確認してください。テンプレートには固定ユーザー名があり、インストーラーの置換処理が別ユーザーに対応しない場合があります。修正方法は [複数ユーザー設定](MULTI_USER_SETUP.md) を参照してください。

必要箇所を修正した場合は systemd を再読み込みしてから起動します。未修正の場合も、unit の内容を確認してから起動してください。

```bash
sudo systemctl daemon-reload
sudo systemctl start picalender
sudo systemctl status picalender --no-pager
sudo journalctl -u picalender -f
```

## ログ

この install_service.sh 経由の unit は start_service.sh が main.py の標準出力とエラーを logs/service.log に書きます。journal は unit や起動前のエラー確認に使います。ExecStart が Python を直接起動する unit では、アプリの出力も journal に記録されます。

```bash
sudo journalctl -u picalender -b -n 100 --no-pager
tail -n 100 ~/picalender/logs/service.log
```

## 関連ドキュメント

- [プロジェクト README](../../README.md)
- [クイックスタート](QUICK_START.md)
- [設定ガイド](SETTINGS_GUIDE.md)
- [壁紙の転送](TRANSFER_FILES.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
