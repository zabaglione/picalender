# PiCalendar クイックスタートガイド

## 🚀 自動起動＆フルスクリーン設定（1コマンド）

Raspberry Piの電源を入れたら自動的にPiCalendarがフルスクリーン表示されるようにする：

```bash
cd ~/picalender
./scripts/setup_autostart_fullscreen.sh
sudo reboot
```

これだけで完了です！

## ✅ 設定内容

上記のコマンドで以下が自動設定されます：

- 🖥️ **自動起動** - X Window起動時に自動でPiCalendarが起動
- 🔲 **フルスクリーン** - 全画面表示
- 🚫 **スクリーンセーバー無効** - 画面が消えない
- ⚡ **最適化** - Raspberry Pi用に最適化

## 📱 操作方法

- **終了**: ESCキーまたはQキー
- **フルスクリーン切り替え**: F11キー（通常は不要）

## 🔧 トラブルシューティング

### 表示されない場合

```bash
# 手動で実行してエラーを確認
cd ~/picalender
python3 main_x11.py
```

### ログ確認

```bash
# 自動起動ログ
tail -f ~/picalender/logs/autostart.log
```

### 自動起動を無効にしたい場合

```bash
rm ~/.config/autostart/picalender.desktop
```

## 💡 ヒント

- 初回起動時は少し時間がかかります（5-10秒）
- メモリ不足の場合はRaspberry Pi OSのGUIを軽量版に変更することを推奨

## 📞 サポート

問題が発生した場合は、[Issues](https://github.com/zabaglione/picalender/issues)でお知らせください。