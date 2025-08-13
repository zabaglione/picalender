#!/bin/bash

# PiCalendar フォントインストールスクリプト

echo "========================================="
echo "  PiCalendar Font Installer"
echo "========================================="
echo ""

# フォントディレクトリ作成
mkdir -p assets/fonts

# OSを検出
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected"
    # macOSの場合はシステムフォントへのシンボリックリンクを作成
    if [ -f "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc" ]; then
        ln -sf "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc" "assets/fonts/NotoSansCJK-Regular.otf"
        echo "✅ Linked to Hiragino font"
    else
        echo "⚠️  Hiragino font not found, Japanese text may not display correctly"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux/Raspberry Pi detected"
    
    # Raspberry Piでのフォントインストール確認
    if [ -f "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" ]; then
        echo "✅ Noto Sans CJK font already installed"
        ln -sf "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" "assets/fonts/NotoSansCJK-Regular.otf"
    else
        echo "❌ Noto Sans CJK font not found"
        echo ""
        echo "Installing Japanese fonts..."
        echo "This may require sudo password:"
        sudo apt-get update
        sudo apt-get install -y fonts-noto-cjk fonts-vlgothic
        
        # インストール後に再度リンク作成を試みる
        if [ -f "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" ]; then
            ln -sf "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" "assets/fonts/NotoSansCJK-Regular.otf"
            echo "✅ Font installed and linked successfully"
        else
            echo "⚠️  Font installation may have failed"
        fi
    fi
fi

echo ""
echo "Font setup completed!"
echo ""

# フォントの確認
if [ -L "assets/fonts/NotoSansCJK-Regular.otf" ] || [ -f "assets/fonts/NotoSansCJK-Regular.otf" ]; then
    echo "✅ Font file is ready: assets/fonts/NotoSansCJK-Regular.otf"
    ls -la assets/fonts/
else
    echo "⚠️  Font file not found. You may need to manually install fonts."
fi