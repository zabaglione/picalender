#!/usr/bin/env python
"""テスト実行スクリプト"""

import subprocess
import sys

# テストを実行
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 
     'tests/test_display_manager.py', 
     '-v', '--tb=short', '--timeout=5'],
    capture_output=True,
    text=True,
    timeout=30
)

# 結果を解析
lines = result.stdout.split('\n')
passed = 0
failed = 0

for line in lines:
    if 'PASSED' in line:
        passed += 1
    elif 'FAILED' in line:
        failed += 1

print(f"Test Results:")
print(f"  PASSED: {passed}")
print(f"  FAILED: {failed}")
print(f"  TOTAL:  {passed + failed}")

# 失敗したテストを表示
if failed > 0:
    print("\nFailed tests:")
    for line in lines:
        if 'FAILED' in line:
            test_name = line.split('::')[-1].split(' ')[0]
            print(f"  - {test_name}")

sys.exit(0 if failed == 0 else 1)