#!/bin/bash

# PiCalendar 診断スクリプト

echo "========================================="
echo "    PiCalendar 診断スクリプト"
echo "========================================="
echo ""

# 1. Pythonバージョン確認
echo "1. Python バージョン:"
python3 --version
echo ""

# 2. 必要なパッケージの確認
echo "2. 必要なパッケージ:"
echo -n "  pygame: "
python3 -c "import pygame; print(pygame.version.ver)" 2>/dev/null || echo "NOT INSTALLED"

echo -n "  PyYAML: "
python3 -c "import yaml; print('Installed')" 2>/dev/null || echo "NOT INSTALLED (Optional)"

echo -n "  requests: "
python3 -c "import requests; print('Installed')" 2>/dev/null || echo "NOT INSTALLED"

echo -n "  Pillow: "
python3 -c "from PIL import Image; print('Installed')" 2>/dev/null || echo "NOT INSTALLED (Optional)"
echo ""

# 3. ディレクトリ構造確認
echo "3. ディレクトリ構造:"
echo "  wallpapers/: $(ls wallpapers 2>/dev/null | wc -l) files"
echo "  assets/weather_icons/: $(ls assets/weather_icons 2>/dev/null | wc -l) files"
echo "  cache/: $(ls cache 2>/dev/null | wc -l) files"
echo "  logs/: $(ls logs 2>/dev/null | wc -l) files"
echo ""

# 4. 設定ファイル確認
echo "4. 設定ファイル:"
if [ -f settings.yaml ]; then
    echo "  settings.yaml: EXISTS"
    # YAMLの構文チェック
    python3 -c "
import sys
try:
    import yaml
    with open('settings.yaml', 'r') as f:
        yaml.safe_load(f)
    print('    YAML syntax: OK')
except ImportError:
    print('    YAML check: PyYAML not installed')
except Exception as e:
    print(f'    YAML syntax: ERROR - {e}')
    sys.exit(1)
" || echo "    YAML syntax: INVALID"
else
    echo "  settings.yaml: NOT FOUND"
fi
echo ""

# 5. メインファイルの構文チェック
echo "5. Pythonファイルの構文チェック:"
echo -n "  main_x11.py: "
python3 -m py_compile main_x11.py 2>/dev/null && echo "OK" || echo "SYNTAX ERROR"

echo -n "  main.py: "
python3 -m py_compile main.py 2>/dev/null && echo "OK" || echo "SYNTAX ERROR"
echo ""

# 6. テスト起動（1秒だけ）
echo "6. テスト起動:"
echo "  Trying to import main_x11..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from main_x11 import PiCalendarApp
    print('    Import: SUCCESS')
except Exception as e:
    print(f'    Import: FAILED - {e}')
    import traceback
    traceback.print_exc()
"
echo ""

# 7. 最近のエラーログ
echo "7. 最近のエラー:"
if [ -f logs/restart.log ]; then
    echo "  最新のエラー（restart.log）:"
    grep -i error logs/restart.log | tail -5 | sed 's/^/    /'
fi

if [ -f logs/autostart.log ]; then
    echo "  最新のエラー（autostart.log）:"
    grep -i error logs/autostart.log | tail -5 | sed 's/^/    /'
fi
echo ""

echo "========================================="
echo "診断完了"
echo ""
echo "問題がある場合の対処法:"
echo "1. パッケージが不足している場合:"
echo "   pip3 install pygame pyyaml requests"
echo ""
echo "2. YAML構文エラーの場合:"
echo "   rm settings.yaml  # 一時的に削除"
echo ""
echo "3. それでも起動しない場合:"
echo "   python3 main_x11.py  # 直接実行してエラーを確認"
echo "========================================="