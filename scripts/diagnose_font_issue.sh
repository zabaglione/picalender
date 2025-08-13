#\!/bin/bash
# フォント問題診断スクリプト

echo "=== フォント問題診断 ==="
echo ""

# 1. 日本語フォントの確認
echo "1. 日本語フォントのインストール状況:"
if dpkg -l | grep -q fonts-noto-cjk; then
    echo "   ✓ fonts-noto-cjk がインストールされています"
else
    echo "   ✗ fonts-noto-cjk がインストールされていません"
fi

# 2. フォントファイルの存在確認
echo ""
echo "2. フォントファイルの存在確認:"

# プロジェクト内のフォント
if [ -f "./assets/fonts/NotoSansCJK-Regular.otf" ]; then
    echo "   ✓ ./assets/fonts/NotoSansCJK-Regular.otf が存在します"
    ls -lh ./assets/fonts/NotoSansCJK-Regular.otf
else
    echo "   ✗ ./assets/fonts/NotoSansCJK-Regular.otf が存在しません"
fi

# システムフォント
if [ -f "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf" ]; then
    echo "   ✓ /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf が存在します"
else
    echo "   ✗ /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf が存在しません"
fi

# 3. Pygameのフォント確認
echo ""
echo "3. Pygameでフォントが読み込めるか確認:"
python3 -c "
import pygame
pygame.init()

# フォントファイルのテスト
fonts_to_test = [
    './assets/fonts/NotoSansCJK-Regular.otf',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
]

for font_path in fonts_to_test:
    try:
        from pathlib import Path
        if Path(font_path).exists():
            font = pygame.font.Font(font_path, 24)
            test_surface = font.render('テスト日本語', True, (255, 255, 255))
            print(f'   ✓ {font_path} - 正常に読み込めました')
        else:
            print(f'   - {font_path} - ファイルが存在しません')
    except Exception as e:
        print(f'   ✗ {font_path} - エラー: {e}')

# システムフォント
print('')
print('システムフォント:')
try:
    sysfont = pygame.font.SysFont('notosanscjkjp', 24)
    test_surface = sysfont.render('テスト日本語', True, (255, 255, 255))
    print('   ✓ SysFont(notosanscjkjp) - 正常')
except Exception as e:
    print(f'   ✗ SysFont(notosanscjkjp) - エラー: {e}')
"

# 4. カレンダーレンダラーのテスト
echo ""
echo "4. カレンダーレンダラーの初期化テスト:"
cd $(dirname $0)/..
python3 -c "
import sys
import pygame
import yaml
from pathlib import Path

pygame.init()

# 設定読み込み
with open('settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)

# レンダラーパス追加
sys.path.append(str(Path('.') / 'src' / 'renderers'))

try:
    from simple_calendar_renderer import SimpleCalendarRenderer
    renderer = SimpleCalendarRenderer(settings)
    print('   ✓ カレンダーレンダラーが正常に初期化されました')
    print(f'   位置: x={renderer.cal_x}, y={renderer.cal_y}')
    print(f'   サイズ: {renderer.cal_width}x{renderer.cal_height}')
except Exception as e:
    print(f'   ✗ カレンダーレンダラーの初期化に失敗: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== 診断完了 ==="
