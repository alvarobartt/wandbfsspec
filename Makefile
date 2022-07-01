.PHONY: quality style test

quality:
	black --check --target-version py39 src/wandbfsspec tests
	isort --check-only src/wandbfsspec tests
	flake8 src/wandbfsspec tests

style:
	black --target-version py39 src/wandbfsspec tests
	isort src/wandbfsspec tests

test:
	python -m pytest tests/ --durations 0 -s