#!/usr/bin/env python
"""一時的なテスト確認スクリプト"""

import sys
import os

# プロジェクトルートをPYTHONPATHに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# testsディレクトリを直接インポート
test_file = os.path.join(project_root, 'tests', 'test_display_manager.py')
import importlib.util
spec = importlib.util.spec_from_file_location("test_display_manager", test_file)
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

TestDisplayManager = test_module.TestDisplayManager
import unittest

# FPSテストを実行
test = TestDisplayManager()
test.setUp()

try:
    test.test_TC012_fps_control()
    print("TC012: PASSED")
except AssertionError as e:
    print(f"TC012 failed: {e}")
except Exception as e:
    print(f"TC012 error: {e}")

# TC016を実行
test2 = TestDisplayManager()
test2.setUp()
try:
    test2.test_TC016_pygame_init_failure()
    print("TC016: PASSED")
except AssertionError as e:
    print(f"TC016 failed: {e}")
except Exception as e:
    print(f"TC016 error: {e}")

# TC020を実行
test3 = TestDisplayManager()
test3.setUp()
try:
    test3.test_TC020_cleanup_on_exception()
    print("TC020: PASSED")
except AssertionError as e:
    print(f"TC020 failed: {e}")
except Exception as e:
    print(f"TC020 error: {e}")