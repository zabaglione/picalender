#!/usr/bin/env python
"""品質確認スクリプト"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """コマンドを実行して結果を表示"""
    print(f"\n{'='*60}")
    print(f"実行: {description}")
    print(f"コマンド: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 成功")
        if result.stdout:
            print(result.stdout[:500])  # 最初の500文字のみ
    else:
        print(f"❌ 失敗 (コード: {result.returncode})")
        if result.stderr:
            print(result.stderr[:500])
    
    return result.returncode == 0

def main():
    """品質確認を実行"""
    print("TASK-101: pygame/SDL2初期化 - 品質確認")
    print("="*60)
    
    checks = []
    
    # 1. テスト実行
    checks.append(run_command(
        "python -m pytest tests/test_display_manager.py -q --tb=no",
        "テスト実行"
    ))
    
    # 2. インポート確認
    checks.append(run_command(
        "python -c 'from src.display import DisplayManager, EnvironmentDetector; print(\"インポート成功\")'",
        "モジュールインポート確認"
    ))
    
    # 3. 基本動作確認
    test_code = """
import sys
sys.path.insert(0, '.')
from src.display import DisplayManager, EnvironmentDetector
from unittest.mock import MagicMock

# モック設定
mock_config = MagicMock()
def mock_get(key, default=None):
    config = {
        'screen': {'width': 800, 'height': 600, 'fps': 30},
        'ui': {'fullscreen': False, 'hide_cursor': False},
        'logging': {'level': 'INFO'}
    }
    return config.get(key, default)
mock_config.get.side_effect = mock_get

# 初期化テスト
dm = DisplayManager(mock_config)
print(f"DisplayManager作成: {dm is not None}")

# 環境検出テスト
is_rpi = EnvironmentDetector.is_raspberry_pi()
has_display = EnvironmentDetector.has_display()
driver = EnvironmentDetector.get_video_driver()

print(f"環境検出: RPi={is_rpi}, Display={has_display}, Driver={driver}")
print("基本動作確認: 成功")
"""
    
    with open('test_basic.py', 'w') as f:
        f.write(test_code)
    
    checks.append(run_command(
        "python test_basic.py",
        "基本動作確認"
    ))
    
    os.remove('test_basic.py')
    
    # 4. ファイル存在確認
    files_to_check = [
        'src/display/__init__.py',
        'src/display/display_manager.py',
        'src/display/environment_detector.py',
        'tests/test_display_manager.py',
        'docs/implementation/TASK-101/requirements.md',
        'docs/implementation/TASK-101/testcases.md',
        'docs/implementation/TASK-101/test_results_red.md',
        'docs/implementation/TASK-101/test_results_green.md',
        'docs/implementation/TASK-101/implementation.md'
    ]
    
    print(f"\n{'='*60}")
    print("ファイル存在確認")
    print('='*60)
    
    all_exist = True
    for file in files_to_check:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
        all_exist = all_exist and exists
    
    checks.append(all_exist)
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("品質確認結果サマリー")
    print('='*60)
    
    check_names = [
        "テスト実行",
        "モジュールインポート",
        "基本動作確認",
        "ファイル存在確認"
    ]
    
    for name, result in zip(check_names, checks):
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{name}: {status}")
    
    all_passed = all(checks)
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 すべての品質確認が成功しました！")
        print("TASK-101: pygame/SDL2初期化 は完了です。")
    else:
        print("⚠️ 一部の品質確認が失敗しました。")
        print("問題を修正してください。")
    print('='*60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())