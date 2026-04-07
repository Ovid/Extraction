.PHONY: all test test-python test-js cover lint format loc fetch score serve help

all: lint format test ## Lint, format, and test

test: test-python test-js ## Run full test suite (Python + JS)

test-python: ## Run Python tests (unit + integration)
	source .venv/bin/activate && pytest tests/python/ --tb=short -q

test-js: ## Run JavaScript tests (Vitest)
	npx vitest run --reporter=default

cover: ## Generate Python unit test coverage report
	source .venv/bin/activate && pytest tests/python/unit/ --cov=score_countries --cov-report=term-missing --tb=short -q

lint: ## Lint (placeholder — no linter configured yet)
	@echo "No linter configured. Add ruff or eslint to enable."

format: ## Format (placeholder — no formatter configured yet)
	@echo "No formatter configured. Add ruff or prettier to enable."

loc: ## Count lines of our own code (excludes dependencies)
	cloc --exclude-dir=node_modules,.venv,raw_data --exclude-ext=json js/ css/ scripts/ tests/ index.html

fetch: ## Fetch raw data from all sources
	source .venv/bin/activate && cd scripts && python fetch_all.py

score: ## Run scoring pipeline (preview mode)
	source .venv/bin/activate && cd scripts && python score_countries.py --preview

score-write: ## Run scoring pipeline (writes scores.json)
	source .venv/bin/activate && cd scripts && python score_countries.py

serve: ## Start local dev server on port 8000
	python3 -m http.server 8000

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
