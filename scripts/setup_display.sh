#!/bin/bash

# ディスプレイ設定スクリプト（Raspberry Pi Zero 2 W + 1024x600ディスプレイ）

set -e

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Raspberry Pi ディスプレイ設定 ===${NC}"

# ルート権限チェック
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: このスクリプトはroot権限で実行する必要があります${NC}"
   echo "使用方法: sudo ./setup_display.sh"
   exit 1
fi

# config.txtのバックアップ
CONFIG_FILE="/boot/config.txt"
BACKUP_FILE="/boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)"

echo "設定ファイルのバックアップを作成中..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "バックアップ作成完了: $BACKUP_FILE"

# ディスプレイ設定の追加/更新
echo "ディスプレイ設定を更新中..."

# 既存の設定をコメントアウト
sed -i 's/^hdmi_group=/#hdmi_group=/g' "$CONFIG_FILE"
sed -i 's/^hdmi_mode=/#hdmi_mode=/g' "$CONFIG_FILE"
sed -i 's/^hdmi_cvt=/#hdmi_cvt=/g' "$CONFIG_FILE"
sed -i 's/^hdmi_drive=/#hdmi_drive=/g' "$CONFIG_FILE"
sed -i 's/^hdmi_force_hotplug=/#hdmi_force_hotplug=/g' "$CONFIG_FILE"
sed -i 's/^config_hdmi_boost=/#config_hdmi_boost=/g' "$CONFIG_FILE"
sed -i 's/^disable_overscan=/#disable_overscan=/g' "$CONFIG_FILE"

# PiCalendar用の設定を追加
cat >> "$CONFIG_FILE" << EOF

# === PiCalendar Display Configuration ===
# 1024x600 @ 60Hz display settings
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 3 0 0 0
hdmi_drive=2
config_hdmi_boost=4
disable_overscan=1

# GPU memory allocation (optimized for Pi Zero 2 W)
gpu_mem=128

# Enable DRM/KMS for pygame
dtoverlay=vc4-kms-v3d
max_framebuffers=2

# Disable screen blanking
hdmi_blanking=1

# === End PiCalendar Configuration ===
EOF

echo -e "${GREEN}設定更新完了${NC}"

# cmdline.txtの設定
CMDLINE_FILE="/boot/cmdline.txt"
CMDLINE_BACKUP="/boot/cmdline.txt.backup.$(date +%Y%m%d_%H%M%S)"

echo "cmdline.txtのバックアップを作成中..."
cp "$CMDLINE_FILE" "$CMDLINE_BACKUP"

# コンソール無効化の確認
if ! grep -q "logo.nologo" "$CMDLINE_FILE"; then
    echo "起動時のロゴを無効化..."
    sed -i '$ s/$/ logo.nologo/' "$CMDLINE_FILE"
fi

if ! grep -q "consoleblank=0" "$CMDLINE_FILE"; then
    echo "コンソールブランキングを無効化..."
    sed -i '$ s/$/ consoleblank=0/' "$CMDLINE_FILE"
fi

# フォントのインストール確認
echo "必要なフォントをインストール中..."
apt-get update
apt-get install -y fonts-noto-cjk fonts-noto-color-emoji

# SDL2とpygameの依存関係
echo "SDL2関連パッケージをインストール中..."
apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Python依存関係の確認
echo "Python依存関係をインストール中..."
pip3 install pygame pyyaml requests pillow

# サービス用ユーザーの設定
echo "ユーザー権限を設定中..."
usermod -a -G video,audio,input pi

# ディスプレイ電源管理の無効化
echo "ディスプレイ電源管理を無効化中..."
cat > /etc/X11/xorg.conf.d/10-blanking.conf << EOF
Section "ServerFlags"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
    Option "BlankTime" "0"
EndSection
EOF

# 起動時の自動ログイン設定（CLI）
echo "自動ログインを設定中..."
systemctl set-default multi-user.target
mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I \$TERM
EOF

echo -e "${GREEN}=== ディスプレイ設定完了 ===${NC}"
echo
echo -e "${YELLOW}重要: 設定を有効にするには再起動が必要です${NC}"
echo "再起動コマンド: sudo reboot"
echo
echo "設定内容:"
echo "  - 解像度: 1024x600 @ 60Hz"
echo "  - DRM/KMS有効化"
echo "  - 画面ブランキング無効化"
echo "  - 自動ログイン設定"
echo "  - 必要なフォントインストール済み"
echo
echo "元の設定に戻す場合:"
echo "  sudo cp $BACKUP_FILE $CONFIG_FILE"
echo "  sudo cp $CMDLINE_BACKUP $CMDLINE_FILE"
echo "  sudo reboot"