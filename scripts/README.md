# PiCalendar のインストールと systemd 運用

このディレクトリには Raspberry Pi 向けのインストール、systemd サービス、診断スクリプトがあります。標準 UI は Field Notes ダッシュボードです。旧 classic 表示では壁紙レンダラーを使います。

## 主なファイル

| ファイル | 用途 |
| --- | --- |
| `install.sh` | 現行 checkout では systemd unit の設置先を誤って生成するため、導入には使わない |
| `install_service.sh` | systemd unit を登録して自動起動を有効化 |
| `picalender.service` | `install_service.sh` が使う unit テンプレート |
| `start_service.sh` | 上記テンプレートから起動し、仮想環境を選択して `main.py` を実行 |
| `uninstall_service.sh` | systemd サービスを削除 |
| `diagnose.sh` | 診断情報を収集 |
| `check_system.sh` | システム要件を確認 |
| `setup_display.sh` | ディスプレイ設定を補助 |

## 手動セットアップ

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
```

現在の `scripts/install.sh` は `INSTALL_DIR` をスクリプト配置先の `scripts/` として扱い、誤った unit path を生成するため、導入に使わないでください。Python の依存関係は `venv` に事前インストールします。

## 表示確認

既にサービスが起動している環境では、前面起動と二重にならないように先に停止します。

```bash
sudo systemctl stop picalender
cd ~/picalender
venv/bin/python main.py
```

終了するときは `Ctrl+C` を押します。

## install_service.sh を使う場合

通常ユーザーとしてプロジェクトルートから実行します。

```bash
cd ~/picalender
sudo ./scripts/install_service.sh
sudo systemctl cat picalender
```

このスクリプトは unit を登録して自動起動を有効にしますが、その場ではサービスを開始しません。テンプレートは `User=zabaglione`、`Group=zabaglione`、`/home/zabaglione/picalender` を含み、インストーラーの置換処理は `pi` と `/home/pi/picalender` のみを対象にします。別ユーザーでは値が残ることがあるため、起動前に `systemctl cat` で確認し、必要なら `sudo systemctl edit --full picalender` で `User`、`Group`、`WorkingDirectory`、`PYTHONPATH`、`ExecStart` を修正してください。詳細は [複数ユーザー設定](../docs/guides/MULTI_USER_SETUP.md) を参照してください。

unit のユーザーとパスを確認・修正した後に systemd を再読み込みし、サービスを開始します。

```bash
sudo systemctl daemon-reload
sudo systemctl start picalender
sudo systemctl status picalender --no-pager
sudo journalctl -u picalender -f
```

## サービス操作

```bash
sudo systemctl start picalender
sudo systemctl stop picalender
sudo systemctl restart picalender
sudo systemctl status picalender --no-pager
sudo systemctl enable picalender
sudo systemctl disable picalender
```

このテンプレート経由では start_service.sh が main.py の標準出力とエラーを logs/service.log に書き、journal には unit や起動前のエラーが記録されます。ExecStart が Python を直接起動する unit では、アプリの出力も journal に記録されます。

```bash
sudo journalctl -u picalender -n 100 --no-pager
sudo journalctl -u picalender -f
tail -f ~/picalender/logs/service.log
```

unit を編集した場合は、再読み込みしてから再起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl restart picalender
```

## 診断

```bash
cd ~/picalender
./scripts/diagnose.sh
./scripts/check_system.sh
```

ディスプレイ設定や起動の問題は [トラブルシューティング](../docs/guides/TROUBLESHOOTING.md) を参照してください。
