#\!/bin/bash
# フォント問題修正スクリプト

echo "=== 日本語フォント問題の修正 ==="
echo ""

# 1. 日本語フォントのインストール
echo "1. 日本語フォントのインストール..."
if \! dpkg -l | grep -q fonts-noto-cjk; then
    echo "   fonts-noto-cjk をインストールします..."
    sudo apt-get update
    sudo apt-get install -y fonts-noto-cjk fonts-noto
    sudo fc-cache -fv
    echo "   ✓ インストール完了"
else
    echo "   ✓ fonts-noto-cjk は既にインストールされています"
fi

# 2. フォントファイルのコピー
echo ""
echo "2. フォントファイルの配置..."

# システムフォントをプロジェクトにコピー
if [ \! -f "./assets/fonts/NotoSansCJK-Regular.otf" ]; then
    echo "   プロジェクトにフォントファイルをコピーします..."
    
    # 利用可能なフォントを探す
    FONT_PATHS=(
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf"
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"
        "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf"
    )
    
    FOUND=false
    for font_path in "${FONT_PATHS[@]}"; do
        if [ -f "$font_path" ]; then
            echo "   見つかったフォント: $font_path"
            cp "$font_path" ./assets/fonts/NotoSansCJK-Regular.otf
            FOUND=true
            echo "   ✓ フォントをコピーしました"
            break
        fi
    done
    
    if [ "$FOUND" = false ]; then
        echo "   ✗ 適切なフォントファイルが見つかりませんでした"
        echo "   手動でフォントをダウンロードします..."
        
        # Google Fontsから直接ダウンロード（代替案）
        cd ./assets/fonts/
        wget -O NotoSansCJK-Regular.otf "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
        cd ../..
        echo "   ✓ フォントをダウンロードしました"
    fi
else
    echo "   ✓ フォントファイルは既に存在します"
fi

# 3. 権限の確認
echo ""
echo "3. ファイル権限の確認..."
chmod 644 ./assets/fonts/*.otf 2>/dev/null
echo "   ✓ フォントファイルの権限を設定しました"

echo ""
echo "=== 修正完了 ==="
echo ""
echo "アプリケーションを再起動してください:"
echo "  ./scripts/quick_restart.sh"
