# PiCalendar統合版への移行ノート

## 変更内容

### 2025年8月13日 - main.py統合

**主な変更：**
- `main.py`と`main_x11.py`を単一の`main.py`に統合
- 環境自動検出機能を実装
- 全レンダラーを統合版で利用可能に変更

**環境検出ロジック：**
1. **macOS**: デフォルトドライバー（Cocoa）を使用
2. **X11環境**: X11ドライバーを自動設定、DISPLAY=:0設定
3. **ARM系（X11なし）**: KMSDRMドライバーを使用
4. **その他**: デフォルトドライバー

**統合されたレンダラー：**
- ✅ 時計（SimpleClockRenderer）
- ✅ 日付（SimpleDateRenderer）  
- ✅ カレンダー（SimpleCalendarRenderer）
- ✅ 天気（SimpleWeatherRenderer）
- ✅ 壁紙（SimpleWallpaperRenderer）
- ✅ 月相（SimpleMoonRenderer）

## 移行後の利用方法

### 基本実行
```bash
# 従来: python3 main_x11.py
# 新方式: python3 main.py（環境自動検出）
python3 main.py
```

### 環境変数制御
```bash
# フルスクリーン強制
export PICALENDER_FULLSCREEN=true
python3 main.py

# ウィンドウモード強制  
export PICALENDER_WINDOWED=true
python3 main.py
```

### キー操作（X11環境）
- `ESC` / `Q`: 終了
- `F11` / `F`: フルスクリーン切り替え

## 更新されたスクリプト

- ✅ `restart.sh` → `main.py`を実行
- ✅ `quick_restart.sh` → `main.py`を実行  
- ✅ `scripts/run_on_x11.sh` → `main.py`を実行

## バックアップファイル

- `main_x11.py.backup` - 旧X11版のバックアップ

## 互換性

**従来のコマンド**は全て動作します：
- `./scripts/restart.sh`
- `./scripts/quick_restart.sh` 
- `scripts/run_on_x11.sh`

統合により、どの環境でも同じコマンドで実行可能になりました。