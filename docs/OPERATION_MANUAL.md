# PiCalendar 運用マニュアル

2026-10-01に現在の `main.py` とサービス起動経路に合わせて整理しました。標準画面はField Notes、旧画面はclassicです。[設定対応表](guides/SETTINGS_STATUS.md)で使える項目を確認します。

## 起動と確認

導入は[インストールガイド](guides/INSTALL_GUIDE.md)に従います。同梱サービスにはユーザー／ホームパスの固定値が残るため、開始前に `systemctl cat picalender` で実環境との一致を確認してください。

```bash
cd ~/picalender
sudo systemctl status picalender --no-pager
sudo journalctl -u picalender --since today
tail -n 40 logs/service.log
```

`install_service.sh` のテンプレート版は `scripts/start_service.sh` 経由で仮想環境の `main.py` を起動し、アプリの標準出力・標準エラーを `logs/service.log` に追記します。unitや起動前のエラーはjournalで確認します。旧 `install.sh` のunit生成は実在しない `scripts/venv` と `scripts/main.py` を指す不整合があります。新規導入には使用せず、導入ガイドの手動セットアップを使います。直接Pythonを起動するunitでは、ログは主にjournalで確認します。実際の起動経路は `systemctl cat picalender` で確認してください。アプリ本体の高度なLogManager設定とは別です。

## 設定変更

```bash
cd ~/picalender
cp settings.yaml settings.yaml.backup
nano settings.yaml
venv/bin/python -c "import yaml; yaml.safe_load(open('settings.yaml')); print('YAML syntax OK')"
sudo systemctl restart picalender
```

構文確認後、画面とログを確認します。標準画面の地点・時刻は `weather.location` と `weather.timezone`、表示項目は `calendar`、日替わり画像は `daily_art` で設定します。1024×600基準の背景・フォント・配置を使い、別寸法には画面全体を拡縮します。

## 更新と復旧

[接続・更新・復旧](guides/UPDATE_GUIDE.md)のGit更新またはマニフェスト付き更新を使用します。更新前に作業状態、設定、壁紙、変更ソースを保存します。通常はSSHで更新し、SDカード書き直しは不要です。

```bash
ssh <user>@<hostname>.local
cd ~/picalender
git status --short
git pull --ff-only
venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart picalender
```

サービス管理中は `quick_restart.sh` や `pkill` による別プロセス起動を避け、`systemctl` で操作します。

## 描画と通信障害の確認

```bash
sudo systemctl kill --kill-who=main --signal=USR1 picalender.service
ls -l ~/picalender/logs/display.png
```

これは稼働中Pygame画面の取得です。物理パネルの撮影や接続状態の確認とは異なります。

時計・暦・天文計算・月別背景はオフラインで使用します。標準画面の天気キャッシュは `cache/field_notes_weather.json`。失敗時は直前データを保持し、古い取得時刻・欠測を区別します。日替わり画像は `cache/daily_art/current.png` / `current.json` で、取得失敗時は以前の画像を保持します。[日替わりイラスト運用](guides/DAILY_ARTWORK.md)

## 性能と証拠

`screen.fps` で描画頻度を調整します。サンプルは5fpsです。`performance.default_quality` やキャッシュ上限指定は現行 `main.py` では使用しません。CPU・メモリの値は機器と測定条件を添えて記録し、過去の目標値を実測値として扱いません。

検証履歴は[月替わりテーマ](monthly-wafu-themes.md)と[初回再設計の記録](redesign-validation-2026-09-18.md)、未解決項目は[文書監査](documentation-audit-2026-10-01.md)を参照してください。
