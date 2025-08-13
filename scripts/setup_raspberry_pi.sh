#\!/bin/bash
# Raspberry Pi用の完全セットアップスクリプト

echo "=== Raspberry Pi PiCalendarセットアップ ==="
echo ""

# 仮想環境の確認と有効化
if [ -d "venv" ]; then
    echo "仮想環境を有効化しています..."
    source venv/bin/activate
else
    echo "仮想環境を作成しています..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 1. システムパッケージの更新
echo "1. システムパッケージの更新..."
sudo apt-get update

# 2. 日本語フォントのインストール
echo ""
echo "2. 日本語フォントのインストール..."
if \! dpkg -l | grep -q fonts-noto-cjk; then
    sudo apt-get install -y fonts-noto-cjk fonts-noto
    sudo fc-cache -fv
    echo "   ✓ フォントをインストールしました"
else
    echo "   ✓ フォントは既にインストールされています"
fi

# 3. Pythonパッケージのインストール
echo ""
echo "3. 必要なPythonパッケージのインストール..."
pip3 install --upgrade pip
pip3 install pygame pyyaml requests holidays

# 4. フォントファイルの確認
echo ""
echo "4. フォントファイルの確認..."
if [ \! -f "./assets/fonts/NotoSansCJK-Regular.otf" ]; then
    echo "   フォントファイルをコピーしています..."
    if [ -f "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" ]; then
        cp /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc ./assets/fonts/NotoSansCJK-Regular.otf
        echo "   ✓ フォントをコピーしました"
    fi
else
    echo "   ✓ フォントファイルは既に存在します"
fi

# 5. 動作確認
echo ""
echo "5. 動作確認..."
python3 -c "
import sys
modules = ['pygame', 'yaml', 'requests', 'holidays']
all_ok = True
for module in modules:
    try:
        __import__(module)
        print(f'   ✓ {module} - OK')
    except ImportError:
        print(f'   ✗ {module} - NG')
        all_ok = False

if all_ok:
    print('')
    print('✅ すべての依存関係が正常にインストールされました')
else:
    print('')
    print('⚠️ 一部のモジュールがインストールされていません')
"

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "アプリケーションを起動するには："
echo "  ./scripts/quick_restart.sh"
echo ""
echo "自動起動を設定するには："
echo "  sudo ./scripts/install_service.sh"
