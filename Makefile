# PiCalendar Makefile

.PHONY: help test test-quick test-unit test-integration coverage clean install run benchmark

# デフォルトターゲット
help:
	@echo "PiCalendar - 利用可能なコマンド:"
	@echo ""
	@echo "  make install       - 依存関係をインストール"
	@echo "  make test          - 全テストを実行"
	@echo "  make test-quick    - クイックテスト（遅いテストをスキップ）"
	@echo "  make test-unit     - 単体テストのみ実行"
	@echo "  make test-integration - 統合テストのみ実行"
	@echo "  make coverage      - カバレッジレポートを生成"
	@echo "  make benchmark     - パフォーマンスベンチマークを実行"
	@echo "  make run           - アプリケーションを実行"
	@echo "  make clean         - 一時ファイルを削除"
	@echo ""

# 依存関係インストール
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-timeout pytest-mock

# 全テスト実行
test:
	python tests/run_all_tests.py

# クイックテスト
test-quick:
	python tests/run_all_tests.py --quick

# 単体テスト
test-unit:
	python tests/run_all_tests.py -m unit

# 統合テスト
test-integration:
	python tests/run_all_tests.py -m integration

# カバレッジレポート生成
coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "カバレッジレポート: htmlcov/index.html"

# パフォーマンスベンチマーク
benchmark:
	python scripts/benchmark.py

# アプリケーション実行
run:
	python main.py

# クリーンアップ
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.json
	rm -f test_results.xml
	rm -rf .pytest_cache/
	rm -f benchmark_results_*.json

# テスト結果表示
show-coverage:
	@if [ -f htmlcov/index.html ]; then \
		echo "ブラウザでカバレッジレポートを開いています..."; \
		open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "手動で htmlcov/index.html を開いてください"; \
	else \
		echo "カバレッジレポートが見つかりません。'make coverage' を実行してください。"; \
	fi

# Raspberry Pi向けデプロイ準備
deploy-prepare:
	@echo "Raspberry Pi向けデプロイパッケージを準備中..."
	tar -czf picalender-deploy.tar.gz \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.git' \
		--exclude='htmlcov' \
		--exclude='.coverage' \
		--exclude='*.log' \
		src/ assets/ wallpapers/ scripts/ \
		main.py settings.yaml requirements.txt \
		Makefile README.md
	@echo "デプロイパッケージ作成完了: picalender-deploy.tar.gz"

# 開発サーバー（デバッグモード）
dev:
	SDL_VIDEODRIVER=x11 python main.py --debug

# コード品質チェック
lint:
	@echo "コード品質チェック中..."
	@which flake8 > /dev/null 2>&1 || (echo "flake8がインストールされていません。pip install flake8" && exit 1)
	flake8 src/ tests/ --max-line-length=120 --exclude=__pycache__

# タイプチェック
typecheck:
	@echo "タイプチェック中..."
	@which mypy > /dev/null 2>&1 || (echo "mypyがインストールされていません。pip install mypy" && exit 1)
	mypy src/ --ignore-missing-imports

# フォーマット
format:
	@echo "コードフォーマット中..."
	@which black > /dev/null 2>&1 || (echo "blackがインストールされていません。pip install black" && exit 1)
	black src/ tests/ --line-length=120

# 全品質チェック
quality: lint typecheck
	@echo "コード品質チェック完了"