# 複数ユーザー環境でのセットアップ

PiCalendar は標準の `pi` ユーザー以外でも動作します。PiCalendar の実行ユーザーでログインし、そのユーザーのホームディレクトリに `picalender` を配置します。

```bash
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv python3-pygame python3-yaml python3-requests python3-pillow fonts-noto-cjk git
cd ~
git clone https://github.com/zabaglione/picalender.git
cd ~/picalender
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp -n settings.example.yaml settings.yaml
```

現在の `scripts/install.sh` は `INSTALL_DIR` をスクリプト配置先の `scripts/` として扱い、誤った service path を生成します。使用せず、上記の手動手順で環境を準備してください。

## 表示確認

既に PiCalendar のサービスが起動している場合は、前面起動と二重にならないよう先に停止します。

```bash
sudo systemctl stop picalender
cd ~/picalender
venv/bin/python main.py
```

終了するときは `Ctrl+C` を押します。

## systemd サービスの登録

通常ユーザーとしてプロジェクトルートから実行します。

```bash
cd ~/picalender
sudo ./scripts/install_service.sh
sudo systemctl cat picalender
```

このスクリプトは `sudo` 実行時に `SUDO_USER` を読み取り、アプリケーションが `~/picalender` にある前提で unit を登録して自動起動を有効にします。その場ではサービスを開始しません。

現在の `scripts/picalender.service` テンプレートは `zabaglione` とそのホームパスを含みますが、インストーラーの置換処理は `pi` と `/home/pi/picalender` だけを置き換えます。別ユーザーではテンプレート値が残ることがあるため、起動前に生成済み unit を確認してください。

```bash
sudo systemctl cat picalender
```

ユーザー名または設置先が違う場合は unit を編集します。

```bash
sudo systemctl edit --full picalender
```

少なくとも次の値を実際の環境に合わせます。

```ini
User=USERNAME
Group=USERNAME
WorkingDirectory=/home/USERNAME/picalender
Environment="PYTHONPATH=/home/USERNAME/picalender:/home/USERNAME/picalender/src:/home/USERNAME/picalender/src/renderers"
ExecStart=/home/USERNAME/picalender/scripts/start_service.sh
```

`USERNAME` と `/home/USERNAME` は実際のユーザー名とホームディレクトリに置き換えます。編集後に systemd を再読み込みしてから起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl start picalender
sudo systemctl status picalender --no-pager
```

テンプレートの実行ユーザーに DRM デバイス権限がない場合は、そのユーザーを `video` グループに追加してからサービスを再起動します。

```bash
sudo usermod -aG video USERNAME
sudo systemctl restart picalender
```

## ログ

この unit テンプレートではアプリの標準出力とエラーは logs/service.log に記録されます。journal は unit や起動前のエラー確認に使います。

```bash
sudo journalctl -u picalender -f
tail -f ~/picalender/logs/service.log
sudo systemctl cat picalender
```

同じ Pi 上で複数ユーザーが同時に画面を占有して起動する運用は避けてください。
