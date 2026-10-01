# PiCalendar クイックスタート

## インストール

Raspberry Pi 上で通常ユーザーとして実行します。プロジェクトを `~/picalender` に置き、仮想環境へ依存関係をインストールします。

```bash
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv python3-pygame python3-yaml python3-requests python3-pillow fonts-noto-cjk git
cd ~
git clone https://github.com/zabaglione/picalender.git
cd ~/picalender
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp -n settings.example.yaml settings.yaml
nano settings.yaml
```

現在の `scripts/install.sh` は systemd unit の設置先を誤って生成するため、この導入手順では使いません。詳細は [インストールガイド](INSTALL_GUIDE.md) を参照してください。

表示場所を変える場合は、settings.yaml の天気設定にある緯度と経度を変更してください。

## 表示確認

既にサービスが起動している環境では、二重起動を避けるため先に停止します。

```bash
sudo systemctl stop picalender
cd ~/picalender
venv/bin/python main.py
```

終了するときは `Ctrl+C` を押します。標準は Field Notes ダッシュボードです。旧 classic 表示を使う場合は `settings.yaml` の `ui.style` を `classic` にします。

## systemd で起動

プロジェクトルートからサービスを登録し、unit のユーザーとパスを確認します。修正が必要な場合は [複数ユーザー設定](MULTI_USER_SETUP.md) の手順に従ってください。

```bash
cd ~/picalender
sudo ./scripts/install_service.sh
sudo systemctl cat picalender
sudo systemctl start picalender
sudo systemctl status picalender --no-pager
```

install_service.sh は自動起動を有効にしますが、登録時点では開始しません。アプリの標準出力とエラーは logs/service.log に記録され、journal には unit や起動前のエラーが記録されます。
