# 文書・Issues監査（2026-10-01）

## 対象と結果

ローカルの現行 `main.py`、使用中のレンダラー、設定サンプル、サービス・同期・プレビューのスクリプトを、README・利用ガイド・運用・設計資料と照合しました。アプリコード、非公開設定、キャッシュ、実機サービスは変更していません。

GitHub `zabaglione/picalender` の全状態のIssuesと未完了PRを確認した時点では、いずれも0件でした。既存Issueの古い記述やクローズ状態を直す対象はありません。文書で見つかった未解決のコード不整合を [Issue #1（サービス導入）](https://github.com/zabaglione/picalender/issues/1)、[Issue #2（旧テーマ管理）](https://github.com/zabaglione/picalender/issues/2) として登録しました。以下の2件を追跡します。

| 問題 | 根拠・再現 | 当面の扱い |
| --- | --- | --- |
| サービス導入のユーザー・パス不整合 | `scripts/install_service.sh` は `User=pi` / `Group=pi` / `/home/pi/picalender` を置換するが、`scripts/picalender.service` の実値は異なる。別の `install.sh` は `INSTALL_DIR` を `scripts/` にして不在のPython・mainパスをunitへ生成する | 手動導入を使用し、登録後に `systemctl cat` で確認し、実際のユーザーとパスへ修正してから開始 |
| 旧テーマ管理のパス不一致 | `docs/theme_manager.py` が `docs/themes/` / `docs/settings.yaml` を参照。ルートの `themes/` にプリセットがあるのに `venv/bin/python docs/theme_manager.py list` は `No themes found` | 壊れた適用コマンドの案内を除去。現行の月別背景は自動切替、旧画面は設定を直接編集 |

## 修正した文書

- README・機能一覧：現在の手描き月別背景、日替わり生成入力、六曜・天文情報、表示制約を反映。存在しないMakefileのコマンドと根拠のない性能・環境保証を除去。
- 設定サンプル：未使用だった `background.*` を旧画面で有効な `wallpaper.*` に置き換え、タイムゾーンと未使用項目の説明を更新。既存の非公開 `settings.yaml` は保持。
- 設定・テーマ・天気・壁紙：Field Notesとclassicを区分。現在の起動経路で使わない設定、タイムゾーン、キャッシュの違いを明記。
- 導入・再起動・トラブル対応・転送：削除済みエントリーポイント、固定IP、実在しない参照、サービス運用時の再起動を訂正。
- 現行実装と文書一覧を追加。古い仕様・API・WBS・性能目標は過去資料と明記し、本文と過去の試験記録を保持。

TASK-402は資料ごとにYahooプロバイダ／キャラクター拡張を指します。古いタスク番号やチェック欄だけを現在の実装進捗として扱いません。独立モジュールが存在しても `main.py` で使用されているとは限りません。

## 今回の確認

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy venv/bin/python -m pytest -q \
  tests/test_astronomy_accuracy.py tests/test_dashboard_weather.py \
  tests/test_monthly_theme.py tests/test_daily_art.py tests/test_staged_update.py
venv/bin/python scripts/render_preview.py --offline \
  --output output/documentation-audit-2026-10-01/preview.png
```

対象テスト181件が通過し、オフラインプレビューの出力に成功し、10月の背景・暦・月相と欠測表示を目視確認しました。既存の全テストやネットワーク取得、他ユーザーでのサービス導入、今回のPi実機・物理パネルは未確認です。日付付き資料にある過去の実機検証を、今回の検証結果とは扱いません。

変更Markdownの相対リンク、設定サンプルのYAML構文、`git diff --check` を確認しました。Astraレビューの導入経路、Git導入順序、ログ保存先、日時APIの検索開始時刻、別寸法への拡縮の指摘を反映し、該当箇所を再確認しました。実機への反映は今回の文書監査には含めていません。
