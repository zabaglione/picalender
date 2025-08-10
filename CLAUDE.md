自信の度合い：高

# 仕様書：Raspberry Pi Zero 2 W 常時表示型「時計・カレンダー・天気・2Dキャラ」キオスク

## 1. 目的・背景

* 目的：Raspberry Pi Zero 2 W（1024×600ディスプレイ）で、常時フルスクリーン表示の情報端末を実現する。主表示要素はデジタル時計、当月カレンダー（日曜始まり）、天気予報（Yahoo API想定）、任意の2Dキャラクターアニメーション。
* 運用方針：電源投入＝専用アプリ自動起動、ネットワーク断でも最低限（時計・カレンダー）を継続表示。将来の要素追加に耐える軽量・拡張性のある構成。

## 2. 対象環境

* ハード：Raspberry Pi Zero 2 W、解像度 1024×600、常時給電、ローカルストレージ microSD
* OS：Raspberry Pi OS Lite（64bit推奨）
* 表示：Xを使わず DRM/KMS 直描画（SDL2 / kmsdrm）
* 言語：Python 3.11 以上
* 主要ライブラリ：pygame（SDL2 バックエンド利用）、PyYAML、requests
* フォント：Noto Sans CJK または等価（日本語表示のため）
* ネットワーク：Wi-Fi（天気取得用）。ネット断時は最後の成功レスポンスをキャッシュ表示

## 3. 全体構成（論理アーキテクチャ）

* 単一プロセス（描画ループ）

  * レイヤ順：背景画像 → 時計（時分秒／年月日） → カレンダー → 天気パネル → 2Dキャラクター（任意）
* バックグラウンドスレッド

  * 天気取得（定期：10〜30分間隔、結果を共有キュー経由でUIへ）
* 設定・資産

  * `settings.yaml` によるレイアウト・フォント・更新間隔・天気プロバイダ等の外部化
  * `assets/`（フォント、天気アイコン、スプライト）
  * `wallpapers/`（背景画像、ローテーション対応）
* 自動起動：systemd サービス
* ログ：標準出力（journald）、必要に応じてローテーションファイル出力

## 4. 画面仕様（1024×600 固定初期設計）

* マージン：左右 24px、上下 16px
* 時計（時:分:秒）

  * 位置：上部中央
  * フォントサイズ：130px 目安
  * 更新：毎秒
* 日付（YYYY-MM-DD (曜)）

  * 時計直下、フォント 36px
  * 更新：毎分
* カレンダー（今月・日曜始まり）

  * 位置：右下、約 420×280px
  * 曜日ヘッダ行＋最大6週表示
  * 日曜は赤系、土曜は青系、平日は白系文字色
  * 更新：毎分
* 天気パネル（3日分）

  * 位置：左下、約 420×280px、角丸の濃色パネル背景内に文字列＋アイコン
  * 項目：日付、最低/最高気温（℃）、降水確率（%）、天気アイコン
  * 更新：取得間隔に準拠（失敗時はキャッシュ）
* 背景画像

  * 優先比率「fit」（レターボックス黒埋め）。`settings.yaml` で `fit|scale` 切替
  * 再スキャン間隔：既定 300 秒（追加・差替を自動反映）
* 2Dキャラクター（任意）

  * 左上付近、スプライトシート横並び、フレームサイズ・FPSは設定可能（初期 128×128、8fps）

## 5. 機能要件（Functional Requirements）

1. 時計表示

   * ローカル時刻から時分秒を描画。NTP 同期はOS任せ。
2. 日付表示

   * ローカル日付、曜日英略または日本語略（設定で切替可）。
3. カレンダー表示

   * 月カレンダー（日曜始まり）。月切替は自動。祝日表示は当面対象外（将来拡張）。
4. 天気表示

   * 3日分の天気予報。既定はテスト用に Open-Meteo、運用では Yahoo へ差替可能なプロバイダ仕様。
   * 通信失敗時は最後に成功した結果をキャッシュ表示。キャッシュがなければ「取得不可」明示。
5. 背景画像

   * `wallpapers/` の静止画を1枚選択して固定表示。複数ある場合は先頭採用。将来はローテーションや時刻別切替に拡張。
6. 全画面・専用化

   * 起動時フルスクリーン、マウスカーソル非表示。systemd 自動起動対応。
7. 設定外部化

   * `settings.yaml` で表示サイズ、フォント、プロバイダ、更新間隔等を編集可能。
8. 低負荷動作

   * テキスト再レンダの間引き（時計：毎秒、日付/カレンダー：毎分、天気：取得時のみ）。
9. ログ

   * 起動・取得成功/失敗・例外を INFO/ERROR レベルで記録。

## 6. 非機能要件（Non-Functional Requirements）

* パフォーマンス：Pi Zero 2 W で CPU 使用率の平均 30% 未満、メモリ消費 180MB 以下を目安（キャラ無効時）
* 可用性：電源断→再投入で自動復旧。ネット断でも時計・カレンダーは継続。
* メンテナンス性：天気プロバイダは抽象クラス準拠の差替設計。描画ロジックから独立。
* セキュリティ：APIキーは平文で置かず、`.env` または root 権限ファイルに保持。通信はHTTPS。
* ライセンス順守：フォント・アイコン・天気データの利用規約に従う。Yahoo 利用時はクレジット表記を設定で有効化。

## 7. データフロー・スレッドモデル

* メインスレッド：描画ループ（FPS 30、KMSDRM）
* ワーカー：天気取得（`requests`、間隔 `weather.refresh_sec`、成功時に上書きキャッシュ）
* 共有：スレッドセーフなキューで最新の天気を渡す。描画側は非ブロッキングで参照。

## 8. APIプロバイダ仕様

### 8.1 共通インターフェース

```python
class WeatherProvider(ABC):
    @abstractmethod
    def fetch(self) -> dict:
        # 返却例:
        # {
        #   "updated": 1699999999,
        #   "forecasts": [
        #     {"date": "YYYY-MM-DD", "icon": "sunny|cloudy|rain|thunder|fog", "tmin": 24, "tmax": 32, "pop": 40},
        #     ...
        #   ]
        # }
        ...
```

### 8.2 Open-Meteo（検証用）

* 認証不要。日次予報を3件抽出し、内部アイコンにマッピング。
* タイムアウト 10 秒、リトライはアプリ側で次周期に任せる。

### 8.3 Yahoo 天気（運用想定）

* 認証：Yahoo! JAPAN の App ID/OAuth 等（正式仕様に準拠）
* 地域コード：設定で指定
* レスポンス→内部アイコンのマッピングテーブルを実装
* 表示義務（クレジット等）がある場合、パネル内に小さく表記できるオプションを設ける

## 9. 設定ファイル（`settings.yaml` 例）

```yaml
screen: { width: 1024, height: 600, fps: 30 }
ui:
  margins: { x: 24, y: 16 }
  clock_font_px: 130
  date_font_px: 36
  cal_font_px: 22
  weather_font_px: 22
calendar:
  first_weekday: "SUNDAY"  # SUNDAY|MONDAY
background:
  dir: "./wallpapers"
  mode: "fit"         # fit|scale
  rescan_sec: 300
weather:
  provider: "openmeteo"    # openmeteo|yahoo
  refresh_sec: 1800
  location: { lat: 35.681236, lon: 139.767125 }
  yahoo:
    app_id: ""
    client_id: ""
    client_secret: ""
character:
  enabled: false
  sprite: "./assets/sprites/char_idle.png"
  frame_w: 128
  frame_h: 128
  fps: 8
fonts:
  main: "./assets/fonts/NotoSansCJK-Regular.otf"
logging:
  level: "INFO"
```

## 10. ディレクトリ構成

```
/home/pi/clock-kiosk/
  main.py
  settings.yaml
  providers/
    __init__.py
    weather_base.py
    weather_openmeteo.py
    weather_yahoo.py      # 実装テンプレート
  assets/
    fonts/NotoSansCJK-Regular.otf
    icons/weather/        # 内部アイコン名と一致させる
      sunny.png cloudy.png rain.png thunder.png fog.png
    sprites/char_idle.png # 横長スプライトシート
  wallpapers/
    001.jpg 002.jpg ...
```

## 11. 実装方針（要点）

* 描画間引き：

  * 秒単位：時計のみ再レンダ
  * 分単位：日付・カレンダー再生成
  * 天気：取得時のみ再描画
* 画像スケーリング：`smoothscale`、ただし Zero 2 W で負荷が高い場合は通常 `scale` に切替可能
* 文字色・配色：見やすさ重視の高コントラスト（背景次第でドロップシャドウを将来検討）

## 12. 起動・常駐（systemd）

* `/etc/systemd/system/clock-kiosk.service`

```
[Unit]
Description=Clock Kiosk (pygame KMSDRM)
After=multi-user.target

[Service]
User=pi
WorkingDirectory=/home/pi/clock-kiosk
Environment=SDL_VIDEODRIVER=kmsdrm
ExecStart=/usr/bin/python3 /home/pi/clock-kiosk/main.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

* 有効化手順
  `sudo systemctl daemon-reload && sudo systemctl enable clock-kiosk && sudo systemctl start clock-kiosk`

## 13. 2Dキャラクター仕様

* スプライト：横並びフレーム、RGBA PNG 推奨
* 設定：`frame_w`・`frame_h`・`fps`・表示座標（固定配置）
* 省負荷：フレーム更新は 8〜12fps 程度。描画は合成1回。サイズは 128〜256px 目安。

## 14. 例外・エラーハンドリング

* 天気取得失敗：前回キャッシュを表示、なければ「取得不可」
* 設定欠落：既定値で起動し、ログで警告
* 画像・フォント読み込み失敗：代替フォント・無地背景で継続
* 連続例外：systemd の Restart 設定で自動再起動

## 15. ログ・監視

* ログ出力：標準出力へ時刻・レベル・メッセージ
* 監視：`systemctl status clock-kiosk`、`journalctl -u clock-kiosk -f`
* 任意：簡易ヘルスエンドポイントは不要（ローカル端末のため）

## 16. セキュリティ

* API 認証情報は `.env` または root 所有の別 YAML に分離し、`settings.yaml` から参照
* HTTPS 必須、証明書検証を無効化しない
* 外部サービス規約（特に Yahoo）に準拠し、必要なクレジット表示を実装

## 17. ビルド・デプロイ

* 依存導入（例）

  * `sudo apt-get update`
  * `sudo apt-get install -y python3-pip fonts-noto-cjk`
  * `pip3 install pygame==2.* pyyaml requests`
* フォント・アイコン・スプライト・壁紙を所定のパスに配置
* 設定調整後、systemd を有効化

## 18. テスト計画（受け入れ基準含む）

* 単体：

  * `WeatherProvider.fetch()` の戻り値フォーマット検証
  * 画像読み込み・スケール関数の境界値（縦横比差）
* 結合：

  * ネットワーク断→復帰で天気表示が更新される
  * 壁紙追加・差替が `background.rescan_sec` 後に反映
* 性能：

  * キャラ無効時 CPU 30% 未満、メモリ 180MB 未満
  * キャラ有効時 45% 未満、メモリ 220MB 未満（目標）
* 長期：

  * 72 時間連続稼働でクラッシュ・メモリリークなし
* 受け入れ基準：

  * 起動 10 秒以内にフルスクリーン表示
  * 時計遅延 ±1 秒以内
  * 天気が 30 分毎に更新（ネット断時はキャッシュ表示）
  * systemd で自動再起動動作が確認できる

## 19. 今後の拡張

* 壁紙ローテーションのスケジューリング（時刻・曜日・天気条件で出し分け）
* 祝日表示、六曜、スケジュール連携（ローカル ICS 読み込み）
* 省電力：就業時間外の減光・消灯、無操作スリープ
* マルチ解像度対応（自動レイアウトスケール）
* GPU 合成（必要なら C++/SDL2 へ移行）

## 20. AIエージェント向け実装タスク分解（WBS）

1. リポジトリ初期化、`settings.yaml` 雛形作成、`requirements.txt` 作成
2. フォント・アイコン・壁紙のダミー資産配置
3. `WeatherProvider` 抽象化、`weather_openmeteo.py` 実装・単体テスト
4. 描画基盤（pygame KMSDRM）実装、フルスクリーン・カーソル非表示
5. 時計・日付描画（更新間引き）
6. カレンダー（日曜始まり、配色）
7. 天気パネル（3日分、アイコン合成、キャッシュ）
8. 背景画像の読み込み・スケーリング・定期再スキャン
9. 2Dキャラ描画（任意、スプライトアニメ）
10. ログ・例外処理・設定バリデーション
11. systemd ユニット作成・有効化スクリプト
12. 性能計測・微調整（フォントサイズ・FPS・合成回数）
13. ドキュメント（導入手順、運用、ライセンス注意点）
14. Yahoo プロバイダ実装テンプレート作成（鍵読み込み、地域コード、アイコンマップ）

## 21. 成果物

* 実行可能な Python アプリ一式（上記構成）
* `README.md`（セットアップ・起動・トラブルシュート）
* `settings.yaml`（本番テンプレート）
* `clock-kiosk.service`（systemd ユニット）
* テスト結果サマリ（性能・長期動作）

---

この仕様に基づき、AIエージェントは順次タスクを実行し、オフラインでも動作確認可能な形で納品できます。必要であれば Yahoo プロバイダの実装テンプレートを追記します。

