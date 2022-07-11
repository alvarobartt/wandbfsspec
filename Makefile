.PHONY: quality style tests

quality:
	black --check --target-version py39 src/wandbfsspec tests
	isort --check-only src/wandbfsspec tests
	flake8 src/wandbfsspec tests

style:
	black --target-version py39 src/wandbfsspec tests
	isort src/wandbfsspec tests

tests:
	pytest tests/ --durations 0 -s