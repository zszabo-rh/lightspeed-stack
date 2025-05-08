run: ## Run the service locally
	python src/lightspeed-stack.py

check-types: ## Checks type hints in sources
	MYPYPATH=src pdm run mypy --namespace-packages --explicit-package-bases --strict --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs .

security-check: ## Check the project for security issues
	bandit -c pyproject.toml -r src tests

format: ## Format the code into unified format
	pdm run black .
	pdm run ruff check . --fix

requirements.txt:	pyproject.toml pdm.lock ## Generate requirements.txt file containing hashes for all non-devel packages
	pdm export --prod --format requirements --output requirements.txt --no-extras --without evaluation


