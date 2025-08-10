#!/usr/bin/env python3
"""
全テストスイート実行スクリプト

すべての単体テストを実行し、カバレッジレポートを生成する。
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


class TestRunner:
    """テスト実行管理クラス"""
    
    def __init__(self, verbose: bool = False):
        """初期化
        
        Args:
            verbose: 詳細出力フラグ
        """
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.results = []
    
    def run_all_tests(self) -> int:
        """全テストを実行
        
        Returns:
            終了コード（0: 成功、1: 失敗）
        """
        print("=" * 60)
        print("PiCalendar 単体テストスイート実行")
        print("=" * 60)
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"テストディレクトリ: {self.test_dir}")
        print()
        
        # pytest実行
        cmd = ["python", "-m", "pytest"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
        
        # カバレッジオプション
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json"
        ])
        
        # JUnitXML出力（CI用）
        cmd.extend(["--junit-xml=test_results.xml"])
        
        # テストディレクトリ指定
        cmd.append(str(self.test_dir))
        
        # 実行
        result = subprocess.run(cmd, cwd=self.project_root)
        
        print()
        print("=" * 60)
        print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if result.returncode == 0:
            print("✅ すべてのテストが成功しました！")
            self._print_coverage_summary()
        else:
            print("❌ テストが失敗しました")
        
        print("=" * 60)
        
        return result.returncode
    
    def run_specific_tests(self, pattern: str) -> int:
        """特定のテストを実行
        
        Args:
            pattern: テストパターン（例: "test_config"）
            
        Returns:
            終了コード
        """
        print(f"パターン '{pattern}' に一致するテストを実行...")
        
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "-k", pattern,
            str(self.test_dir)
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode
    
    def run_by_marker(self, marker: str) -> int:
        """マーカーでテストを実行
        
        Args:
            marker: マーカー名（unit, integration, slow等）
            
        Returns:
            終了コード
        """
        print(f"マーカー '{marker}' のテストを実行...")
        
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "-m", marker,
            str(self.test_dir)
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode
    
    def _print_coverage_summary(self):
        """カバレッジサマリーを表示"""
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            import json
            with open(coverage_file) as f:
                data = json.load(f)
                total = data.get("totals", {})
                percent = total.get("percent_covered", 0)
                print(f"\n📊 カバレッジ: {percent:.1f}%")
                print(f"   HTMLレポート: htmlcov/index.html")
    
    def list_tests(self):
        """テスト一覧を表示"""
        print("利用可能なテストファイル:")
        print("-" * 40)
        
        test_files = sorted(self.test_dir.glob("test_*.py"))
        for test_file in test_files:
            # テストファイルから簡単な説明を抽出
            with open(test_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:10]:  # 最初の10行をチェック
                    if line.strip().startswith('"""'):
                        desc = line.strip().strip('"""')
                        if desc:
                            print(f"  {test_file.name:<40} - {desc}")
                            break
                else:
                    print(f"  {test_file.name}")
        
        print(f"\n合計: {len(test_files)} ファイル")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='PiCalendar テストスイート実行'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細出力'
    )
    parser.add_argument(
        '-k', '--pattern',
        help='特定のテストパターンを実行（例: test_config）'
    )
    parser.add_argument(
        '-m', '--marker',
        help='マーカーでテストを実行（unit, integration, slow）'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='テスト一覧を表示'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='クイックテスト（slowマーカーを除外）'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    if args.list:
        runner.list_tests()
        return 0
    
    if args.pattern:
        return runner.run_specific_tests(args.pattern)
    
    if args.marker:
        return runner.run_by_marker(args.marker)
    
    if args.quick:
        print("クイックテストモード（遅いテストをスキップ）")
        return runner.run_by_marker("not slow")
    
    # デフォルト: 全テスト実行
    return runner.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())