#!/bin/bash

# PiCalendar X11自動起動スクリプト
# X Window環境で自動起動するための設定

# LXDEの自動起動ディレクトリにデスクトップエントリを作成
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/picalender.desktop"

echo "PiCalendar X11自動起動設定"
echo "========================="

# 自動起動ディレクトリ作成
mkdir -p "$AUTOSTART_DIR"

# デスクトップエントリ作成
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=PiCalendar
Comment=Raspberry Pi Calendar Display
Exec=/home/$USER/picalender/main_x11.py
Icon=/home/$USER/picalender/assets/icon.png
Terminal=false
Categories=Utility;
StartupNotify=false
EOF

# 実行権限付与
chmod +x /home/$USER/picalender/main_x11.py

echo "✓ 自動起動設定を作成しました: $DESKTOP_FILE"
echo ""
echo "次回のX Window起動時からPiCalendarが自動的に起動します。"
echo ""
echo "手動で起動する場合:"
echo "  cd ~/picalender"
echo "  ./main_x11.py"
echo ""
echo "または、ターミナルから:"
echo "  DISPLAY=:0 python3 ~/picalender/main_x11.py"