#!/bin/bash

# PiCalendar 自動起動＆フルスクリーン設定スクリプト

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  PiCalendar 自動起動設定"
echo "  （フルスクリーン版）"
echo "========================================="
echo ""

CURRENT_USER=${SUDO_USER:-$USER}
INSTALL_DIR="/home/$CURRENT_USER/picalender"

echo -e "${GREEN}ユーザー名:${NC} $CURRENT_USER"
echo -e "${GREEN}インストールディレクトリ:${NC} $INSTALL_DIR"
echo ""

# 1. 起動スクリプトの作成
echo -e "${YELLOW}1. 起動スクリプトを作成...${NC}"

cat > "$INSTALL_DIR/start_fullscreen.sh" <<'EOF'
#!/bin/bash

# 少し待機（X Windowの起動を待つ）
sleep 5

# ログファイル
LOG_FILE="/home/$USER/picalender/logs/autostart.log"
mkdir -p /home/$USER/picalender/logs

echo "$(date): Starting PiCalendar..." >> $LOG_FILE

# 環境変数設定
export DISPLAY=:0
export PICALENDER_FULLSCREEN=true

# PiCalendarディレクトリに移動
cd /home/$USER/picalender

# 仮想環境のアクティベート（存在する場合）
if [ -d "venv" ]; then
    echo "$(date): Activating virtual environment..." >> $LOG_FILE
    source venv/bin/activate
    PYTHON_CMD="python3"
else
    echo "$(date): Using system Python" >> $LOG_FILE
    PYTHON_CMD="python3"
fi

# X11版をフルスクリーンで起動
$PYTHON_CMD main_x11.py >> $LOG_FILE 2>&1 &

echo "$(date): PiCalendar started with PID $!" >> $LOG_FILE
EOF

chmod +x "$INSTALL_DIR/start_fullscreen.sh"
echo -e "${GREEN}✓ 起動スクリプトを作成しました${NC}"

# 2. LXDEの自動起動設定
echo -e "${YELLOW}2. LXDE自動起動設定...${NC}"

# ユーザーの自動起動ディレクトリ
AUTOSTART_DIR="/home/$CURRENT_USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/picalender.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PiCalendar Fullscreen
Comment=Raspberry Pi Calendar Display (Fullscreen)
Exec=$INSTALL_DIR/start_fullscreen.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
StartupNotify=false
EOF

echo -e "${GREEN}✓ デスクトップエントリを作成しました${NC}"

# 3. LXDEのautostart設定（システム全体）
echo -e "${YELLOW}3. システム自動起動設定...${NC}"

LXDE_AUTOSTART="/home/$CURRENT_USER/.config/lxsession/LXDE-pi/autostart"
LXDE_DIR="/home/$CURRENT_USER/.config/lxsession/LXDE-pi"

# ディレクトリ作成
mkdir -p "$LXDE_DIR"

# 既存の設定をバックアップ
if [ -f "$LXDE_AUTOSTART" ]; then
    cp "$LXDE_AUTOSTART" "${LXDE_AUTOSTART}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}既存の設定をバックアップしました${NC}"
fi

# autostartファイルを作成/更新
if ! grep -q "picalender/start_fullscreen.sh" "$LXDE_AUTOSTART" 2>/dev/null; then
    # デフォルト設定をコピー（存在しない場合）
    if [ ! -f "$LXDE_AUTOSTART" ]; then
        cat > "$LXDE_AUTOSTART" <<EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
EOF
    fi
    
    # PiCalender追加
    echo "@$INSTALL_DIR/start_fullscreen.sh" >> "$LXDE_AUTOSTART"
    echo -e "${GREEN}✓ 自動起動設定を追加しました${NC}"
else
    echo -e "${GREEN}✓ 自動起動設定は既に存在します${NC}"
fi

# 4. スクリーンセーバーとブランキングの無効化
echo -e "${YELLOW}4. スクリーンセーバーを無効化...${NC}"

# lightdm設定
if [ -f /etc/lightdm/lightdm.conf ]; then
    sudo cp /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # xserver-commandの設定
    if ! grep -q "xserver-command=X -s 0 -dpms" /etc/lightdm/lightdm.conf; then
        sudo sed -i '/^\[Seat:\*\]/a xserver-command=X -s 0 -dpms' /etc/lightdm/lightdm.conf
        echo -e "${GREEN}✓ スクリーンセーバーを無効化しました${NC}"
    fi
fi

# autostart内でもスクリーンセーバーを無効化
if ! grep -q "@xset" "$LXDE_AUTOSTART"; then
    cat >> "$LXDE_AUTOSTART" <<EOF
@xset s noblank
@xset s off
@xset -dpms
EOF
    echo -e "${GREEN}✓ 画面ブランキングを無効化しました${NC}"
fi

# 5. main_x11.pyをフルスクリーンデフォルトに変更
echo -e "${YELLOW}5. フルスクリーンをデフォルトに設定...${NC}"

sed -i "s/'fullscreen': False/'fullscreen': True/" "$INSTALL_DIR/main_x11.py" 2>/dev/null || true
echo -e "${GREEN}✓ フルスクリーンをデフォルトに設定しました${NC}"

# 6. 権限設定
echo -e "${YELLOW}6. 権限設定...${NC}"

chmod +x "$INSTALL_DIR/main_x11.py"
chmod +x "$INSTALL_DIR/start_fullscreen.sh"
chown -R $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR/.config" 2>/dev/null || true
chown -R $CURRENT_USER:$CURRENT_USER "/home/$CURRENT_USER/.config/autostart" 2>/dev/null || true
chown -R $CURRENT_USER:$CURRENT_USER "/home/$CURRENT_USER/.config/lxsession" 2>/dev/null || true

echo -e "${GREEN}✓ 権限を設定しました${NC}"

# 7. systemdサービスの無効化（競合防止）
echo -e "${YELLOW}7. systemdサービスを無効化...${NC}"

if systemctl is-enabled --quiet picalender 2>/dev/null; then
    sudo systemctl stop picalender 2>/dev/null || true
    sudo systemctl disable picalender 2>/dev/null || true
    echo -e "${GREEN}✓ systemdサービスを無効化しました${NC}"
else
    echo -e "${GREEN}✓ systemdサービスは既に無効です${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}設定完了！${NC}"
echo "========================================="
echo ""
echo "設定内容："
echo "  • 電源投入時に自動起動"
echo "  • フルスクリーン表示"
echo "  • スクリーンセーバー無効"
echo "  • 画面ブランキング無効"
echo ""
echo "次のステップ："
echo -e "${YELLOW}1. システムを再起動してください：${NC}"
echo "   sudo reboot"
echo ""
echo "手動テスト："
echo "   cd $INSTALL_DIR"
echo "   ./start_fullscreen.sh"
echo ""
echo "ログ確認："
echo "   tail -f $INSTALL_DIR/logs/autostart.log"
echo ""
echo "終了方法："
echo "   ESCキーまたはQキーを押す"
echo ""