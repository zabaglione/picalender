# ドキュメント一覧

2026-10-01に現行の起動経路と過去資料を区分しました。

## 現在の利用・保守

- [現行実装とAPI](current-implementation.md)
- [インストール](guides/INSTALL_GUIDE.md)、[クイックスタート](guides/QUICK_START.md)
- [設定](guides/SETTINGS_GUIDE.md)、[設定対応表](guides/SETTINGS_STATUS.md)、[機能一覧](guides/FEATURES.md)
- [運用マニュアル](OPERATION_MANUAL.md)、[接続・更新・復旧](guides/UPDATE_GUIDE.md)
- [月別背景](monthly-wafu-themes.md)、[テーマの区分](guides/THEME_GUIDE.md)、[日替わり画像](guides/DAILY_ARTWORK.md)
- [天気](guides/WEATHER_SETUP.md)、[旧画面の壁紙](guides/WALLPAPER_GUIDE.md)
- [今回の監査結果と未解決項目](documentation-audit-2026-10-01.md)

## 過去の設計・実装記録

`spec/`、`design/`、`tasks/`、`implementation/`、`tdd/`、`TASK-*`、旧API資料、性能最適化資料は開発時の計画・試験記録です。未チェックの項目や過去の成功数を、現在のアプリの進捗・受け入れ状態として読み替えないでください。TASK-402はWBSではYahoo天気、別資料ではキャラクター拡張を指すため、番号だけで対応づけできません。

日付付きの月相・画面情報・再設計・月別背景の検証は、その日のコードと環境に対する証拠として残します。実機の現在の状態は別途確認が必要です。旧 `X11_SETUP.md` はデスクトップ環境の補助資料であり、標準KMSDRM運用の入口は上記の導入・更新ガイドです。
