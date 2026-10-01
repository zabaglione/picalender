# SSHとCodexによる日替わりイラスト

Field Notesの左下を毎日異なるイラストにするオプション。
PiがSSHで自宅サーバーに依頼し、サーバーが `codex exec` の組み込み画像生成で
PNGを作成する。同じ日付は保存済みの画像を再利用する。
画像の生成にはCodexの利用枠とクラウド通信を使用する。
画像の保存とPiへの転送は自宅の機器間で行う。APIキー方式へ自動で切り替えない。

## 保存先と動作

- サーバー：`~/picalender-artwork/cache/YYYY-MM-DD/` に原画像 `source.png`、
  `prompt.txt`、生成ログ、メタデータを残す。過去の日付を自動削除しない。
- Pi：`~/picalender/cache/daily_art/current.png` に800×450の表示用PNGを1枚だけ保持する。
  `current.json` は日付・チェックサム。転送中の一時画像は処理後に取り除く。
- Piのタイマーが15分ごとに確認する。既定では日本時間の朝5時に対象日が切り替わる。
  同日の画像を保持していればSSH接続も生成も行わない。
- サーバーの同日キャッシュは天気やテーマ設定を変えても再生成しない。
  テーマは最初の生成に使われる。過去画像はそのまま保管する。
- 失敗時は前の画像を維持する。生成は日付ごとに最大2回の試行、失敗後は30分間隔を空ける。
  SSH・転送の再試行で毎回Codexを呼ぶことはない。
- 生成処理は画面表示と別のサービス。画像の差し替えは5秒間隔で検知し、時計・六曜・月齢は継続表示する。
- 日付別テーマを最優先し、該当日の記念日・季節行事、日本の祝日、月ごとの季節描写、森の場面の順に使う。
- 天気はPiの `cache/field_notes_weather.json` にある取得2時間以内・設定地点一致・対象日一致の予報だけを使う。
  生成時点の取得時刻と、天気カテゴリ、最高・最低気温（摂氏）、降水確率を渡す。
  条件を満たさない場合は `unknown` とし、数値を補わず天候を断定しない。新しい天気取得は行わない。
- 確認済みの固定日イベントは [daily_events.json](../../assets/field_notes/daily_events.json) に収録している。
  七草、ひな祭り、端午、七夕、重陽、鏡開き、小正月、大晦日、コーヒーの日の対象日だけ送る。
  365日を網羅する記念日一覧ではなく、可変日（節分、冬至、十五夜など）は固定日扱いしない。
  対象日に登録イベントがなくても、月ごとの季節描写を使い、記念日名を捏造しない。
- 任意の追加イベントは `daily_art.observances` に登録できる。キーは引用符付きの `MM-DD` または
  `YYYY-MM-DD`、値は `name` と `visual_hint` を持つオブジェクト。年指定が最優先、続いて毎年指定、
  最後に確認済みカタログの順で選ぶ。同じ日のカタログイベントを設定値で置き換えられる。

## サーバーの準備

Piの公開鍵をサーバーの接続ユーザーに登録し、Piから非対話SSH接続が通ることを確認する。
ホスト鍵の確認は省略しない。秘密鍵とCodexの認証情報は、それぞれの機器で保持する。

サーバーでCodexにログインし、組み込み画像生成が使えることを確認する。
`scripts/serve_daily_art.py` をサーバーの `~/picalender-artwork/` にコピーする。
このスクリプトの依存はPython標準ライブラリだけ。

同じディレクトリに、実環境に合わせた非公開の `config.json` を作る。

```json
{
  "codex_binary": "/home/USER/.nvm/versions/node/VERSION/bin/codex",
  "timeout_sec": 900,
  "max_attempts_per_day": 2,
  "retry_sec": 1800
}
```

`codex_binary` には、実際にログインして利用しているCodexの絶対パスを指定する。
nvm環境でも無人実行できるよう、そのエントリーポイントのディレクトリをPATHに加えて実行する。
作業先は日付ごとの専用ディレクトリ、Codexの権限は `workspace-write`。
生成に失敗した場合は、その日付の `stderr.log`、`events.jsonl`、`result.txt` を確認する。

## Piの設定

Git管理外の `settings.yaml` に追加する。

```yaml
daily_art:
  enabled: true
  refresh_hour: 5
  ssh_host: "USER@SERVER.local"
  remote_script: "picalender-artwork/serve_daily_art.py"
  # identity_file: "~/.ssh/id_ed25519"
  themes:
    "2026-12-25": "A quiet winter celebration in the forest"
  observances:
    "10-01":
      name: "Neighborhood Coffee Day"
      visual_hint: "Share a steaming cup at a small woodland table."
    "2026-10-02":
      name: "One-time Garden Day"
      visual_hint: "Arrange a few autumn leaves beside a watering can."
```

専用のSSH鍵を指定したい場合だけ `identity_file` を設定する。
IPアドレス、ユーザー名、鍵のパス、サーバーの `config.json` は公開リポジトリに含めない。
生成用のプロンプトは `scripts/serve_daily_art.py` の `build_prompt()` にある。
同じ日付の画像はサーバーで再利用するため、日付別テーマやイベント設定を変更しても再生成しない。

初回取得と表示の有効化：

```bash
cd ~/picalender
venv/bin/python scripts/sync_daily_art.py
sudo systemctl restart picalender
```

以後の画像更新にアプリの再起動は不要。

## 自動更新

`/home/USER/picalender` に設置したPi向けのsystemdテンプレートを同梱している。
以下の `USER` をPiの実際のユーザー名に置き換える。
別の配置先を使う場合は、serviceの作業ディレクトリとPythonのパスを変更する。

```bash
sudo install -m 644 scripts/picalender-artwork@.service /etc/systemd/system/
sudo install -m 644 scripts/picalender-artwork@.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now picalender-artwork@USER.timer
sudo systemctl start picalender-artwork@USER.service
systemctl list-timers 'picalender-artwork@*'
journalctl -u picalender-artwork@USER.service -n 30 --no-pager
```

画像の自動生成を止める場合：

```bash
sudo systemctl disable --now picalender-artwork@USER.timer
```

`daily_art.enabled: false` にしてアプリを再起動すると、同梱の固定イラストへ戻る。
サーバーの保存済み画像は残る。

## 確認済みの範囲

2026-09-18にLinuxサーバーのCodex CLI 0.154.0・ChatGPT認証で
組み込み画像生成とPNG保存を確認した。
非対話SSHでは通常のPATHからCodexが見つからなかったため、絶対パスを設定している。
生成成功時でも必ずPNGの構造とチェックサムを確認し、Pi側で画像をデコードしてから置き換える。

- Mac：既存の月齢・六曜・天気・更新処理と合わせて129テスト成功。
- Pi Zero 2 W：追加した26テスト成功。
- PiからSSH経由で翌日分を新規生成し、同じ日付の2回目は同じSHA-256のキャッシュを取得。
- Piへの初回転送、2回目の取得省略、同じアプリPIDでの画像再読み込みを確認。
- systemdタイマーと実行サービスの正常終了を確認。DRM画面出力でも新しい絵を確認。

日付境界は自動テストで確認している。翌朝の自然な切り替えや長期連続運転は、この時点では未観測。

[Codexの非対話実行](https://learn.chatgpt.com/docs/non-interactive-mode)と
[画像生成](https://learn.chatgpt.com/docs/image-generation)の公式説明を参照。
