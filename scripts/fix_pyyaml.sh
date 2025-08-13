#\!/bin/bash
# PyYAMLインストールスクリプト

echo "=== PyYAML インストール ==="
echo ""

# 仮想環境の確認
if [ -d "venv" ]; then
    echo "仮想環境を有効化しています..."
    source venv/bin/activate
fi

# PyYAMLのインストール
echo "PyYAMLをインストールしています..."
pip3 install pyyaml

# インストール確認
echo ""
echo "インストール確認:"
python3 -c "import yaml; print('✓ PyYAML', yaml.__version__, 'がインストールされました')" 2>/dev/null || echo "✗ PyYAMLのインストールに失敗しました"

echo ""
echo "=== 完了 ==="
echo ""
echo "アプリケーションを再起動してください:"
echo "  ./scripts/quick_restart.sh"
