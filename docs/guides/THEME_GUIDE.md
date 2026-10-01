# テーマ機能ガイド

## Field Notesの月替わり背景

標準画面は `weather.timezone`（既定 `Asia/Tokyo`）の新暦の月に従い、12枚の手描き・和紙調背景と配色を自動で切り替えます。表示項目、配置、日替わり画像は維持します。テーマ適用コマンドは不要です。

背景PNGは `assets/field_notes/monthly/` に同梱しています。月別の説明、全月プレビュー、過去の検証は[月替わりの和風テーマ](../monthly-wafu-themes.md)を参照してください。

```bash
venv/bin/python scripts/render_preview.py --offline --all-months \
  --output output/monthly/preview.png
```

## 旧プリセットの状態

`themes/` の `default`、`compact`、`night`、`colorful`、`minimal` は旧画面用の設定資料です。Field Notesの背景・フォント・配色を変更するものではありません。

旧管理ツールは `docs/theme_manager.py` にありますが、自身の所在を基準に `docs/themes/` と `docs/settings.yaml` を探します。実際の対象はプロジェクト直下にあるため、そのままでは一覧表示・適用が正しく動きません。従来の `python3 theme_manager.py apply night` は削除済みのルートファイルを指します。

現在は[設定ガイド](SETTINGS_GUIDE.md)に従って `settings.yaml` を編集し、旧画面が必要な場合は `ui.style: classic` を指定してください。プリセットの全項目が現行の旧画面に適用されるとは限らないため、[設定対応表](SETTINGS_STATUS.md)で確認します。
