# PiCalendar トラブルシューティング

コマンドは Raspberry Pi のプロジェクトルート `~/picalender` で実行します。

## 画面が表示されない

サービス状態と起動ログを確認します。

```bash
sudo systemctl status picalender --no-pager
sudo journalctl -u picalender -b -n 100 --no-pager
```

`scripts/install_service.sh` で登録した unit では、補助ログも確認できます。 この unit ではアプリの出力は service.log、unit や起動前のエラーは journal に記録されます。

```bash
test -f ~/picalender/logs/service.log && tail -n 100 ~/picalender/logs/service.log
```

サービス定義の実行ユーザー、作業ディレクトリ、起動スクリプト、SDL 環境変数が現在の設置先に合うか確認します。

```bash
sudo systemctl cat picalender
ls -l /dev/fb0 /dev/dri/card0
```

DRM デバイスへの権限がない場合は、サービス実行ユーザーを確認して `video` グループへの追加を検討します。その後サービスを再起動します。

```bash
sudo systemctl show -p User -p Group picalender
sudo usermod -aG video USER
sudo systemctl restart picalender
```

`USER` はサービスの実行ユーザーに置き換えます。ユーザーやパスが違う場合の修正方法は [複数ユーザー設定](MULTI_USER_SETUP.md) を参照してください。

## Python モジュールが見つからない

システム Python へ直接 pip インストールせず、プロジェクトの仮想環境に依存関係を入れます。

```bash
cd ~/picalender
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -c "import pygame, yaml, requests"
sudo systemctl restart picalender
```

## 設定エラー

設定ファイルの YAML 構文を確認します。

```bash
cd ~/picalender
venv/bin/python -c "import yaml; yaml.safe_load(open('settings.yaml', encoding='utf-8'))"
```

設定を変更した後はサービスを再起動します。

```bash
sudo systemctl restart picalender
```

## Field Notes と classic の表示

標準設定は `ui.style: field_notes` です。`ui.style: classic` は旧レンダラーを使い、壁紙を表示できます。表示が意図と異なる場合は `settings.yaml` の `ui.style` を確認してください。

## 天気情報が更新されない

ネットワーク接続と DNS 解決を確認します。天気情報にはインターネット接続が必要です。サービスログに接続エラーがないか確認してください。

```bash
getent hosts api.open-meteo.com
sudo journalctl -u picalender -b -n 100 --no-pager
```

## 診断情報

付属の診断スクリプトをプロジェクトルートから実行できます。

```bash
cd ~/picalender
./scripts/diagnose.sh
```

問い合わせ時は Raspberry Pi の機種、OS 情報、Python バージョン、エラー全文を添えてください。設定ファイルを共有する場合は個人情報を除いてください。

```bash
cat /etc/os-release
python3 --version
sudo journalctl -u picalender -b -n 100 --no-pager
```
