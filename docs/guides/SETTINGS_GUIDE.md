# PiCalendar 設定ガイド

設定はプロジェクト直下の `settings.yaml` から起動時に読み込みます。初回だけ `cp settings.example.yaml settings.yaml` を実行し、既存設定は上書きしないでください。

## 標準画面の設定

```yaml
ui:
  style: field_notes
screen:
  width: 1024
  height: 600
  fps: 5
  fullscreen: true
weather:
  timezone: Asia/Tokyo
  location:
    lat: 35.681236
    lon: 139.767125
  refresh_sec: 1800
calendar:
  first_weekday: SUNDAY
  holidays_enabled: true
  holidays_country: JP
  show_holiday_names: true
  rokuyou_enabled: true
  show_rokuyou_names: true
  moon_phase_enabled: true
```

緯度・経度は設置地点へ変更します。`weather.timezone` は時刻・月別背景の切替にも使用します。月相の主要名称は天文計算側でJSTの現象日に基づきます。

標準画面は1024×600基準の固定配置で、別寸法では縦横比を保って全体を拡縮します。別寸法の実機確認範囲は検証記録で区別します。フォント・文字サイズ・配置・月別配色は実装で固定しています。旧画面用の設定では変更できません。背景は同梱の12枚を自動切替するため、個別テーマの適用操作は不要です。

日替わり画像の有効化と別サーバーの設定は[DAILY_ARTWORK.md](DAILY_ARTWORK.md)を参照してください。ローカルの設定・SSH情報はGitに含めません。

## 旧画面の設定

```yaml
ui:
  style: classic
  clock_font_px: 130
  date_font_px: 36
  cal_font_px: 28
  weather_font_px: 22
wallpaper:
  rotation_seconds: 300
  fit_mode: fill
```

旧画面は `wallpapers/` を使用し、60秒ごとに追加画像を検出します。`rotation_seconds: 0` で切替を止められます。`background.dir` / `mode` / `rescan_sec` は現在の起動経路では使用しません。旧画面のカレンダーは日曜始まり固定です。

`character.*`、自動品質調整、任意のキャッシュ上限、ログレベル指定は、現在の `main.py` に接続されていません。対応範囲は[SETTINGS_STATUS.md](SETTINGS_STATUS.md)で確認できます。

## 検証・反映・復元

```bash
cd ~/picalender
cp settings.yaml settings.yaml.backup
nano settings.yaml
venv/bin/python -c "import yaml; yaml.safe_load(open('settings.yaml')); print('YAML syntax OK')"
sudo systemctl restart picalender
sudo systemctl status picalender --no-pager
```

構文確認は設定値の意味や画面表示まで保証しません。サービスを使用しない場合は手動起動を終了して `venv/bin/python main.py` で起動し直します。

復元する場合は `cp settings.yaml.backup settings.yaml` の後、同じ方法で再起動してください。サンプルへの置換は地点や日替わり画像の設定も初期化するため、復元にはバックアップを使います。
