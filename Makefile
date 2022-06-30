.PHONY: quality style test

quality:
	black --check --target-version py39 src/wandbfs tests
	isort --check-only src/wandbfs tests
	flake8 src/wandbfs tests

style:
	black --target-version py39 src/wandbfs tests
	isort src/wandbfs tests

test:
	python -m pytest tests/ --durations 0 -s