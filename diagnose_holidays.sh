#!/bin/bash

# PiCalendar 祝日機能診断スクリプト

echo "========================================"
echo "  PiCalendar 祝日機能診断"
echo "========================================"
echo ""

# 仮想環境の確認
if [ -d "venv" ]; then
    echo "✅ 仮想環境が存在します"
    source venv/bin/activate
else
    echo "❌ 仮想環境が見つかりません"
    exit 1
fi

echo ""
echo "1. holidaysライブラリの確認"
echo "----------------------------------------"

# holidaysライブラリの確認
if pip list | grep -q holidays; then
    echo "✅ holidaysライブラリはインストール済み"
    pip list | grep holidays
else
    echo "❌ holidaysライブラリがインストールされていません"
    echo ""
    echo "修正コマンド:"
    echo "  pip install holidays"
    echo ""
fi

echo ""
echo "2. 祝日データの動作テスト"
echo "----------------------------------------"

python3 << 'EOF'
try:
    import holidays
    from datetime import date
    
    print("✅ holidaysライブラリのインポート成功")
    
    # 日本の祝日データを取得
    jp_holidays = holidays.Japan(years=[2025])
    print(f"✅ 日本の祝日データ読み込み成功（{len(jp_holidays)}件）")
    
    # 8月11日（山の日）のテスト
    mountain_day = date(2025, 8, 11)
    is_holiday = mountain_day in jp_holidays
    
    print(f"8月11日の祝日判定: {is_holiday}")
    if is_holiday:
        print(f"祝日名: {jp_holidays[mountain_day]}")
    else:
        print("❌ 8月11日が祝日として認識されていません")
    
    # 今月の祝日一覧
    print("\n2025年8月の祝日:")
    for day in range(1, 32):
        try:
            check_date = date(2025, 8, day)
            if check_date in jp_holidays:
                print(f"  {day}日: {jp_holidays[check_date]}")
        except ValueError:
            break
    
except ImportError:
    print("❌ holidaysライブラリがインストールされていません")
    print("修正コマンド: pip install holidays")
except Exception as e:
    print(f"❌ エラー: {e}")
EOF

echo ""
echo "3. 設定ファイルの確認"
echo "----------------------------------------"

if [ -f "settings.yaml" ]; then
    echo "✅ settings.yamlが存在します"
    echo ""
    echo "祝日関連の設定:"
    grep -A 10 "calendar:" settings.yaml || echo "calendar設定が見つかりません"
    echo ""
    echo "色設定:"
    grep -A 10 "colors:" settings.yaml | grep holiday || echo "holiday色設定が見つかりません"
else
    echo "❌ settings.yamlが見つかりません"
fi

echo ""
echo "4. ログの確認"
echo "----------------------------------------"

if [ -f "logs/restart.log" ]; then
    echo "最新の祝日関連ログ:"
    tail -20 logs/restart.log | grep -i holiday || echo "祝日関連のログが見つかりません"
else
    echo "ログファイルが見つかりません"
fi

echo ""
echo "========================================"
echo "診断完了"
echo "========================================"