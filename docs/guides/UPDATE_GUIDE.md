# 接続・更新・復旧

## Raspberry Piへの接続

OSセットアップ時に指定したユーザー名とホスト名を使用する。

```bash
ssh <user>@<hostname>.local
```

IPアドレスはDHCPで変わる場合がある。通常のアプリ更新ではSDカードを抜かず、
SSHでPiに接続し、アプリのファイルを更新してサービスを再起動する。

```bash
cd ~/picalender
systemctl status picalender --no-pager
tail -n 40 logs/service.log
```

## Gitから更新する場合

先に実機の変更を確認し、設定・壁紙・変更したソースをバックアップする。
未コミットの修正があれば退避または統合し、上書きしない。

```bash
cd ~/picalender
git status --short
git pull --ff-only
venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart picalender
```

Field Notesは `astronomy-engine==2.1.19` が必要。
既存環境への今回の導入では、このパッケージだけを追加した。

旧 `quick_restart.sh` はプロセスを直接起動するため、systemd管理の環境では
上記の `systemctl restart` を使用する。

## 検証済みファイルを転送して更新する場合

公開前の版は、転送対象のファイル一覧とSHA-256を持つ `deploy_manifest.json` を
作り、別ディレクトリで検証してから反映できる。形式は次のとおり。

```json
{
  "release": "release-name",
  "files": {
    "main.py": "<sha256-of-main.py>"
  }
}
```

検証ディレクトリには、実機のアプリソースのコピーに更新ファイルを重ね、
必要な依存関係・設定を用意する。プレビュー・月相照合・メインアプリの起動と
終了を確認してから、Pi上で次を実行する。

```bash
python3 scripts/apply_staged_update.py --stage <candidate-directory>
```

スクリプトはマニフェストの対象だけを更新し、`settings.yaml`、壁紙、キャッシュ、
仮想環境、Git情報を保護する。旧ファイルを `~/picalender-backups/` に保存後、
サービスを停止して置換・再起動する。プロセスが安定して稼働しない場合は旧ファイルへ戻す。
表示内容の確認は別途行う。

## 元に戻す

上記のスクリプトが出力したバックアップディレクトリを指定する。

```bash
python3 <backup-directory>/restore.py --rollback <backup-directory>
```

更新前に存在した対象ファイルを復元し、今回追加した対象ファイルを取り除いて
サービスを再起動する。設定・壁紙は保持する。追加した依存パッケージは仮想環境に残る。

## 描画の確認

Field Notesを含む新版はSIGUSR1で次の描画ループに画面を保存する。

```bash
sudo systemctl kill --kill-who=main --signal=USR1 picalender.service
ls -l ~/picalender/logs/display.png
```

旧版はこのシグナルに対応していないため、旧版へ戻した後は実行しない。

ローカルでのプレビュー：

```bash
venv/bin/python scripts/render_preview.py
venv/bin/python scripts/render_preview.py --offline --at 2026-08-31T23:59:58+09:00
```

`ui.style: field_notes` が新しい既定デザイン。旧レイアウトが必要な場合は
`settings.yaml` の `ui.style` を `classic` にしてサービスを再起動する。
月齢と六曜の修正は両方のデザインに適用される。
